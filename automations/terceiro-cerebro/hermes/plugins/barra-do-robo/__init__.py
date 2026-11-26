"""barra-do-robo: o Hermes nunca responde a "/comando" no WhatsApp, e em grupo sabe quando não é com ele.

1. Texto que começa com "/" é do robô de vendas. O gateway do Hermes trataria esse texto antes do modelo
   (executaria os comandos dele ou responderia "comando desconhecido"), então o gancho `pre_gateway_dispatch`
   descarta a mensagem na entrada. Também descarta o que o dono do aparelho digitou (fromOwner); a ponte do
   WhatsApp já ignora o que o próprio número envia (modo bot), isto é só uma segunda trava.
2. No grupo dos sócios o Hermes lê toda mensagem (WHATSAPP_REQUIRE_MENTION=false) e decide pelo contexto se entra. O gateway
   só aceita um `[SILENT]` do modelo se `event.reply_expected is False` (gateway/response_filters.py:156); o adaptador do WhatsApp
   nunca preenche isso, então este gancho preenche: em grupo, mensagem que NÃO é @menção do bot, NÃO é resposta a mensagem do
   bot e NÃO começa com "hermes" fica com `reply_expected = False` (se o modelo calar, o silêncio vale; se responder, a resposta
   sai normal). Mensagem endereçada e todo DM ficam com o padrão (None): o gateway não deixa o modelo calar.
Qualquer outra mensagem segue o caminho normal.
"""
import re

# "hermes," / "@hermes" / "Hermes:" no começo da frase chama o Hermes (mesmo padrão de WHATSAPP_MENTION_PATTERNS).
_CHAMADA_PELO_NOME = re.compile(r"^[ ]*@?hermes(?![a-z])", re.IGNORECASE)


def _plataforma(event) -> str:
    plataforma = getattr(getattr(event, "source", None), "platform", None)
    return str(getattr(plataforma, "value", plataforma) or "").lower()


def _e_grupo(event) -> bool:
    if str(getattr(getattr(event, "source", None), "chat_type", "") or "").lower() == "group":
        return True
    bruto = getattr(event, "raw_message", None)
    return isinstance(bruto, dict) and bool(bruto.get("isGroup"))


def _bare(jid) -> str:
    """'5562...:12@s.whatsapp.net' -> '5562...' (tira domínio e sufixo de aparelho)."""
    return str(jid or "").split("@", 1)[0].split(":", 1)[0].strip().lower()


def _marcou_o_bot(event) -> bool:
    bruto = getattr(event, "raw_message", None)
    if not isinstance(bruto, dict):
        return False
    bots = {_bare(b) for b in (bruto.get("botIds") or []) if _bare(b)}
    if not bots:
        return False
    marcados = {_bare(m) for m in (bruto.get("mentionedIds") or []) if _bare(m)}
    if marcados & bots:
        return True
    corpo = str(bruto.get("body") or getattr(event, "text", "") or "").lower()
    return any(f"@{b}" in corpo for b in bots)


def enderecada_ao_hermes(event) -> bool:
    """A mensagem de grupo chama o Hermes de forma explícita (menção, resposta a ele, ou nome no começo)?"""
    if getattr(event, "reply_to_is_own_message", False):
        return True
    if _marcou_o_bot(event):
        return True
    return bool(_CHAMADA_PELO_NOME.search(str(getattr(event, "text", "") or "")))


def pode_calar(event) -> bool:
    """True quando o Hermes pode responder só `[SILENT]` a esta mensagem: WhatsApp, em grupo, sem chamar o Hermes."""
    return _plataforma(event) == "whatsapp" and _e_grupo(event) and not enderecada_ao_hermes(event)


def ignorar_barra(event, **kwargs):
    """Devolve {"action": "skip", ...} para comando com barra e mensagem do dono; senão None.

    Como efeito colateral (o gancho recebe o próprio evento, que segue adiante sem cópia), marca `reply_expected = False`
    nas mensagens de grupo que não chamam o Hermes, para o `[SILENT]` do modelo valer.
    """
    if _plataforma(event) != "whatsapp":
        return None
    texto = getattr(event, "text", None) or ""
    if texto.lstrip().startswith("/"):
        return {"action": "skip", "reason": "barra-do-robo: comando do robo de vendas"}
    metadata = getattr(event, "metadata", None) or {}
    if isinstance(metadata, dict) and metadata.get("whatsapp_from_owner"):
        return {"action": "skip", "reason": "barra-do-robo: mensagem do proprio aparelho"}
    if pode_calar(event):
        try:
            event.reply_expected = False
        except Exception:  # evento imutável ou de outro tipo: o padrão do gateway (sem silêncio) segue valendo
            pass
    return None


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", ignorar_barra)
