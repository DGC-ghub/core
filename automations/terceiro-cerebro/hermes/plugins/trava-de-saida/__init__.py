"""trava-de-saida: o Hermes só manda mensagem para os sócios e o grupo deles, e não mexe em segredo.

Gancho `pre_tool_call` (roda antes de toda ferramenta, inclusive nas rodadas do cron e nos subagentes). Devolve
{"action": "block", "message": ...} quando a chamada:

1. cria ou muda um job de cron (`cronjob_manage` create/update) com entrega (`deliver`, `failure_deliver`) para fora da
   lista de destinos, com frequência maior que uma vez por hora (intervalo < 60 min, cron com minuto que não é fixo),
   ou com `script`/`monitor`/`no_agent` (rodam fora deste gancho);
2. manda mensagem (ferramenta `send_message`, se um dia existir, ou `hermes send` no terminal) para fora da lista, ou
   fala direto com a ponte do WhatsApp (porta local 3000);
3. cita no terminal, no código ou num caminho de arquivo um lugar de segredo: `.env`, `cerebro.env`, `compose.env`,
   `/etc/dgc-cerebro`, `auth.json`, `.git-credentials`, chave `id_*` e `.ssh/`, `/proc/*/environ`;
4. tenta desligar as próprias travas: criar/mudar cron pelo terminal (`hermes cron create/edit`), mexer em plugin ou
   config do Hermes (`hermes plugins`, `hermes config`, `hermes auth`, `.hermes/plugins`, `config.yaml`), escrever
   em `~/.hermes`, ou parar/reiniciar serviço (`systemctl stop/restart/...`).

A lista de destinos vem de um arquivo do root (DESTINOS, fora do repositório e fora do alcance de escrita do Hermes):
uma linha por destino (`<id>@g.us`, `<id>@lid`, telefone ou `whatsapp:<id>`), `#` começa comentário. Sem o arquivo,
nenhum destino explícito vale (falha fechada); `origin` (a conversa de onde veio o pedido) e `local` continuam valendo.

É trava contra engano e texto malicioso lido em tarefa ou página, não contra um processo decidido a fugir: o Hermes
roda como o mesmo usuário que poderia, com esforço, contornar uma checagem de texto. Ver o documento interno da VM.
"""
import re
from pathlib import Path

DESTINOS = Path("/etc/dgc-cerebro/destinos.conf")
PORTA_DA_PONTE = 3000

FERRAMENTAS_DE_CRON = {"cronjob_manage", "cronjob"}
FERRAMENTAS_DE_ENVIO = {"send_message"}
FERRAMENTAS_DE_COMANDO = {"terminal", "process_manage", "execute_code"}  # todo texto dos argumentos é olhado
FERRAMENTAS_DE_ARQUIVO = {"read_file", "write_file", "patch", "search_files"}  # só os argumentos de caminho
FERRAMENTAS_QUE_ESCREVEM = {"write_file", "patch"}

_SEGREDO = re.compile(
    r"(?<![\w.-])\.env\b"
    r"|\b(?:cerebro|compose|robo)\.env\b"
    r"|/etc/dgc-cerebro"
    r"|\bauth\.json\b"
    r"|\.git-credentials"
    r"|(?<![\w-])id_(?:rsa|dsa|ecdsa|ed25519|github)\w*"
    r"|\.ssh/"
    r"|/proc/[^\s/]*/environ",
    re.IGNORECASE,
)
_PONTE = re.compile(r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[?::1\]?)\s*:\s*%d\b" % PORTA_DA_PONTE, re.IGNORECASE)
# "hermes" na posição de comando (começo, depois de espaço, ;, &, |, ( ou crase; com ou sem caminho), seguido de opções e do
# subcomando. "repos/produto-hermes/config" não casa.
_COMANDO_HERMES = r"(?:^|(?<=[\s;&|(`]))(?:[^\s;&|(`]*/)?hermes\s+(?:-{1,2}[\w-]+(?:=\S+)?\s+)*"
_HERMES_PROIBIDO = re.compile(
    _COMANDO_HERMES + r"(?:cron\s+(?:create|add|edit|update|new)|plugins?|config|auth|update|whatsapp|gateway|hooks?)\b",
    re.IGNORECASE | re.MULTILINE,
)
_HERMES_SEND = re.compile(_COMANDO_HERMES + r"send\b", re.IGNORECASE | re.MULTILINE)
_ALVO_DO_SEND = re.compile(r"(?:--to|-t)(?:=|\s+)(['\"]?)([^\s'\"]+)\1")
_AUTODEFESA = re.compile(
    r"\.hermes/(?:plugins|config\.yaml|\.env|SOUL\.md|hooks)"
    r"|\bplugins\.(?:enabled|disabled)\b"
    r"|\bsystemctl\b[^\n;&|]*\b(?:stop|restart|kill|disable|mask|edit|revert|set-environment|daemon-reload|reload)\b",
    re.IGNORECASE,
)
_CHAVE_DE_CAMINHO = re.compile(r"path|file|dir|target|cwd|glob", re.IGNORECASE)


# --- destinos ------------------------------------------------------------------------------------
def normalizar(alvo: str) -> str:
    """'whatsapp:+5562...@s.whatsapp.net' e '5562...' viram a mesma coisa; grupo e LID ficam com o domínio.

    Tira o sufixo de aparelho (':12') e o de tópico depois do chat ('...@g.us:7')."""
    alvo = str(alvo or "").strip().lower()
    if alvo.startswith("whatsapp:"):
        alvo = alvo[len("whatsapp:"):]
    usuario, arroba, dominio = alvo.partition("@")
    usuario = usuario.split(":", 1)[0].strip().lstrip("+").replace(" ", "").replace("-", "")
    dominio = dominio.split(":", 1)[0].strip()
    if not arroba or dominio in ("s.whatsapp.net", "c.us"):
        return usuario
    return f"{usuario}@{dominio}"


def ler_destinos(caminho: Path = DESTINOS) -> frozenset:
    """Destinos liberados, já normalizados. Arquivo ausente ou ilegível: nenhum (falha fechada)."""
    try:
        linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        return frozenset()
    return frozenset(normalizar(l.split("#", 1)[0]) for l in linhas if normalizar(l.split("#", 1)[0]))


def _destino_ok(parte: str, destinos: frozenset) -> bool:
    parte = parte.strip()
    if parte.lower() in ("", "origin", "local"):
        return True
    plataforma, _, resto = parte.partition(":")
    if plataforma.strip().lower() != "whatsapp" or not resto.strip():
        return False  # all, bot-chat, outra plataforma, whatsapp sem chat: nada disso
    return normalizar(resto) in destinos


def _entrega_ok(valor, destinos: frozenset) -> bool:
    if valor is None:
        return True
    return all(_destino_ok(p, destinos) for p in str(valor).split(","))


# --- frequência do cron --------------------------------------------------------------------------
_DURACAO = re.compile(r"^(\d*)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days)$")
_CAMPO_FIXO = re.compile(r"^\d+$")


def _minutos(texto: str):
    achado = _DURACAO.match(texto.strip().lower())
    if not achado:
        return None
    n = int(achado.group(1)) if achado.group(1) else 1
    return n * {"m": 1, "h": 60, "d": 1440}[achado.group(2)[0]]


def mais_que_de_hora_em_hora(agenda) -> bool:
    """True se o agendamento repete mais de uma vez por hora (o mesmo jeito de ler do cron/jobs.py do Hermes)."""
    s = str(agenda or "").strip()
    baixo = s.lower()
    if not s or baixo.startswith("in "):
        return False  # vazio (o Hermes recusa) ou uma vez só
    if baixo.startswith("every "):
        minutos = _minutos(baixo[6:])
        return minutos is not None and minutos < 60  # "every monday 9am" e afins: uma vez por dia ou menos
    partes = s.split()
    if len(partes) >= 5 and all(re.match(r"^[A-Za-z\d*\-,/?]+$", p) for p in partes[:5]):
        if not _CAMPO_FIXO.match(partes[0]):
            return True  # minuto com *, lista, faixa ou passo
        return len(partes) >= 6 and not _CAMPO_FIXO.match(partes[5])  # 6º campo = segundos
    minutos = _minutos(baixo)
    return minutos is not None and minutos < 60


# --- texto de comando e caminhos -----------------------------------------------------------------
def _textos(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _textos(v)
    elif isinstance(valor, (list, tuple)):
        for v in valor:
            yield from _textos(v)


def _caminhos(args: dict):
    for chave, valor in (args or {}).items():
        if _CHAVE_DE_CAMINHO.search(str(chave)):
            yield from _textos(valor)


def _checar_comando(texto: str, destinos: frozenset):
    if _SEGREDO.search(texto):
        return "lugar de segredo (.env, chave, token, credencial): o Hermes não lê nem mexe nisso"
    if _PONTE.search(texto):
        return "falar direto com a ponte do WhatsApp não vale: a resposta final da conversa já é a mensagem"
    if _HERMES_PROIBIDO.search(texto):
        return ("cron, plugin, config, login e serviço do Hermes não se mexem pelo terminal; rotina nova só pela "
                "ferramenta de cron, entregando no grupo ou para um sócio")
    for achado in _HERMES_SEND.finditer(texto):
        trecho = texto[achado.start():].split("\n", 1)[0]
        alvos = [m.group(2) for m in _ALVO_DO_SEND.finditer(trecho)]
        if not alvos or not all(_destino_ok(a, destinos) for a in alvos):
            return "mensagem só vai para o grupo dos sócios ou para um sócio"
    if _AUTODEFESA.search(texto):
        return "as travas e o serviço do Hermes não se mexem por aqui; peça ao Gabriel"
    return None


def decidir(tool_name: str, args, destinos: frozenset):
    """Motivo do bloqueio (texto curto) ou None quando a chamada pode seguir."""
    nome = str(tool_name or "")
    args = args if isinstance(args, dict) else {}

    if nome in FERRAMENTAS_DE_CRON:
        acao = str(args.get("action") or "").strip().lower()
        if acao in ("create", "update", "add", "edit"):
            for campo in ("deliver", "failure_deliver"):
                if not _entrega_ok(args.get(campo), destinos):
                    return "rotina só entrega no grupo dos sócios ou para um sócio (ou na própria conversa)"
            if mais_que_de_hora_em_hora(args.get("schedule")):
                return "rotina no máximo de hora em hora"
            # script e monitor rodam fora deste gancho (antes do agente, sem passar pelas ferramentas): não valem
            if args.get("script") or args.get("monitor") or args.get("no_agent"):
                return "rotina do Hermes é só prompt (sem script, monitor nem no_agent)"
        return None

    if nome in FERRAMENTAS_DE_ENVIO:
        acao = str(args.get("action") or "send").strip().lower()
        if acao in ("list",):
            return None
        alvo = args.get("target") or args.get("to") or args.get("chat_id")
        if not alvo or not _destino_ok(str(alvo), destinos):
            return "mensagem só vai para o grupo dos sócios ou para um sócio"
        return None

    if nome in FERRAMENTAS_DE_COMANDO:
        for texto in _textos(args):
            motivo = _checar_comando(texto, destinos)
            if motivo:
                return motivo
        return None

    if nome in FERRAMENTAS_DE_ARQUIVO:
        for caminho in _caminhos(args):
            if _SEGREDO.search(caminho):
                return "lugar de segredo (.env, chave, token, credencial): o Hermes não lê nem mexe nisso"
            if nome in FERRAMENTAS_QUE_ESCREVEM and re.search(r"(?:^|/)\.hermes(?:/|$)", caminho):
                return "a configuração do Hermes não se mexe por aqui; peça ao Gabriel"
        return None

    return None


def guardar(tool_name=None, args=None, **kwargs):
    motivo = decidir(tool_name, args, ler_destinos())
    if motivo:
        return {"action": "block", "message": f"trava-de-saida: {motivo}."}
    return None


def register(ctx):
    ctx.register_hook("pre_tool_call", guardar)
