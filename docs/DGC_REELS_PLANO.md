# DGC Reels — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o motor `dgc-reels` (pipeline de vídeo + loop com controle de falhas + aprovação pelo Telegram + revisão automática de PR) e colocar o Hermes para produzir o estoque de Reels da DGC.

**Architecture:** Três processos com responsabilidades separadas. (1) **Worker** Python sem LLM (`loop/worker.py`, serviço systemd) executa os passos mecânicos de cada card (voz, legenda, ilustração, render, QA), aplica a política de falhas e envia pacotes e alertas via `hermes send`. (2) **Hermes** (cron em monitor mode + gateway do Telegram) faz só o criativo: cardápio, roteiro/cenas, refações, e aplica as respostas do Gabriel via `loop/cli.py`. (3) **Watchdog/relatório** são scripts sem LLM no cron do Hermes. O Remotion renderiza uma composição única `ReelDGC` guiada por `props.json`.

**Tech Stack:** Python 3.13 (venv: pyyaml, requests, pytest), Remotion 4.0.534 + React 19 + TypeScript + Biome + Vitest, Gemini API (TTS, imagem, visão), faster-whisper (venv do produto-hermes), ffmpeg, GitHub CLI, Hermes Agent (cron, gateway, `hermes send`), DGC Dev Hub (`dev run`).

**Spec:** `~/dgc-hub/docs/DGC_REELS_DESIGN.md` — ler antes de qualquer tarefa.

## Global Constraints

- Repo: `~/projects/dgc-reels`, remoto `DGC-ghub/dgc-reels` (privado). Código e docs em commits separados. Mensagens de commit em português, terminando com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Vídeo: 9:16, 1080×1920, 30 fps, 45–60 s, 5 cenas = 5 atos (`gancho`, `problema`, `construcao`, `resultado`, `fecho`), legenda queimada palavra a palavra.
- Remotion fixado em `4.0.534` (mesma versão da campanha). Chromium: `/home/pi/.cache/ms-playwright/chromium_headless_shell-1217/chrome-linux/headless_shell`. Sempre renderizar com `flock /tmp/remotion-dgc.lock` (nunca dois Chromium do Remotion ao mesmo tempo no Pi).
- `GOOGLE_API_KEY` lida de `~/.hermes/.env` (nunca impressa, nunca commitada).
- Estados do card: `ideia → aprovada → roteirizada → narrada → legendada → ilustrada → renderizada → qa_ok → enviada → aprovada_final`; desvios `refazer`, `bloqueada`, `cortada`. Uma falha com retry pendente **não** muda o estado: fica registrada em `tentativas` + `retomar_em` (é a representação do "falha" da spec).
- Restrições duras da spec §3 valem para todo roteiro, cena e render. A lista proibida fica em `metodo/proibidos.txt`.
- Série B sempre com `selo_exemplo: true` (o render mostra "EXEMPLO ILUSTRATIVO").
- Nada é publicado no Instagram neste plano.
- Merge automático só neste repo, e só com veredito `VEREDITO: APROVADO` do `claude-20b` + CI verde. Dois `VEREDITO: MUDANCAS` no mesmo PR → parar e chamar o Gabriel.
- Fuso: `America/Sao_Paulo`. Cota gratuita do Gemini considerada renovada às 05:10 BRT.

## Estrutura de arquivos

```text
~/projects/dgc-reels/
  CLAUDE.md  README.md  .gitignore  pyproject.toml  requirements.txt
  metodo/METODO.md            # 5 atos, séries, restrições, schema de roteiro/cenas
  metodo/proibidos.txt        # nomes/termos que bloqueiam o card
  marca/tokens.json           # identidade (provisória até o Gabriel aprovar)
  marca/estilo-ilustracao.md  # prompt-base das ilustrações
  trilhas/LICENCAS.md
  backlog/lote-01.yaml        # cardápio (gerado pelo Hermes)
  backlog/estado.yaml         # estado do loop (pausa, circuit breaker, método aprovado)
  backlog/cards/<id>-<slug>/{card.yaml,roteiro.json,cenas.json}
  loop/__init__.py
  loop/card.py        # Card, estados, transições, IO
  loop/estado.py      # EstadoLoop: pausa, circuit breaker, método aprovado
  loop/falhas.py      # classificação de falhas e reação
  loop/sensivel.py    # varredura de dados sensíveis
  loop/trava.py       # lock de instância única com heartbeat
  loop/respostas.py   # parser das respostas do Telegram
  loop/aplicar.py     # aplica comandos aos cards
  loop/selecao.py     # escolhe próximo card mecânico, monta pacote, pendências do Hermes
  loop/telegram_fmt.py# textos das mensagens
  loop/worker.py      # processo principal sem LLM
  loop/cli.py         # CLI usada pelo Hermes e pelos scripts
  pipeline/tts.py  pipeline/tts_unico.py  pipeline/conferir_fala.py   # fork da campanha
  pipeline/legendas.py  pipeline/imagens.py  pipeline/tempos.py  pipeline/mix.py  pipeline/qa.py
  pipeline/render.mjs
  audio/sfx/*.wav  audio/trilhas/*.wav     # copiados da campanha (síntese própria)
  remotion/{package.json,tsconfig.json,biome.json,remotion.config.ts,vitest.config.ts}
  remotion/fixtures/props-smoke.json
  remotion/public/Inter.ttf
  remotion/src/{index.ts,Root.tsx,ReelDGC.tsx,tipos.ts,timeline.ts,timeline.test.ts,ui.tsx,Legenda.tsx}
  remotion/src/cenas/{Gancho,Problema,Construcao,Resultado,Fecho,SeloExemplo,Marca}.tsx
  scripts/watchdog.sh  scripts/relatorio.sh  scripts/revisar_pr.sh
  deploy/dgc-reels-worker.service
  deploy/hermes-skill/SKILL.md
  tests/test_*.py
  .github/workflows/ci.yml
  out/                       # gitignored
```

---

# FASE 0 — Motor (executado pelo Claude Code, sex 10/10)

### Task 1: Scaffold do repositório, método e CI

**Files:**
- Create: `~/projects/dgc-reels/{CLAUDE.md,README.md,.gitignore,pyproject.toml,requirements.txt}`
- Create: `metodo/METODO.md`, `metodo/proibidos.txt`, `marca/tokens.json`, `marca/estilo-ilustracao.md`, `trilhas/LICENCAS.md`, `backlog/estado.yaml`, `backlog/cards/.gitkeep`, `loop/__init__.py`, `tests/__init__.py`, `.github/workflows/ci.yml`
- Copy: `audio/sfx/*.wav` e `audio/trilhas/*.wav`
- Modify: `/home/pi/tools/dgc-dev-hub/projects.json` (nova entrada)

**Interfaces:**
- Produces: venv `.venv` com `pytest`, `pyyaml`, `requests`; `marca/tokens.json` com chaves `provisorio,nome,cores{fundo,primaria,destaque,texto,suave},fonte`; alias `dev` `reels`.

- [ ] **Step 1: Criar repo e venv**

```bash
mkdir -p ~/projects/dgc-reels && cd ~/projects/dgc-reels && git init -b main
python3 -m venv .venv
printf 'pyyaml==6.0.2\nrequests==2.32.3\npytest==8.3.4\n' > requirements.txt
.venv/bin/pip install -q -r requirements.txt
mkdir -p metodo marca trilhas backlog/cards loop tests pipeline audio/sfx audio/trilhas scripts deploy/hermes-skill .github/workflows out
touch backlog/cards/.gitkeep loop/__init__.py tests/__init__.py
cp ~/projects/campanha-hub-ipeconect/audio/sfx/*.wav audio/sfx/
cp ~/projects/campanha-hub-ipeconect/audio/trilhas-v3/*.wav audio/trilhas/
```

- [ ] **Step 2: Escrever `.gitignore` e `pyproject.toml`**

`.gitignore`:
```gitignore
.venv/
out/
node_modules/
remotion/public/cards/
remotion/out/
__pycache__/
*.pyc
.env
loop/.lock
```

`pyproject.toml`:
```toml
[project]
name = "dgc-reels"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: Escrever `CLAUDE.md` (enxuto)**

```markdown
# dgc-reels — CLAUDE.md

Motor de conteúdo da DGC: Reels 9:16 com narração, gerados em lote e aprovados pelo Gabriel no Telegram.
Spec: ~/dgc-hub/docs/DGC_REELS_DESIGN.md · Plano: ~/dgc-hub/docs/DGC_REELS_PLANO.md

- Português, termos técnicos em inglês. TDD. Código e docs em commits separados.
- Testes Python: `.venv/bin/pytest -q`. Remotion: `cd remotion && npm test && npx tsc --noEmit && npx @biomejs/biome ci .`
- Nunca commitar `out/`, áudio, vídeo, frames ou chaves. `GOOGLE_API_KEY` vem de `~/.hermes/.env`.
- Restrições duras: metodo/METODO.md §Restrições. Lista proibida: metodo/proibidos.txt.
- Render sempre com `flock /tmp/remotion-dgc.lock`.
- Nada é publicado no Instagram por este repo.
```

- [ ] **Step 4: Escrever `metodo/METODO.md`**

```markdown
# Método DGC de vídeo

## Os 5 atos (uma cena por ato, ids s1..s5)
| id | tipo | tempo | conteúdo |
|---|---|---|---|
| s1 | gancho | 0–3 s | a dor numa frase que o empresário goiano reconhece |
| s2 | problema | 3–15 s | ilustração do "como era" |
| s3 | construcao | 15–35 s | entendemos → desenhamos → construímos → entregamos + tela recriada |
| s4 | resultado | 35–45 s | antes × depois (número só em case real documentado) |
| s5 | fecho | 45–55 s | "Você imagina uma solução assim na sua empresa? ..." + CTA |

## Séries
A = case real Ipeconect · B = "E se fosse na sua empresa?" (Goiás, SEMPRE selo_exemplo) ·
C = pequenas automações · D = bastidores/quem é a DGC · E = Hermes (só o que funciona hoje).

## Restrições duras (violar invalida o vídeo)
1. Nenhum dado real de terceiro: cliente do BPO, telefone, CNPJ, CPF, e-mail, IP, login, valor em R$.
2. Nenhum caso fictício apresentado como real; série B com selo.
3. Nenhuma promessa de ganho garantido; nada de "IA substitui funcionário".
4. Nenhum preço ou prazo de entrega.
5. Nenhum claim exagerado sobre o Hermes.
6. Não citar concorrente/fornecedor pelo nome: "um sistema de RH pago", "um BI pago".

## Tom
Empresário de Goiás/Goiânia: direto, sem jargão, orgulhoso do que construiu. Referências locais
(agro, gado, Região da 44, Setor Marista, Ceasa) quando couber. Escrever "está" e "para" (não "tá"/"pra").

## roteiro.json
{"titulo": str, "voz": "Puck", "estilo": str, "segmentos": [{"id": "s1", "fala": str}, ... s5]}
Cada fala: 1 a 2 frases. Total falado: 40–50 s.

## cenas.json
{"serie": "A"|"B"|"C"|"D"|"E", "selo_exemplo": bool, "trilha": "a-tropical"|"b-future"|"c-funk-groove",
 "cenas": [
  {"id": "s1", "tipo": "gancho", "headline": ["linha 1", "linha 2"], "destaque": "palavra"},
  {"id": "s2", "tipo": "problema", "texto": str, "prompt_imagem": str},
  {"id": "s3", "tipo": "construcao", "etapas": ["Entendemos", "Desenhamos", "Construímos", "Entregamos"],
   "tela": {"titulo": str, "linhas": [str, ...]}},
  {"id": "s4", "tipo": "resultado", "antes": str, "depois": str, "legenda": str},
  {"id": "s5", "tipo": "fecho", "pergunta": str, "cta": "Chama a DGC no WhatsApp"}]}
`prompt_imagem` descreve só a cena; o estilo vem de marca/estilo-ilustracao.md.
```

- [ ] **Step 5: Escrever `metodo/proibidos.txt`, `marca/*`, `trilhas/LICENCAS.md`, `backlog/estado.yaml`**

`metodo/proibidos.txt` (um termo por linha; comparação sem acento, sem caixa, palavra inteira):
```text
Start
KPS
GMR
Anderson Bastos
Efactus
SPK8
JASC
SNF
Prestacon
Matheus
Pedro
Camila
Daiane
Anderson
Roosevelt
Stênio
Sólides
Data4Company
Autimize
EasyJur
Digisac
Omie
Pluggy
```

`marca/tokens.json`:
```json
{
  "provisorio": true,
  "nome": "DGC",
  "cores": { "fundo": "#0B1020", "primaria": "#3B82F6", "destaque": "#F59E0B", "texto": "#FFFFFF", "suave": "#94A3B8" },
  "fonte": "Inter"
}
```

`marca/estilo-ilustracao.md`:
```markdown
Ilustração vetorial flat moderna, vertical 9:16, cores da marca DGC (azul-escuro de fundo, azul e âmbar
como destaques), personagens brasileiros genéricos sem rosto detalhado, ambiente de escritório/negócio de
Goiás quando fizer sentido, sem texto escrito na imagem, sem logotipos, sem marcas reais.
```

`trilhas/LICENCAS.md`:
```markdown
# Licenças de trilha e efeitos
| arquivo | origem | licença |
|---|---|---|
| audio/trilhas/a-tropical.wav, b-future.wav, c-funk-groove.wav | síntese própria (`musica_variantes.py`, campanha HUB) | própria |
| audio/sfx/*.wav | síntese própria (`sfx.py`, campanha HUB) | própria |
```

`backlog/estado.yaml`:
```yaml
pausado: false
motivo: null
falhas_seguidas: 0
metodo_aprovado: false
alerta_pausa_enviado: false
ultima_mudanca: null
```

- [ ] **Step 6: CI**

`.github/workflows/ci.yml`:
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: pytest -q
  remotion:
    uses: DGC-ghub/core/.github/workflows/ci-node.yml@main
    with:
      working-directory: remotion
  smoke:
    runs-on: ubuntu-latest
    needs: remotion
    defaults: { run: { working-directory: remotion } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: npm ci
      - run: npm run smoke
```

- [ ] **Step 7: Registrar no Dev Hub**

Adicionar em `/home/pi/tools/dgc-dev-hub/projects.json` → `projects`:
```json
"dgc-reels": { "path": "/home/pi/projects/dgc-reels", "policy": "writable", "aliases": ["reels"], "copias": true }
```
Run: `dev status reels`
Expected: `Projeto: dgc-reels` com `Política: writable`.

- [ ] **Step 8: Commit e remoto**

```bash
cd ~/projects/dgc-reels
git add .gitignore pyproject.toml requirements.txt CLAUDE.md loop tests backlog marca trilhas audio .github
git commit -m "chore: scaffold do dgc-reels (venv, CI, marca provisória, áudio próprio)"
git add metodo README.md
git commit -m "docs: método DGC de vídeo e lista proibida"
gh repo create DGC-ghub/dgc-reels --private --source . --push
```
(README.md: 5 linhas — o que é, link da spec e do plano, como rodar testes.)

---

### Task 2: `loop/card.py` — card, estados e IO

**Files:**
- Create: `loop/card.py`
- Test: `tests/test_card.py`

**Interfaces:**
- Produces:
  - `ESTADOS: list[str]`, `DESVIOS: list[str]`, `MECANICOS: list[str]` (= `["roteirizada","narrada","legendada","ilustrada","renderizada"]`)
  - `@dataclass Card(id:str, slug:str, serie:str, titulo:str, gancho:str, resumo:str, estado:str="ideia", piloto:bool=False, tentativas:int=0, retomar_em:str|None=None, render_concurrency:int|None=None, notificado:bool=False, erros:list[dict], notas:list[str], dir:Path|None)`
  - `Card.avancar() -> None`, `Card.mover(estado:str) -> None`, `Card.registrar_erro(passo:str, tipo:str, msg:str, agora:datetime) -> None`
  - `carregar(dir:Path) -> Card`, `salvar(card:Card) -> None`, `listar(raiz:Path) -> list[Card]` (ordenado por id), `criar(raiz:Path, **campos) -> Card`
  - `normalizar_id(x:str|int) -> str` (`"4"` → `"04"`)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_card.py
import datetime as dt
import pytest
from loop.card import Card, ESTADOS, MECANICOS, carregar, salvar, listar, criar, normalizar_id

AGORA = dt.datetime(2026, 10, 11, 10, 0, tzinfo=dt.timezone.utc)

def test_normalizar_id():
    assert normalizar_id(4) == "04"
    assert normalizar_id("12") == "12"

def test_avancar_segue_a_ordem_e_zera_tentativas():
    c = Card(id="01", slug="x", serie="A", titulo="t", gancho="g", resumo="r", estado="narrada", tentativas=2, retomar_em="2026-10-11T12:00:00+00:00")
    c.avancar()
    assert c.estado == "legendada" and c.tentativas == 0 and c.retomar_em is None

def test_avancar_no_fim_falha():
    c = Card(id="01", slug="x", serie="A", titulo="t", gancho="g", resumo="r", estado="aprovada_final")
    with pytest.raises(ValueError):
        c.avancar()

def test_mover_rejeita_estado_invalido():
    c = Card(id="01", slug="x", serie="A", titulo="t", gancho="g", resumo="r")
    with pytest.raises(ValueError):
        c.mover("publicado")
    c.mover("bloqueada")
    assert c.estado == "bloqueada"

def test_registrar_erro_guarda_historico():
    c = Card(id="01", slug="x", serie="A", titulo="t", gancho="g", resumo="r")
    c.registrar_erro("render", "render", "exit 137", AGORA)
    assert c.erros == [{"passo": "render", "tipo": "render", "msg": "exit 137", "em": AGORA.isoformat()}]

def test_roundtrip_e_listagem(tmp_path):
    criar(tmp_path, id="2", slug="pecuaria", serie="B", titulo="Gado", gancho="g", resumo="r")
    criar(tmp_path, id="1", slug="32-telas", serie="A", titulo="32 telas", gancho="g", resumo="r", piloto=True)
    cards = listar(tmp_path)
    assert [c.id for c in cards] == ["01", "02"]
    assert cards[0].dir == tmp_path / "01-32-telas"
    cards[0].mover("aprovada"); salvar(cards[0])
    assert carregar(tmp_path / "01-32-telas").estado == "aprovada"
    assert carregar(tmp_path / "01-32-telas").piloto is True

def test_mecanicos_sao_subconjunto_ordenado():
    assert MECANICOS == [e for e in ESTADOS if e in MECANICOS]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_card.py -q`
Expected: FAIL com `ModuleNotFoundError: No module named 'loop.card'`

- [ ] **Step 3: Write minimal implementation**

```python
# loop/card.py
"""Card de vídeo: estado no ciclo de vida, tentativas, erros e notas. Persistido em card.yaml."""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

ESTADOS = ["ideia", "aprovada", "roteirizada", "narrada", "legendada", "ilustrada",
           "renderizada", "qa_ok", "enviada", "aprovada_final"]
DESVIOS = ["refazer", "bloqueada", "cortada"]
MECANICOS = ["roteirizada", "narrada", "legendada", "ilustrada", "renderizada"]


def normalizar_id(x: str | int) -> str:
    return str(int(x)).zfill(2)


@dataclass
class Card:
    id: str
    slug: str
    serie: str
    titulo: str
    gancho: str
    resumo: str
    estado: str = "ideia"
    piloto: bool = False
    tentativas: int = 0
    retomar_em: str | None = None
    render_concurrency: int | None = None
    notificado: bool = False
    erros: list[dict] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    dir: Path | None = field(default=None, repr=False, compare=False)

    def avancar(self) -> None:
        if self.estado not in ESTADOS or self.estado == ESTADOS[-1]:
            raise ValueError(f"card {self.id}: não há próximo estado depois de {self.estado}")
        self.estado = ESTADOS[ESTADOS.index(self.estado) + 1]
        self.tentativas = 0
        self.retomar_em = None
        self.render_concurrency = None
        self.notificado = False

    def mover(self, estado: str) -> None:
        if estado not in ESTADOS + DESVIOS:
            raise ValueError(f"estado inválido: {estado}")
        self.estado = estado
        self.tentativas = 0
        self.retomar_em = None
        self.notificado = False

    def registrar_erro(self, passo: str, tipo: str, msg: str, agora: dt.datetime) -> None:
        self.erros.append({"passo": passo, "tipo": tipo, "msg": msg[-500:], "em": agora.isoformat()})


def _dados(card: Card) -> dict:
    d = asdict(card)
    d.pop("dir")
    return d


def salvar(card: Card) -> None:
    assert card.dir is not None
    card.dir.mkdir(parents=True, exist_ok=True)
    (card.dir / "card.yaml").write_text(yaml.safe_dump(_dados(card), allow_unicode=True, sort_keys=False))


def carregar(dir: Path) -> Card:
    d = yaml.safe_load((dir / "card.yaml").read_text())
    return Card(**d, dir=dir)


def listar(raiz: Path) -> list[Card]:
    cards = [carregar(p.parent) for p in sorted(raiz.glob("*/card.yaml"))]
    return sorted(cards, key=lambda c: c.id)


def criar(raiz: Path, **campos) -> Card:
    campos["id"] = normalizar_id(campos["id"])
    card = Card(**campos)
    card.dir = raiz / f"{card.id}-{card.slug}"
    salvar(card)
    return card
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_card.py -q`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add loop/card.py tests/test_card.py
git commit -m "feat(loop): card com estados, transições e persistência yaml"
```

---

### Task 3: `loop/falhas.py` e `loop/estado.py` — política de falhas e circuit breaker

**Files:**
- Create: `loop/falhas.py`, `loop/estado.py`
- Test: `tests/test_falhas.py`, `tests/test_estado.py`

**Interfaces:**
- Produces:
  - `classificar(passo:str, rc:int, saida:str) -> str` ∈ `{"cota","transitoria","render","qa","sensivel"}`
  - `@dataclass(frozen=True) Reacao(tipo:str, acao:str, espera_s:int=0, concurrency:int|None=None, voltar_para:str|None=None)` — `acao` ∈ `{"esperar","retry","bloquear"}`
  - `reagir(tipo:str, passo:str, tentativas:int, agora:datetime) -> Reacao`
  - `proxima_renovacao(agora:datetime) -> datetime` (próximas 05:10 BRT)
  - `BACKOFF = [30, 120, 600]`; `VOLTA_QA = {"conferir_fala": "roteirizada", "qa": "legendada"}`
  - `@dataclass EstadoLoop(pausado:bool, motivo:str|None, falhas_seguidas:int, metodo_aprovado:bool, alerta_pausa_enviado:bool, ultima_mudanca:str|None, caminho:Path)`
  - `EstadoLoop.carregar(caminho:Path) -> EstadoLoop`, `.salvar()`, `.registrar_falha(motivo:str) -> bool` (True se acabou de pausar), `.registrar_sucesso(agora:datetime)`, `.pausar(motivo:str)`, `.retomar()`
  - `LIMITE_FALHAS = 3`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_falhas.py
import datetime as dt
from zoneinfo import ZoneInfo
from loop.falhas import classificar, reagir, proxima_renovacao, BACKOFF

BRT = ZoneInfo("America/Sao_Paulo")

def test_classifica_cota_por_texto():
    assert classificar("tts", 1, "cota DIÁRIA esgotada neste modelo") == "cota"
    assert classificar("imagens", 1, '{"error": {"status": "RESOURCE_EXHAUSTED"}}') == "cota"
    assert classificar("imagens", 1, "HTTP 429 Too Many Requests") == "cota"

def test_429_solto_no_log_nao_e_cota():
    assert classificar("render", 1, "300/1500 429 s") == "render"

def test_classifica_por_passo():
    assert classificar("sensivel", 2, "") == "sensivel"
    assert classificar("qa", 4, "") == "sensivel"
    assert classificar("qa", 3, "") == "qa"
    assert classificar("conferir_fala", 3, "VER s2") == "qa"
    assert classificar("render", 137, "Killed") == "render"
    assert classificar("tts", 1, "ReadTimeout") == "transitoria"

def test_sensivel_bloqueia_sem_retry():
    r = reagir("sensivel", "sensivel", 0, dt.datetime(2026, 10, 11, tzinfo=BRT))
    assert r.acao == "bloquear"

def test_cota_espera_ate_renovacao():
    agora = dt.datetime(2026, 10, 11, 22, 0, tzinfo=BRT)
    r = reagir("cota", "tts", 0, agora)
    assert r.acao == "esperar"
    assert r.espera_s == int((dt.datetime(2026, 10, 12, 5, 10, tzinfo=BRT) - agora).total_seconds())

def test_renovacao_no_mesmo_dia_de_madrugada():
    assert proxima_renovacao(dt.datetime(2026, 10, 12, 3, 0, tzinfo=BRT)) == dt.datetime(2026, 10, 12, 5, 10, tzinfo=BRT)

def test_transitoria_backoff_e_depois_bloqueia():
    agora = dt.datetime(2026, 10, 11, tzinfo=BRT)
    assert [reagir("transitoria", "tts", t, agora).espera_s for t in range(3)] == BACKOFF
    assert reagir("transitoria", "tts", 3, agora).acao == "bloquear"

def test_render_refaz_com_concurrency_1_uma_vez():
    agora = dt.datetime(2026, 10, 11, tzinfo=BRT)
    r = reagir("render", "render", 0, agora)
    assert (r.acao, r.concurrency) == ("retry", 1)
    assert reagir("render", "render", 1, agora).acao == "bloquear"

def test_qa_volta_ao_passo_culpado_ate_2x():
    agora = dt.datetime(2026, 10, 11, tzinfo=BRT)
    assert reagir("qa", "conferir_fala", 0, agora).voltar_para == "roteirizada"
    assert reagir("qa", "qa", 1, agora).voltar_para == "legendada"
    assert reagir("qa", "qa", 2, agora).acao == "bloquear"
```

```python
# tests/test_estado.py
import datetime as dt
from loop.estado import EstadoLoop, LIMITE_FALHAS

def test_circuit_breaker_pausa_na_terceira(tmp_path):
    e = EstadoLoop.carregar(tmp_path / "estado.yaml")
    assert e.pausado is False
    assert e.registrar_falha("render") is False
    assert e.registrar_falha("render") is False
    assert e.registrar_falha("render") is True
    assert e.pausado and e.falhas_seguidas == LIMITE_FALHAS and "3 falhas" in e.motivo

def test_sucesso_zera_e_persiste(tmp_path):
    e = EstadoLoop.carregar(tmp_path / "estado.yaml")
    e.registrar_falha("x")
    e.registrar_sucesso(dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc))
    e.salvar()
    e2 = EstadoLoop.carregar(tmp_path / "estado.yaml")
    assert e2.falhas_seguidas == 0 and e2.ultima_mudanca.startswith("2026-10-11")

def test_retomar_limpa_pausa(tmp_path):
    e = EstadoLoop.carregar(tmp_path / "estado.yaml")
    e.pausar("temperatura"); e.retomar()
    assert (e.pausado, e.motivo, e.falhas_seguidas, e.alerta_pausa_enviado) == (False, None, 0, False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_falhas.py tests/test_estado.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# loop/falhas.py
"""Classifica a falha de um passo e decide a reação (esperar, refazer ou bloquear)."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")
BACKOFF = [30, 120, 600]
VOLTA_QA = {"conferir_fala": "roteirizada", "qa": "legendada"}


@dataclass(frozen=True)
class Reacao:
    tipo: str
    acao: str
    espera_s: int = 0
    concurrency: int | None = None
    voltar_para: str | None = None


def classificar(passo: str, rc: int, saida: str) -> str:
    s = saida.lower()
    if passo == "sensivel" or (passo == "qa" and rc == 4):
        return "sensivel"
    if "cota di" in s or "resource_exhausted" in s or re.search(r"(http|status|code)\D{0,10}429|too many requests", s):
        return "cota"
    if passo in VOLTA_QA and rc == 3:
        return "qa"
    if passo == "render":
        return "render"
    return "transitoria"


def proxima_renovacao(agora: dt.datetime) -> dt.datetime:
    local = agora.astimezone(BRT)
    alvo = local.replace(hour=5, minute=10, second=0, microsecond=0)
    if alvo <= local:
        alvo += dt.timedelta(days=1)
    return alvo


def reagir(tipo: str, passo: str, tentativas: int, agora: dt.datetime) -> Reacao:
    if tipo == "sensivel":
        return Reacao(tipo, "bloquear")
    if tipo == "cota":
        return Reacao(tipo, "esperar", int((proxima_renovacao(agora) - agora).total_seconds()))
    if tipo == "render":
        return Reacao(tipo, "retry", concurrency=1) if tentativas == 0 else Reacao(tipo, "bloquear")
    if tipo == "qa":
        return Reacao(tipo, "retry", voltar_para=VOLTA_QA[passo]) if tentativas < 2 else Reacao(tipo, "bloquear")
    if tentativas < len(BACKOFF):
        return Reacao(tipo, "retry", BACKOFF[tentativas])
    return Reacao(tipo, "bloquear")
```

```python
# loop/estado.py
"""Estado global do loop: pausa, circuit breaker e portão do método (piloto)."""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

LIMITE_FALHAS = 3


@dataclass
class EstadoLoop:
    pausado: bool = False
    motivo: str | None = None
    falhas_seguidas: int = 0
    metodo_aprovado: bool = False
    alerta_pausa_enviado: bool = False
    ultima_mudanca: str | None = None
    caminho: Path | None = field(default=None, repr=False)

    @classmethod
    def carregar(cls, caminho: Path) -> "EstadoLoop":
        dados = yaml.safe_load(caminho.read_text()) if caminho.exists() else {}
        return cls(**(dados or {}), caminho=caminho)

    def salvar(self) -> None:
        d = asdict(self)
        d.pop("caminho")
        self.caminho.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))

    def registrar_falha(self, motivo: str) -> bool:
        self.falhas_seguidas += 1
        if self.falhas_seguidas >= LIMITE_FALHAS and not self.pausado:
            self.pausar(f"{self.falhas_seguidas} falhas seguidas (última: {motivo})")
            return True
        return False

    def registrar_sucesso(self, agora: dt.datetime) -> None:
        self.falhas_seguidas = 0
        self.ultima_mudanca = agora.isoformat()

    def pausar(self, motivo: str) -> None:
        self.pausado, self.motivo, self.alerta_pausa_enviado = True, motivo, False

    def retomar(self) -> None:
        self.pausado, self.motivo, self.falhas_seguidas, self.alerta_pausa_enviado = False, None, 0, False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_falhas.py tests/test_estado.py -q`
Expected: PASS (12 passed)

- [ ] **Step 5: Commit**

```bash
git add loop/falhas.py loop/estado.py tests/test_falhas.py tests/test_estado.py
git commit -m "feat(loop): política de falhas, espera de cota e circuit breaker"
```

---

### Task 4: `loop/sensivel.py` — varredura de dados sensíveis

**Files:**
- Create: `loop/sensivel.py`
- Test: `tests/test_sensivel.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) Achado(tipo:str, trecho:str)`
  - `carregar_proibidos(caminho:Path) -> list[str]`
  - `varrer(texto:str, proibidos:list[str]) -> list[Achado]` — tipos: `telefone, cnpj, cpf, email, ip, valor, proibido`
  - `varrer_card(dir:Path, proibidos:list[str]) -> list[Achado]` (lê `roteiro.json` + `cenas.json`)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sensivel.py
import json
from loop.sensivel import varrer, varrer_card, carregar_proibidos

P = ["Start", "JASC", "Sólides", "Anderson Bastos"]

def tipos(texto):
    return sorted({a.tipo for a in varrer(texto, P)})

def test_pega_telefone_cnpj_cpf_email_ip_valor():
    assert tipos("liga 62 99853-6579") == ["telefone"]
    assert tipos("+55 (62) 9853-6579") == ["telefone"]
    assert tipos("CNPJ 06.295.345/0001-04") == ["cnpj"]
    assert tipos("cpf 123.456.789-09") == ["cpf"]
    assert tipos("fale com gabriel@ipeconect.com.br") == ["email"]
    assert tipos("servidor 192.168.4.245") == ["ip"]
    assert tipos("faturou R$ 61.942 em janeiro") == ["valor"]

def test_pega_proibido_sem_acento_e_sem_caixa_palavra_inteira():
    assert tipos("saímos da solides") == ["proibido"]
    assert tipos("o cliente JASC tinha 3 mil contas") == ["proibido"]
    assert tipos("a ANDERSON BASTOS") == ["proibido"]
    assert tipos("startup de Goiânia") == []

def test_texto_limpo_passa():
    assert varrer("32 telas por dia viraram 1 tela só, para 8 empresas do grupo.", P) == []

def test_varrer_card_le_roteiro_e_cenas(tmp_path):
    (tmp_path / "roteiro.json").write_text(json.dumps({"segmentos": [{"id": "s1", "fala": "A Start pagava caro."}]}))
    (tmp_path / "cenas.json").write_text(json.dumps({"cenas": [{"id": "s3", "tela": {"linhas": ["62 99999-1234"]}}]}))
    assert sorted(a.tipo for a in varrer_card(tmp_path, P)) == ["proibido", "telefone"]

def test_carregar_proibidos_ignora_vazias(tmp_path):
    f = tmp_path / "p.txt"; f.write_text("Start\n\n  JASC  \n")
    assert carregar_proibidos(f) == ["Start", "JASC"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_sensivel.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# loop/sensivel.py
"""Varredura de dado sensível em roteiro/cenas/texto de tela. Qualquer achado bloqueia o card."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PADROES = {
    "cnpj": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-?\d{2}\b"),
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "telefone": re.compile(r"(?:\+?55\s?)?\(?\b\d{2}\)?\s?9?\d{4}[-\s]\d{4}\b"),
    "valor": re.compile(r"R\$\s?\d"),
}


@dataclass(frozen=True)
class Achado:
    tipo: str
    trecho: str


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower()


def carregar_proibidos(caminho: Path) -> list[str]:
    return [l.strip() for l in caminho.read_text().splitlines() if l.strip()]


def varrer(texto: str, proibidos: list[str]) -> list[Achado]:
    achados = []
    resto = texto
    for tipo in ("cnpj", "cpf", "email", "ip", "telefone", "valor"):
        for m in PADROES[tipo].finditer(resto):
            achados.append(Achado(tipo, m.group(0)))
        resto = PADROES[tipo].sub(" ", resto)  # um trecho conta uma vez só (CNPJ não vira telefone)
    base = _sem_acento(texto)
    for termo in proibidos:
        if re.search(rf"(?<!\w){re.escape(_sem_acento(termo))}(?!\w)", base):
            achados.append(Achado("proibido", termo))
    return achados


def _textos(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [t for v in obj.values() for t in _textos(v)]
    if isinstance(obj, list):
        return [t for v in obj for t in _textos(v)]
    return []


def varrer_card(dir: Path, proibidos: list[str]) -> list[Achado]:
    textos = []
    for nome in ("roteiro.json", "cenas.json"):
        p = dir / nome
        if p.exists():
            textos += _textos(json.loads(p.read_text()))
    return varrer("\n".join(textos), proibidos)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_sensivel.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add loop/sensivel.py tests/test_sensivel.py
git commit -m "feat(loop): varredura de dados sensíveis e lista proibida"
```

---

### Task 5: `loop/trava.py` — instância única com heartbeat

**Files:**
- Create: `loop/trava.py`
- Test: `tests/test_trava.py`

**Interfaces:**
- Produces: `class Trava(caminho:Path, ttl_s:int=1800, relogio=time.time, pid_vivo=_pid_vivo)` com `adquirir() -> bool`, `bater() -> None`, `liberar() -> None`, atributo `removeu_antiga: bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_trava.py
import json
from loop.trava import Trava

def test_adquire_e_bloqueia_segunda(tmp_path):
    t1 = Trava(tmp_path / ".lock", relogio=lambda: 1000, pid_vivo=lambda p: True)
    assert t1.adquirir() is True
    t2 = Trava(tmp_path / ".lock", relogio=lambda: 1001, pid_vivo=lambda p: True)
    assert t2.adquirir() is False

def test_remove_trava_de_pid_morto(tmp_path):
    (tmp_path / ".lock").write_text(json.dumps({"pid": 999999, "heartbeat": 1000}))
    t = Trava(tmp_path / ".lock", relogio=lambda: 1001, pid_vivo=lambda p: False)
    assert t.adquirir() is True and t.removeu_antiga is True

def test_remove_trava_sem_heartbeat_ha_mais_de_ttl(tmp_path):
    (tmp_path / ".lock").write_text(json.dumps({"pid": 1, "heartbeat": 0}))
    t = Trava(tmp_path / ".lock", ttl_s=1800, relogio=lambda: 1801, pid_vivo=lambda p: True)
    assert t.adquirir() is True

def test_bater_atualiza_e_liberar_remove(tmp_path):
    agora = [1000]
    t = Trava(tmp_path / ".lock", relogio=lambda: agora[0], pid_vivo=lambda p: True)
    t.adquirir(); agora[0] = 1500; t.bater()
    assert json.loads((tmp_path / ".lock").read_text())["heartbeat"] == 1500
    t.liberar()
    assert not (tmp_path / ".lock").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_trava.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# loop/trava.py
"""Trava de instância única: PID + heartbeat. Trava de processo morto ou sem heartbeat há > ttl é removida."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def _pid_vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class Trava:
    def __init__(self, caminho: Path, ttl_s: int = 1800, relogio=time.time, pid_vivo=_pid_vivo):
        self.caminho, self.ttl_s, self.relogio, self.pid_vivo = caminho, ttl_s, relogio, pid_vivo
        self.removeu_antiga = False

    def _gravar(self) -> None:
        self.caminho.write_text(json.dumps({"pid": os.getpid(), "heartbeat": self.relogio()}))

    def adquirir(self) -> bool:
        if self.caminho.exists():
            d = json.loads(self.caminho.read_text() or "{}")
            viva = self.pid_vivo(d.get("pid", 0)) and self.relogio() - d.get("heartbeat", 0) <= self.ttl_s
            if viva:
                return False
            self.caminho.unlink()
            self.removeu_antiga = True
        self._gravar()
        return True

    def bater(self) -> None:
        self._gravar()

    def liberar(self) -> None:
        self.caminho.unlink(missing_ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_trava.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add loop/trava.py tests/test_trava.py
git commit -m "feat(loop): trava de instância única com heartbeat"
```

---

### Task 6: `loop/respostas.py` e `loop/aplicar.py` — protocolo do Telegram

**Files:**
- Create: `loop/respostas.py`, `loop/aplicar.py`
- Test: `tests/test_respostas.py`, `tests/test_aplicar.py`

**Interfaces:**
- Consumes: `Card`, `normalizar_id` (Task 2); `EstadoLoop` (Task 3).
- Produces:
  - `@dataclass(frozen=True) Comando(acao:str, ids:tuple[str,...]=(), texto:str|None=None)`; `acao` ∈ `{"ok","corta","muda","refaz","pausa","retoma","status","ambiguo"}`; `ids == ("tudo",)` para "tudo".
  - `parse(texto:str) -> list[Comando]`
  - `@dataclass Resultado(mensagens:list[str], tarefas_hermes:list[dict])`
  - `aplicar(comandos:list[Comando], cards:list[Card], estado:EstadoLoop) -> Resultado` — modifica os objetos; quem chama salva.
  - Tarefas para o Hermes: `{"tipo": "reescrever_ideia", "id": "03", "instrucao": "..."}`, `{"tipo": "perguntar", "texto": "..."}`, `{"tipo": "status"}`.

Semântica:
- `ok N`: `ideia → aprovada`; `enviada → aprovada_final` (se o card for piloto, também `estado.metodo_aprovado = True`). Outros estados: mensagem "nada a aprovar".
- `ok tudo`: aplica `ok` a todos os cards em `ideia` ou `enviada`.
- `corta N`: qualquer estado diferente de `aprovada_final` → `cortada`.
- `muda N: txt`: card em `ideia` → nota + tarefa `reescrever_ideia`; em outro estado → igual a `refaz`.
- `refaz N: txt`: → `refazer`, nota guardada.
- `muda`/`refaz` sem texto → `ambiguo`.
- `pausa`/`retoma` → `estado.pausar("pedido do Gabriel")` / `estado.retomar()`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_respostas.py
from loop.respostas import parse, Comando

def test_ok_tudo():
    assert parse("ok tudo") == [Comando("ok", ("tudo",))]

def test_ok_intervalo_e_lista():
    assert parse("ok 1-3, 7") == [Comando("ok", ("01", "02", "03", "07"))]
    assert parse("ok 1-3 e 7") == [Comando("ok", ("01", "02", "03", "07"))]

def test_varios_comandos_numa_mensagem():
    cmds = parse("ok tudo, corta 7 e 12, muda 3: pra clínica, odontológica")
    assert cmds == [Comando("ok", ("tudo",)), Comando("corta", ("07", "12")),
                    Comando("muda", ("03",), "pra clínica, odontológica")]

def test_refaz_com_texto_e_sem_texto():
    assert parse("refaz 5: voz mais animada") == [Comando("refaz", ("05",), "voz mais animada")]
    assert parse("refaz 5") == [Comando("ambiguo", (), "refaz 5")]

def test_controle_e_lixo():
    assert parse("pausa") == [Comando("pausa")]
    assert parse("Retoma") == [Comando("retoma")]
    assert parse("status") == [Comando("status")]
    assert parse("show de bola") == [Comando("ambiguo", (), "show de bola")]
```

```python
# tests/test_aplicar.py
from loop.aplicar import aplicar
from loop.card import Card
from loop.estado import EstadoLoop
from loop.respostas import Comando

def card(id, estado, piloto=False):
    return Card(id=id, slug="x", serie="A", titulo="t", gancho="g", resumo="r", estado=estado, piloto=piloto)

def test_ok_tudo_aprova_ideias_e_enviadas(tmp_path):
    cs = [card("01", "ideia"), card("02", "enviada"), card("03", "narrada")]
    r = aplicar([Comando("ok", ("tudo",))], cs, EstadoLoop(caminho=tmp_path / "e.yaml"))
    assert [c.estado for c in cs] == ["aprovada", "aprovada_final", "narrada"]
    assert r.tarefas_hermes == []

def test_ok_no_piloto_aprova_metodo(tmp_path):
    e = EstadoLoop(caminho=tmp_path / "e.yaml")
    cs = [card("04", "enviada", piloto=True)]
    aplicar([Comando("ok", ("04",))], cs, e)
    assert e.metodo_aprovado is True and cs[0].estado == "aprovada_final"

def test_corta_e_refaz(tmp_path):
    cs = [card("07", "ideia"), card("05", "enviada")]
    aplicar([Comando("corta", ("07",)), Comando("refaz", ("05",), "voz mais animada")], cs, EstadoLoop(caminho=tmp_path / "e.yaml"))
    assert cs[0].estado == "cortada"
    assert cs[1].estado == "refazer" and cs[1].notas == ["voz mais animada"]

def test_muda_ideia_vira_tarefa_do_hermes(tmp_path):
    cs = [card("03", "ideia")]
    r = aplicar([Comando("muda", ("03",), "pra clínica")], cs, EstadoLoop(caminho=tmp_path / "e.yaml"))
    assert cs[0].estado == "ideia" and cs[0].notas == ["pra clínica"]
    assert r.tarefas_hermes == [{"tipo": "reescrever_ideia", "id": "03", "instrucao": "pra clínica"}]

def test_id_inexistente_e_ambiguo_viram_mensagem_e_pergunta(tmp_path):
    r = aplicar([Comando("ok", ("99",)), Comando("ambiguo", (), "show")], [], EstadoLoop(caminho=tmp_path / "e.yaml"))
    assert any("99" in m for m in r.mensagens)
    assert r.tarefas_hermes == [{"tipo": "perguntar", "texto": "show"}]

def test_pausa_e_retoma(tmp_path):
    e = EstadoLoop(caminho=tmp_path / "e.yaml")
    aplicar([Comando("pausa")], [], e); assert e.pausado
    aplicar([Comando("retoma")], [], e); assert not e.pausado
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_respostas.py tests/test_aplicar.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# loop/respostas.py
"""Parser estrito das respostas do Gabriel no Telegram. O que não entende vira 'ambiguo' (o Hermes pergunta)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from loop.card import normalizar_id

CHAVES = ("ok", "corta", "muda", "refaz", "pausa", "retoma", "status")
_INICIO = re.compile(rf"^\s*({'|'.join(CHAVES)})\b\s*(.*)$", re.IGNORECASE | re.DOTALL)
_ID = re.compile(r"(\d+)\s*-\s*(\d+)|(\d+)|(tudo)", re.IGNORECASE)


@dataclass(frozen=True)
class Comando:
    acao: str
    ids: tuple[str, ...] = ()
    texto: str | None = None


def _ids(trecho: str) -> tuple[str, ...] | None:
    ids: list[str] = []
    for m in _ID.finditer(trecho):
        if m.group(4):
            ids.append("tudo")
        elif m.group(1):
            ids += [normalizar_id(i) for i in range(int(m.group(1)), int(m.group(2)) + 1)]
        else:
            ids.append(normalizar_id(m.group(3)))
    sobra = re.sub(r"\b(e)\b", " ", _ID.sub(" ", trecho), flags=re.IGNORECASE).strip()
    return tuple(ids) if ids and not sobra else None


def _comando(chave: str, resto: str) -> Comando:
    chave = chave.lower()
    if chave in ("pausa", "retoma", "status"):
        return Comando(chave)
    if chave in ("muda", "refaz"):
        alvo, _, texto = resto.partition(":")
        ids = _ids(alvo)
        if not ids or not texto.strip():
            return Comando("ambiguo", (), f"{chave} {resto}".strip())
        return Comando(chave, ids, texto.strip())
    ids = _ids(resto)
    return Comando(chave, ids) if ids else Comando("ambiguo", (), f"{chave} {resto}".strip())


def parse(texto: str) -> list[Comando]:
    brutos: list[list[str]] = []  # [chave, resto]
    for pedaco in re.split(r"[\n;,]", texto):
        if not pedaco.strip():
            continue
        m = _INICIO.match(pedaco)
        if m:
            brutos.append([m.group(1), m.group(2).strip()])
        elif brutos and brutos[-1][0].lower() in ("muda", "refaz") and ":" in brutos[-1][1]:
            brutos[-1][1] += "," + pedaco  # vírgula dentro do texto livre do muda/refaz
        elif brutos and brutos[-1][0].lower() in ("ok", "corta") and _ids(pedaco):
            brutos[-1][1] += " " + pedaco.strip()  # "ok 1-3, 7"
        else:
            brutos.append(["", pedaco.strip()])
    return [_comando(c, r) if c else Comando("ambiguo", (), r) for c, r in brutos]
```

```python
# loop/aplicar.py
"""Aplica os comandos do Gabriel aos cards e ao estado do loop. Quem chama é responsável por salvar."""
from __future__ import annotations

from dataclasses import dataclass, field

from loop.card import Card
from loop.estado import EstadoLoop
from loop.respostas import Comando


@dataclass
class Resultado:
    mensagens: list[str] = field(default_factory=list)
    tarefas_hermes: list[dict] = field(default_factory=list)


def _alvos(ids: tuple[str, ...], cards: list[Card], estados: tuple[str, ...], r: Resultado) -> list[Card]:
    if ids == ("tudo",):
        return [c for c in cards if c.estado in estados]
    por_id = {c.id: c for c in cards}
    for i in ids:
        if i not in por_id:
            r.mensagens.append(f"#{i} não existe no lote")
    return [por_id[i] for i in ids if i in por_id]


def aplicar(comandos: list[Comando], cards: list[Card], estado: EstadoLoop) -> Resultado:
    r = Resultado()
    for cmd in comandos:
        if cmd.acao == "ambiguo":
            r.tarefas_hermes.append({"tipo": "perguntar", "texto": cmd.texto})
        elif cmd.acao == "status":
            r.tarefas_hermes.append({"tipo": "status"})
        elif cmd.acao == "pausa":
            estado.pausar("pedido do Gabriel"); r.mensagens.append("loop pausado")
        elif cmd.acao == "retoma":
            estado.retomar(); r.mensagens.append("loop retomado")
        elif cmd.acao == "ok":
            for c in _alvos(cmd.ids, cards, ("ideia", "enviada"), r):
                if c.estado == "ideia":
                    c.mover("aprovada"); r.mensagens.append(f"#{c.id} aprovada")
                elif c.estado == "enviada":
                    c.mover("aprovada_final"); r.mensagens.append(f"#{c.id} aprovada (final)")
                    if c.piloto:
                        estado.metodo_aprovado = True; r.mensagens.append("método aprovado: produção em série liberada")
                else:
                    r.mensagens.append(f"#{c.id} está em {c.estado}: nada a aprovar")
        elif cmd.acao == "corta":
            for c in _alvos(cmd.ids, cards, (), r):
                if c.estado != "aprovada_final":
                    c.mover("cortada"); r.mensagens.append(f"#{c.id} cortada")
        elif cmd.acao in ("muda", "refaz"):
            for c in _alvos(cmd.ids, cards, (), r):
                c.notas.append(cmd.texto)
                if cmd.acao == "muda" and c.estado == "ideia":
                    r.tarefas_hermes.append({"tipo": "reescrever_ideia", "id": c.id, "instrucao": cmd.texto})
                else:
                    c.mover("refazer"); r.mensagens.append(f"#{c.id} vai ser refeita")
    return r
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_respostas.py tests/test_aplicar.py -q`
Expected: PASS (11 passed)

- [ ] **Step 5: Commit**

```bash
git add loop/respostas.py loop/aplicar.py tests/test_respostas.py tests/test_aplicar.py
git commit -m "feat(loop): parser das respostas do Telegram e aplicação nos cards"
```

---

### Task 7: Pipeline de áudio e tempo — fork do TTS, legendas e `tempos.py`

**Files:**
- Copy+Modify: `pipeline/tts.py`, `pipeline/tts_unico.py`, `pipeline/conferir_fala.py` (de `~/projects/campanha-hub-ipeconect/pipeline/`)
- Create: `pipeline/legendas.py`, `pipeline/tempos.py`, `pipeline/__init__.py`
- Test: `tests/test_legendas.py`, `tests/test_tempos.py`

**Interfaces:**
- Consumes: contrato `manifest.json` do `tts_unico.py`: `{"voz","modelo","grafia","segmentos":[{"id","fala","arquivo","duracao","de","ate"}]}`.
- Produces:
  - `pipeline/tts_unico.py <roteiro.json> <pasta_audio> [voz] [grafia]` → `<pasta>/sN.trim.wav` + `manifest.json`. Exit ≠ 0 com "cota DIÁRIA" no stderr quando a cota acabar.
  - `pipeline/conferir_fala.py <pasta_audio>` → **exit 3** quando alguma fala não confere (antes era 1), exit 1 em erro.
  - `pipeline/legendas.py <pasta_audio> <saida_palavras.json>` (rodar com `WHISPER_PYTHON`) → `{"s1": [{"w","ini","fim"}], ...}` com tempos relativos ao início do segmento e palavras do roteiro.
  - `legendas.alinhar(fala:str, ouvidas:list[tuple[float,float]], duracao:float) -> list[dict]`
  - `pipeline/tempos.py <card_dir> <out_dir>` → `<out_dir>/props.json` e cópia das imagens para `remotion/public/cards/<id>/`.
  - `tempos.montar_props(manifest:dict, cenas:dict, palavras:dict, tokens:dict, pasta_audio:str, card_id:str, fps:int=30) -> dict` com chaves `fps,total,cortes,falas,palavras,cenas,serie,selo_exemplo,trilha,tokens`. Em `cenas`, `imagem` vira `cards/<id>/<sN>.png` quando existir `prompt_imagem`.
  - `MIN_POR_TIPO = {"gancho": 2.5, "problema": 4.0, "construcao": 5.0, "resultado": 3.5, "fecho": 4.0}`

- [ ] **Step 1: Copiar o fork e ajustar exit code e grafia**

```bash
cp ~/projects/campanha-hub-ipeconect/pipeline/{tts.py,tts_unico.py,conferir_fala.py} pipeline/
touch pipeline/__init__.py
sed -i 's/grafia = sys.argv\[4\] if len(sys.argv) > 4 else "Ipeconect"/grafia = sys.argv[4] if len(sys.argv) > 4 else "DGC"/' pipeline/tts_unico.py
sed -i 's/^sys.exit(1 if ruim else 0)$/sys.exit(3 if ruim else 0)/' pipeline/conferir_fala.py
grep -n 'else "DGC"' pipeline/tts_unico.py && grep -n 'sys.exit(3 if ruim' pipeline/conferir_fala.py
```
Expected: as duas linhas encontradas. No `conferir_fala.py`, trocar a função `junta` (regra da marca Ipeconect) por `lambda w: re.sub(r"\bd ?g ?c\b|\bde ge ce\b", "dgc", " ".join(w)).split()`.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_legendas.py
from pipeline.legendas import alinhar

def test_mesma_quantidade_usa_tempos_do_whisper():
    r = alinhar("Chama a DGC.", [(0.0, 0.4), (0.45, 0.6), (0.62, 1.1)], 1.2)
    assert r == [{"w": "Chama", "ini": 0.0, "fim": 0.4}, {"w": "a", "ini": 0.45, "fim": 0.6}, {"w": "DGC.", "ini": 0.62, "fim": 1.1}]

def test_quantidade_diferente_cai_na_estimativa_por_peso():
    r = alinhar("Você imagina isso?", [(0.0, 2.0)], 2.0)
    assert [p["w"] for p in r] == ["Você", "imagina", "isso?"]
    assert r[0]["ini"] == 0.0 and abs(r[-1]["fim"] - 2.0) < 1e-6
    assert all(a["fim"] <= b["ini"] + 1e-9 for a, b in zip(r, r[1:]))
```

```python
# tests/test_tempos.py
from pipeline.tempos import montar_props

MAN = {"segmentos": [{"id": f"s{i}", "fala": f"fala {i}", "arquivo": f"s{i}.trim.wav", "duracao": d}
                     for i, d in zip(range(1, 6), [3.0, 6.0, 12.0, 6.0, 7.0])]}
CENAS = {"serie": "B", "selo_exemplo": True, "trilha": "b-future", "cenas": [
    {"id": "s1", "tipo": "gancho", "headline": ["a"]},
    {"id": "s2", "tipo": "problema", "texto": "t", "prompt_imagem": "curral"},
    {"id": "s3", "tipo": "construcao", "etapas": ["E"]},
    {"id": "s4", "tipo": "resultado", "antes": "a", "depois": "b"},
    {"id": "s5", "tipo": "fecho", "pergunta": "p", "cta": "c"}]}
PAL = {f"s{i}": [{"w": "fala", "ini": 0.0, "fim": 0.5}, {"w": str(i), "ini": 0.5, "fim": 1.0}] for i in range(1, 6)}
TOK = {"nome": "DGC", "cores": {}, "fonte": "Inter"}

def test_cortes_respeitam_minimo_e_fala():
    p = montar_props(MAN, CENAS, PAL, TOK, "/a", "07")
    assert p["cortes"][0] == 0
    assert p["cortes"][1] == round((0.1 + 3.0 + 0.35) * 30)  # fala s1 acaba em 3.1 + respiro (> mínimo 2.5)
    assert len(p["cortes"]) == 5 and p["cortes"] == sorted(p["cortes"])
    assert p["total"] > p["cortes"][-1]

def test_palavras_ficam_absolutas_e_imagem_aponta_para_public():
    p = montar_props(MAN, CENAS, PAL, TOK, "/a", "07")
    s2 = p["falas"][1]
    assert p["palavras"][2]["ini"] == s2["ini"]  # 1ª palavra de s2
    assert p["cenas"][1]["imagem"] == "cards/07/s2.png"
    assert p["falas"][0]["arquivo"] == "/a/s1.trim.wav"
    assert (p["serie"], p["selo_exemplo"], p["trilha"]) == ("B", True, "b-future")

def test_numero_de_cenas_tem_que_bater_com_segmentos():
    import pytest
    with pytest.raises(ValueError):
        montar_props({"segmentos": MAN["segmentos"][:4]}, CENAS, PAL, TOK, "/a", "07")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_legendas.py tests/test_tempos.py -q`
Expected: FAIL com `ModuleNotFoundError: No module named 'pipeline.legendas'`

- [ ] **Step 4: Write implementation**

```python
# pipeline/legendas.py
"""Tempo de cada palavra da legenda. Texto vem do ROTEIRO (grafia certa: "DGC"); o tempo vem do faster-whisper.
Se o whisper ouvir outra quantidade de palavras, cai na estimativa por peso (tamanho da palavra + pontuação).

Uso: $WHISPER_PYTHON pipeline/legendas.py <pasta_audio> <saida_palavras.json>
WHISPER_PYTHON padrão: ~/projects/produto-hermes/.venv-transcribe/bin/python
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _estimar(ws: list[str], duracao: float) -> list[dict]:
    peso = [len(re.sub(r"[^\w]", "", w)) + 2 + (3 if re.search(r"[,.?!]$", w) else 0) for w in ws]
    total, t, out = sum(peso), 0.0, []
    for w, p in zip(ws, peso):
        d = duracao * p / total
        out.append({"w": w, "ini": round(t, 3), "fim": round(t + d, 3)})
        t += d
    out[-1]["fim"] = round(duracao, 3)
    return out


def alinhar(fala: str, ouvidas: list[tuple[float, float]], duracao: float) -> list[dict]:
    ws = fala.split()
    if len(ws) == len(ouvidas):
        return [{"w": w, "ini": round(a, 3), "fim": round(b, 3)} for w, (a, b) in zip(ws, ouvidas)]
    return _estimar(ws, duracao)


def main(pasta: Path, saida: Path) -> None:
    from faster_whisper import WhisperModel  # só existe no venv do whisper

    modelo = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    man = json.loads((pasta / "manifest.json").read_text())
    out = {}
    for s in man["segmentos"]:
        segs, _ = modelo.transcribe(str(pasta / s["arquivo"]), language="pt", word_timestamps=True)
        ouvidas = [(w.start, w.end) for seg in segs for w in (seg.words or [])]
        out[s["id"]] = alinhar(s["fala"], ouvidas, s["duracao"])
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("ok", saida)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
```

```python
# pipeline/tempos.py
"""Monta props.json (entrada da composição ReelDGC) a partir da narração medida, das cenas e das legendas.

Uso: python3 pipeline/tempos.py <card_dir> <out_dir>
Lê <out_dir>/audio/manifest.json, <out_dir>/palavras.json, <card_dir>/cenas.json, marca/tokens.json.
Copia <out_dir>/img/*.png para remotion/public/cards/<id>/ e grava <out_dir>/props.json.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MIN_POR_TIPO = {"gancho": 2.5, "problema": 4.0, "construcao": 5.0, "resultado": 3.5, "fecho": 4.0}
ENTRADA, RESPIRO, FIM = 0.2, 0.35, 2.0


def montar_props(manifest: dict, cenas: dict, palavras: dict, tokens: dict, pasta_audio: str,
                 card_id: str, fps: int = 30) -> dict:
    segs, lista = manifest["segmentos"], cenas["cenas"]
    if len(segs) != len(lista):
        raise ValueError(f"{len(segs)} falas para {len(lista)} cenas")
    t, cortes, falas, pals = 0.0, [], [], []
    for i, (s, cena) in enumerate(zip(segs, lista)):
        cortes.append(round(t * fps))
        ini = t + (0.1 if i == 0 else ENTRADA)
        fim = ini + s["duracao"]
        falas.append({"id": s["id"], "fala": s["fala"], "arquivo": f"{pasta_audio}/{s['arquivo']}",
                      "ini": round(ini, 3), "fim": round(fim, 3)})
        pals += [{"w": p["w"], "ini": round(ini + p["ini"], 3), "fim": round(ini + p["fim"], 3)}
                 for p in palavras.get(s["id"], [])]
        ultimo = i == len(segs) - 1
        t = max(t + MIN_POR_TIPO.get(cena["tipo"], 3.0), fim + (FIM if ultimo else RESPIRO))
    cenas_out = []
    for cena in lista:
        c = {k: v for k, v in cena.items() if k != "prompt_imagem"}
        if cena.get("prompt_imagem"):
            c["imagem"] = f"cards/{card_id}/{cena['id']}.png"
        cenas_out.append(c)
    return {"fps": fps, "total": round(t * fps), "cortes": cortes, "falas": falas, "palavras": pals,
            "cenas": cenas_out, "serie": cenas["serie"], "selo_exemplo": bool(cenas.get("selo_exemplo")),
            "trilha": cenas.get("trilha", "a-tropical"), "tokens": tokens}


def main(card_dir: Path, out_dir: Path) -> None:
    card_id = card_dir.name.split("-")[0]
    props = montar_props(
        json.loads((out_dir / "audio" / "manifest.json").read_text()),
        json.loads((card_dir / "cenas.json").read_text()),
        json.loads((out_dir / "palavras.json").read_text()),
        json.loads((RAIZ / "marca" / "tokens.json").read_text()),
        str(out_dir / "audio"), card_id)
    destino = RAIZ / "remotion" / "public" / "cards" / card_id
    destino.mkdir(parents=True, exist_ok=True)
    for png in (out_dir / "img").glob("*.png"):
        shutil.copy2(png, destino / png.name)
    (out_dir / "props.json").write_text(json.dumps(props, ensure_ascii=False, indent=1))
    print("total:", round(props["total"] / props["fps"], 2), "s →", out_dir / "props.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_legendas.py tests/test_tempos.py -q`
Expected: PASS (5 passed)

- [ ] **Step 6: Prova real de TTS + legenda (gasta 1 chamada de cota)**

```bash
mkdir -p out/prova && cat > out/prova/roteiro.json <<'EOF'
{"titulo": "prova", "voz": "Puck", "estilo": "Locução animada e natural em português do Brasil. Diga \"está\" e \"para\". Leia apenas o texto.",
 "segmentos": [{"id": "s1", "fala": "Seu financeiro ainda vive numa planilha?"}, {"id": "s2", "fala": "Chama a DGC."}]}
EOF
.venv/bin/python pipeline/tts_unico.py out/prova/roteiro.json out/prova/audio Puck DGC
.venv/bin/python pipeline/conferir_fala.py out/prova/audio; echo "exit=$?"
~/projects/produto-hermes/.venv-transcribe/bin/python pipeline/legendas.py out/prova/audio out/prova/palavras.json
```
Expected: `manifest.json` com 2 segmentos; `exit=0`; `palavras.json` com `s1` (7 palavras) e `s2` (3 palavras).

- [ ] **Step 7: Commit**

```bash
git add pipeline/__init__.py pipeline/tts.py pipeline/tts_unico.py pipeline/conferir_fala.py pipeline/legendas.py pipeline/tempos.py tests/test_legendas.py tests/test_tempos.py
git commit -m "feat(pipeline): fork do TTS da campanha, legendas com whisper e montagem de props"
```

---

### Task 8: Remotion — composição `ReelDGC` guiada por props

**Files:**
- Create: `remotion/{package.json,tsconfig.json,biome.json,remotion.config.ts,vitest.config.ts}`, `remotion/fixtures/props-smoke.json`, `remotion/public/Inter.ttf`
- Create: `remotion/src/{index.ts,Root.tsx,ReelDGC.tsx,tipos.ts,timeline.ts,timeline.test.ts,ui.tsx,Legenda.tsx}`
- Create: `remotion/src/cenas/{Gancho,Problema,Construcao,Resultado,Fecho,SeloExemplo,Marca}.tsx`
- Create: `pipeline/render.mjs`

**Interfaces:**
- Consumes: formato de `props.json` (Task 7).
- Produces: composição `ReelDGC`; `node pipeline/render.mjs remotion/src/index.ts ReelDGC --video <saida.mp4> --props <props.json>` e `... ReelDGC <pasta_stills> f1,f2 --props <props.json>`; variável `RENDER_CONCURRENCY` (padrão 2); `npm run smoke`.

- [ ] **Step 1: Pacote e config**

`remotion/package.json`:
```json
{
  "name": "dgc-reels-remotion",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "remotion studio src/index.ts",
    "test": "vitest run",
    "lint": "biome ci . && tsc --noEmit",
    "smoke": "remotion still src/index.ts ReelDGC out/smoke.png --frame=45 --props=fixtures/props-smoke.json"
  },
  "dependencies": {
    "@remotion/bundler": "4.0.534",
    "@remotion/cli": "4.0.534",
    "@remotion/renderer": "4.0.534",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "remotion": "4.0.534"
  },
  "devDependencies": {
    "@biomejs/biome": "2.2.4",
    "@types/react": "19.2.7",
    "typescript": "5.9.3",
    "vitest": "3.2.4"
  }
}
```

```bash
cd ~/projects/dgc-reels/remotion && npm install --loglevel=error
cp ~/projects/campanha-hub-ipeconect/remotion-reel/public/Inter.ttf public/
cp ~/dgc-hub/configs/biome.json biome.json 2>/dev/null || npx @biomejs/biome init
```

`remotion/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "Bundler", "jsx": "react-jsx",
    "strict": true, "resolveJsonModule": true, "skipLibCheck": true, "noEmit": true, "lib": ["DOM", "ES2022"]
  },
  "include": ["src", "fixtures"]
}
```

`remotion/remotion.config.ts`:
```ts
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

`remotion/vitest.config.ts`:
```ts
import { defineConfig } from "vitest/config";

export default defineConfig({ test: { include: ["src/**/*.test.ts"] } });
```

- [ ] **Step 2: Write the failing test (timeline puro)**

```ts
// remotion/src/timeline.test.ts
import { describe, expect, it } from "vitest";
import { blocoAtivo, sequencias } from "./timeline";

describe("sequencias", () => {
  it("sobrepõe 14 quadros na troca e termina no total", () => {
    expect(sequencias([0, 100, 250], 400)).toEqual([
      { from: 0, duration: 114 },
      { from: 100, duration: 164 },
      { from: 250, duration: 150 },
    ]);
  });
});

describe("blocoAtivo", () => {
  const p = [
    { w: "Seu", ini: 0, fim: 0.3 },
    { w: "financeiro", ini: 0.3, fim: 0.9 },
    { w: "ainda", ini: 0.9, fim: 1.2 },
    { w: "vive", ini: 1.2, fim: 1.5 },
    { w: "assim?", ini: 1.5, fim: 2.0 },
  ];
  it("agrupa de 3 em 3", () => {
    expect(blocoAtivo(p, 0.5)?.map((x) => x.w)).toEqual(["Seu", "financeiro", "ainda"]);
    expect(blocoAtivo(p, 1.6)?.map((x) => x.w)).toEqual(["vive", "assim?"]);
  });
  it("some depois do fim + 0,2 s", () => {
    expect(blocoAtivo(p, 2.5)).toBeNull();
  });
});
```

Run: `cd remotion && npm test`
Expected: FAIL com `Failed to resolve import "./timeline"`

- [ ] **Step 3: Implementar tipos e timeline**

```ts
// remotion/src/tipos.ts
export type Palavra = { w: string; ini: number; fim: number };
export type Fala = { id: string; fala: string; arquivo: string; ini: number; fim: number };
export type Tokens = {
  nome: string;
  cores: { fundo: string; primaria: string; destaque: string; texto: string; suave: string };
  fonte: string;
};
export type Cena =
  | { id: string; tipo: "gancho"; headline: string[]; destaque?: string }
  | { id: string; tipo: "problema"; texto: string; imagem?: string }
  | { id: string; tipo: "construcao"; etapas: string[]; tela?: { titulo: string; linhas: string[] } }
  | { id: string; tipo: "resultado"; antes: string; depois: string; legenda?: string }
  | { id: string; tipo: "fecho"; pergunta: string; cta: string };
export type PropsReel = {
  fps: number;
  total: number;
  cortes: number[];
  falas: Fala[];
  palavras: Palavra[];
  cenas: Cena[];
  serie: string;
  selo_exemplo: boolean;
  trilha: string;
  tokens: Tokens;
};
```

```ts
// remotion/src/timeline.ts
import type { Palavra } from "./tipos";

export const SOBREPOSICAO = 14;

export function sequencias(cortes: number[], total: number, sobre = SOBREPOSICAO) {
  return cortes.map((from, i) => {
    const fim = i + 1 < cortes.length ? Math.min(cortes[i + 1] + sobre, total) : total;
    return { from, duration: Math.max(1, fim - from) };
  });
}

function blocos(palavras: Palavra[], tamanho: number): Palavra[][] {
  const out: Palavra[][] = [];
  let atual: Palavra[] = [];
  for (const p of palavras) {
    atual.push(p);
    if (atual.length === tamanho || /[.?!]$/.test(p.w)) {
      out.push(atual);
      atual = [];
    }
  }
  if (atual.length) out.push(atual);
  return out;
}

export function blocoAtivo(palavras: Palavra[], t: number, tamanho = 3): Palavra[] | null {
  const bs = blocos(palavras, tamanho);
  for (let i = 0; i < bs.length; i++) {
    const fim = i + 1 < bs.length ? Math.min(bs[i + 1][0].ini, bs[i][bs[i].length - 1].fim + 0.2) : bs[i][bs[i].length - 1].fim + 0.2;
    if (t >= bs[i][0].ini && t < fim) return bs[i];
  }
  return null;
}
```

Run: `cd remotion && npm test`
Expected: PASS (3 passed)

- [ ] **Step 4: Componentes visuais**

```tsx
// remotion/src/ui.tsx
import { continueRender, delayRender, staticFile } from "remotion";

const fonte = delayRender("Inter");
const face = new FontFace("Inter", `url(${staticFile("Inter.ttf")}) format('truetype')`, { weight: "100 900" });
face
  .load()
  .then(() => {
    document.fonts.add(face);
    continueRender(fonte);
  })
  .catch(() => continueRender(fonte));

export const FONT = "Inter, sans-serif";
export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
```

```tsx
// remotion/src/cenas/Gancho.tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Tokens } from "../tipos";
import { FONT } from "../ui";

export const Gancho: React.FC<{ cena: Extract<Cena, { tipo: "gancho" }>; tokens: Tokens }> = ({ cena, tokens }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: tokens.cores.fundo, justifyContent: "center", padding: 90 }}>
      {cena.headline.map((linha, i) => {
        const s = spring({ frame: f - i * 6, fps, config: { damping: 13, stiffness: 160 } });
        return (
          <div key={linha} style={{ fontFamily: FONT, fontWeight: 900, fontSize: 132, lineHeight: 1.02, letterSpacing: "-0.03em", color: tokens.cores.texto, opacity: s, translate: `0 ${interpolate(s, [0, 1], [80, 0])}px` }}>
            {linha.split(" ").map((w) => (
              <span key={w} style={{ color: cena.destaque && w.includes(cena.destaque) ? tokens.cores.destaque : undefined }}>{w} </span>
            ))}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/cenas/Problema.tsx
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Tokens } from "../tipos";
import { clamp, FONT } from "../ui";

export const Problema: React.FC<{ cena: Extract<Cena, { tipo: "problema" }>; tokens: Tokens }> = ({ cena, tokens }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const zoom = interpolate(f, [0, durationInFrames], [1.0, 1.12]);
  return (
    <AbsoluteFill style={{ background: tokens.cores.fundo }}>
      {cena.imagem ? (
        <Img src={staticFile(cena.imagem)} style={{ width: "100%", height: "100%", objectFit: "cover", scale: String(zoom) }} />
      ) : (
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 35%, ${tokens.cores.primaria}55, ${tokens.cores.fundo})` }} />
      )}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,.75) 80%)" }} />
      <div style={{ position: "absolute", left: 80, right: 80, top: 1130, fontFamily: FONT, fontWeight: 800, fontSize: 64, lineHeight: 1.15, color: tokens.cores.texto, opacity: interpolate(f, [6, 18], [0, 1], clamp) }}>
        {cena.texto}
      </div>
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/cenas/Construcao.tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Tokens } from "../tipos";
import { clamp, FONT } from "../ui";

export const Construcao: React.FC<{ cena: Extract<Cena, { tipo: "construcao" }>; tokens: Tokens }> = ({ cena, tokens }) => {
  const f = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const passo = Math.max(8, Math.floor((durationInFrames * 0.45) / Math.max(1, cena.etapas.length)));
  const c = tokens.cores;
  return (
    <AbsoluteFill style={{ background: c.fundo, padding: 80, paddingTop: 300, gap: 26 }}>
      <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 800, letterSpacing: "0.2em", color: c.destaque }}>MÉTODO DGC</div>
      {cena.etapas.map((e, i) => {
        const s = spring({ frame: f - i * passo, fps, config: { damping: 14 } });
        return (
          <div key={e} style={{ display: "flex", alignItems: "center", gap: 22, opacity: s, translate: `${interpolate(s, [0, 1], [-60, 0])}px 0` }}>
            <div style={{ width: 54, height: 54, borderRadius: 27, background: c.primaria, color: c.texto, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, fontSize: 30 }}>✓</div>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 60, color: c.texto }}>{e}</div>
          </div>
        );
      })}
      {cena.tela ? (
        <div style={{ marginTop: 40, borderRadius: 28, background: "#FFFFFF", padding: 36, boxShadow: "0 30px 80px rgba(0,0,0,.45)", opacity: interpolate(f, [passo * cena.etapas.length, passo * cena.etapas.length + 12], [0, 1], clamp) }}>
          <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 40, color: c.fundo, marginBottom: 18 }}>{cena.tela.titulo}</div>
          {cena.tela.linhas.map((l, i) => (
            <div key={l} style={{ fontFamily: FONT, fontSize: 32, color: "#334155", padding: "12px 0", borderTop: i ? "1px solid #E2E8F0" : undefined }}>{l}</div>
          ))}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/cenas/Resultado.tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Tokens } from "../tipos";
import { clamp, FONT } from "../ui";

export const Resultado: React.FC<{ cena: Extract<Cena, { tipo: "resultado" }>; tokens: Tokens }> = ({ cena, tokens }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const risco = interpolate(f, [14, 26], [0, 100], clamp);
  const depois = spring({ frame: f - 28, fps, config: { damping: 11 } });
  const c = tokens.cores;
  return (
    <AbsoluteFill style={{ background: c.fundo, justifyContent: "center", alignItems: "center", gap: 50, fontFamily: FONT }}>
      <div style={{ position: "relative", fontSize: 84, fontWeight: 800, color: c.suave }}>
        {cena.antes}
        <div style={{ position: "absolute", left: 0, top: "52%", height: 10, width: `${risco}%`, background: "#EF4444", borderRadius: 5 }} />
      </div>
      <div style={{ fontSize: 132, fontWeight: 900, color: c.destaque, scale: String(depois) }}>{cena.depois}</div>
      {cena.legenda ? <div style={{ fontSize: 44, fontWeight: 700, color: c.texto, opacity: depois, padding: "0 80px", textAlign: "center" }}>{cena.legenda}</div> : null}
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/cenas/Fecho.tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Tokens } from "../tipos";
import { clamp, FONT } from "../ui";

export const Fecho: React.FC<{ cena: Extract<Cena, { tipo: "fecho" }>; tokens: Tokens }> = ({ cena, tokens }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const botao = spring({ frame: f - 30, fps, config: { damping: 12 } });
  const c = tokens.cores;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${c.fundo}, ${c.primaria})`, justifyContent: "center", padding: 90, gap: 60, fontFamily: FONT }}>
      <div style={{ fontSize: 76, fontWeight: 900, lineHeight: 1.1, color: c.texto, opacity: interpolate(f, [0, 12], [0, 1], clamp) }}>{cena.pergunta}</div>
      <div style={{ alignSelf: "flex-start", padding: "30px 46px", borderRadius: 999, background: "#25D366", color: "#fff", fontSize: 48, fontWeight: 900, scale: String(botao) }}>{cena.cta}</div>
      <div style={{ fontSize: 56, fontWeight: 900, letterSpacing: "0.12em", color: c.texto, opacity: botao }}>{tokens.nome}</div>
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/cenas/SeloExemplo.tsx
import type { Tokens } from "../tipos";
import { FONT } from "../ui";

export const SeloExemplo: React.FC<{ tokens: Tokens }> = ({ tokens }) => (
  <div style={{ position: "absolute", top: 70, right: 50, padding: "12px 22px", borderRadius: 12, background: "rgba(0,0,0,.55)", border: `2px solid ${tokens.cores.destaque}`, fontFamily: FONT, fontSize: 26, fontWeight: 800, letterSpacing: "0.12em", color: tokens.cores.texto }}>
    EXEMPLO ILUSTRATIVO
  </div>
);
```

```tsx
// remotion/src/cenas/Marca.tsx
import type { Tokens } from "../tipos";
import { FONT } from "../ui";

export const Marca: React.FC<{ tokens: Tokens }> = ({ tokens }) => (
  <div style={{ position: "absolute", top: 70, left: 50, padding: "12px 24px", borderRadius: 999, background: "rgba(0,0,0,.45)", fontFamily: FONT, fontSize: 28, fontWeight: 900, letterSpacing: "0.2em", color: tokens.cores.texto }}>
    {tokens.nome}
  </div>
);
```

```tsx
// remotion/src/Legenda.tsx
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { blocoAtivo } from "./timeline";
import type { Palavra, Tokens } from "./tipos";
import { clamp, FONT } from "./ui";

export const Legenda: React.FC<{ palavras: Palavra[]; tokens: Tokens }> = ({ palavras, tokens }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const bloco = blocoAtivo(palavras, t);
  if (!bloco) return null;
  const entrada = interpolate(t, [bloco[0].ini, bloco[0].ini + 0.12], [0.85, 1], clamp);
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: 1540, display: "flex", justifyContent: "center" }}>
      <div style={{ padding: "12px 26px", borderRadius: 18, background: "rgba(5,8,20,.75)", fontFamily: FONT, fontSize: 50, fontWeight: 900, color: tokens.cores.texto, scale: String(entrada) }}>
        {bloco.map((p, i) => (
          <span key={`${p.ini}-${p.w}`} style={{ color: t >= p.ini && t < p.fim + 0.05 ? tokens.cores.destaque : undefined, marginRight: i < bloco.length - 1 ? 14 : 0 }}>{p.w}</span>
        ))}
      </div>
    </div>
  );
};
```

```tsx
// remotion/src/ReelDGC.tsx
import { AbsoluteFill, Sequence } from "remotion";
import { Construcao } from "./cenas/Construcao";
import { Fecho } from "./cenas/Fecho";
import { Gancho } from "./cenas/Gancho";
import { Marca } from "./cenas/Marca";
import { Problema } from "./cenas/Problema";
import { Resultado } from "./cenas/Resultado";
import { SeloExemplo } from "./cenas/SeloExemplo";
import { Legenda } from "./Legenda";
import { sequencias } from "./timeline";
import type { Cena, PropsReel, Tokens } from "./tipos";

// O áudio é mixado fora (pipeline/mix.py), para trocar a trilha sem renderizar de novo.
const CenaPorTipo: React.FC<{ cena: Cena; tokens: Tokens }> = ({ cena, tokens }) => {
  switch (cena.tipo) {
    case "gancho": return <Gancho cena={cena} tokens={tokens} />;
    case "problema": return <Problema cena={cena} tokens={tokens} />;
    case "construcao": return <Construcao cena={cena} tokens={tokens} />;
    case "resultado": return <Resultado cena={cena} tokens={tokens} />;
    case "fecho": return <Fecho cena={cena} tokens={tokens} />;
  }
};

export const ReelDGC: React.FC<PropsReel> = (props) => {
  const seqs = sequencias(props.cortes, props.total);
  return (
    <AbsoluteFill style={{ background: props.tokens.cores.fundo }}>
      {props.cenas.map((cena, i) => (
        <Sequence key={cena.id} name={`${cena.id} ${cena.tipo}`} from={seqs[i].from} durationInFrames={seqs[i].duration} premountFor={props.fps}>
          <CenaPorTipo cena={cena} tokens={props.tokens} />
        </Sequence>
      ))}
      <Marca tokens={props.tokens} />
      {props.selo_exemplo ? <SeloExemplo tokens={props.tokens} /> : null}
      <Legenda palavras={props.palavras} tokens={props.tokens} />
    </AbsoluteFill>
  );
};
```

```tsx
// remotion/src/Root.tsx
import { Composition } from "remotion";
import smoke from "../fixtures/props-smoke.json";
import { ReelDGC } from "./ReelDGC";
import type { PropsReel } from "./tipos";

const padrao = smoke as unknown as PropsReel;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="ReelDGC"
    component={ReelDGC}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={padrao.total}
    defaultProps={padrao}
    calculateMetadata={({ props }) => ({ durationInFrames: props.total, fps: props.fps })}
  />
);
```

```ts
// remotion/src/index.ts
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
```

`remotion/fixtures/props-smoke.json` (sem imagem, para rodar no CI):
```json
{
  "fps": 30, "total": 300, "cortes": [0, 60, 120, 200, 250], "serie": "B", "selo_exemplo": true, "trilha": "a-tropical",
  "falas": [{ "id": "s1", "fala": "Seu financeiro ainda vive numa planilha?", "arquivo": "", "ini": 0.1, "fim": 1.9 }],
  "palavras": [{ "w": "Seu", "ini": 0.1, "fim": 0.3 }, { "w": "financeiro", "ini": 0.3, "fim": 0.9 }, { "w": "ainda", "ini": 0.9, "fim": 1.2 }],
  "cenas": [
    { "id": "s1", "tipo": "gancho", "headline": ["Seu financeiro", "numa planilha?"], "destaque": "planilha?" },
    { "id": "s2", "tipo": "problema", "texto": "Cada fim de mês, horas conferindo conta por conta." },
    { "id": "s3", "tipo": "construcao", "etapas": ["Entendemos", "Desenhamos", "Construímos", "Entregamos"], "tela": { "titulo": "Financeiro", "linhas": ["A pagar hoje: 4", "Vencendo na semana: 9", "Sem descrição: 0"] } },
    { "id": "s4", "tipo": "resultado", "antes": "Planilha", "depois": "1 tela", "legenda": "Tudo num lugar só." },
    { "id": "s5", "tipo": "fecho", "pergunta": "Você imagina uma solução assim na sua empresa?", "cta": "Chama a DGC no WhatsApp" }
  ],
  "tokens": { "nome": "DGC", "cores": { "fundo": "#0B1020", "primaria": "#3B82F6", "destaque": "#F59E0B", "texto": "#FFFFFF", "suave": "#94A3B8" }, "fonte": "Inter" }
}
```

- [ ] **Step 5: `pipeline/render.mjs`**

```js
// Render da composição ReelDGC com props de um card.
//   node pipeline/render.mjs remotion/src/index.ts ReelDGC --video <saida.mp4> --props <props.json>
//   node pipeline/render.mjs remotion/src/index.ts ReelDGC <pasta_stills> f1,f2,... --props <props.json>
// Rode SEMPRE com a trava (nunca dois Chromium do Remotion no Pi): flock /tmp/remotion-dgc.lock node ...
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(path.resolve("remotion/package.json"));
const { bundle } = require("@remotion/bundler");
const { renderMedia, renderStill, selectComposition, openBrowser } = require("@remotion/renderer");

const CHROME = "/home/pi/.cache/ms-playwright/chromium_headless_shell-1217/chrome-linux/headless_shell";
const args = process.argv.slice(2);
const iProps = args.indexOf("--props");
const inputProps = JSON.parse(fs.readFileSync(args[iProps + 1], "utf8"));
const [entrada, id, a, b] = args.filter((_, i) => i !== iProps && i !== iProps + 1);
const t0 = Date.now();
const serveUrl = await bundle({ entryPoint: path.resolve(entrada), publicDir: path.resolve("remotion/public") });
const opts = { serveUrl, browserExecutable: CHROME, inputProps };
const composition = await selectComposition({ ...opts, id });
if (a === "--video") {
  await renderMedia({
    ...opts, composition, codec: "h264", outputLocation: b, muted: true,
    concurrency: Number(process.env.RENDER_CONCURRENCY ?? 2), imageFormat: "jpeg", jpegQuality: 92, crf: 17,
    onProgress: ({ renderedFrames }) => { if (renderedFrames % 150 === 0) console.log(`${renderedFrames}/${composition.durationInFrames} ${((Date.now() - t0) / 1000).toFixed(0)} s`); },
  });
  console.log("ok", b);
} else {
  fs.mkdirSync(a, { recursive: true });
  const browser = await openBrowser("chrome", { browserExecutable: CHROME });
  for (const f of b.split(",").map(Number)) {
    await renderStill({ ...opts, puppeteerInstance: browser, composition, frame: f, output: path.join(a, `f${String(f).padStart(4, "0")}.jpg`), imageFormat: "jpeg", jpegQuality: 85 });
  }
  await browser.close({ silent: true });
  console.log("ok stills", ((Date.now() - t0) / 1000).toFixed(0), "s");
}
```

- [ ] **Step 6: Verificar tipos, lint e smoke local**

```bash
cd ~/projects/dgc-reels/remotion && npx tsc --noEmit && npx @biomejs/biome check --write . && npm test
cd ~/projects/dgc-reels && flock /tmp/remotion-dgc.lock node pipeline/render.mjs remotion/src/index.ts ReelDGC out/smoke 15,75,150,220,280 --props remotion/fixtures/props-smoke.json
```
Expected: tsc sem erro, testes passando, 5 JPGs em `out/smoke/`. **Abrir os 5 frames com o Read tool e conferir** gancho, cena sem imagem, método + tela, antes/depois e fecho legíveis, selo "EXEMPLO ILUSTRATIVO" visível e legenda no rodapé.

- [ ] **Step 7: Commit**

```bash
git add remotion pipeline/render.mjs
git commit -m "feat(remotion): composição ReelDGC guiada por props, cenas dos 5 atos e render"
```

---

### Task 9: Ilustração, mixagem e QA (`imagens.py`, `mix.py`, `qa.py`)

**Files:**
- Create: `pipeline/imagens.py`, `pipeline/mix.py`, `pipeline/qa.py`
- Test: `tests/test_mix.py`, `tests/test_qa.py`

**Interfaces:**
- Consumes: `tts.chave()` (Task 7), `loop.sensivel.varrer` (Task 4), `props.json`.
- Produces:
  - `pipeline/imagens.py <cenas.json> <pasta_img>` → `<pasta_img>/<sN>.png` para cada cena com `prompt_imagem` (pula as que já existem). Erros de cota escrevem "cota DIÁRIA" no stderr.
  - `pipeline/mix.py <video_mudo.mp4> <props.json> <saida.mp4>`; função pura `mix.cues(props:dict) -> list[tuple[float,str,int]]`.
  - `pipeline/qa.py <card_dir> <out_dir>` → `<out_dir>/qa.json` `{"aprovado": bool, "problemas": [str], "texto_visivel": str}`; exit 0 aprovado, 3 reprovado, 4 dado sensível; função pura `qa.decidir(resposta:dict, proibidos:list[str], selo_exigido:bool) -> tuple[int, list[str]]`; `qa.frames_chave(props:dict) -> list[int]` (meio de cada cena).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_mix.py
from pipeline.mix import cues

def test_whoosh_em_cada_corte_menos_o_primeiro_e_impacto_na_abertura():
    props = {"fps": 30, "cortes": [0, 90, 300, 600, 750], "total": 900}
    c = cues(props)
    assert c[0] == (0.0, "impact", -9)
    assert [t for t, nome, _ in c if nome == "whoosh"] == [round(90 / 30 - 0.15, 3), round(300 / 30 - 0.15, 3), round(600 / 30 - 0.15, 3), round(750 / 30 - 0.15, 3)]
    assert c[-1][1] == "ding"
```

```python
# tests/test_qa.py
from pipeline.qa import decidir, frames_chave

def test_frames_no_meio_de_cada_cena():
    assert frames_chave({"cortes": [0, 100, 300], "total": 400}) == [50, 200, 350]

def test_aprovado_quando_modelo_aprova_e_texto_limpo():
    assert decidir({"aprovado": True, "problemas": [], "texto_visivel": "EXEMPLO ILUSTRATIVO 1 tela"}, [], True) == (0, [])

def test_dado_sensivel_no_texto_visivel_da_exit_4():
    rc, probs = decidir({"aprovado": True, "problemas": [], "texto_visivel": "ligue 62 99853-6579"}, [], False)
    assert rc == 4 and "telefone" in probs[0]

def test_selo_ausente_reprova_serie_b():
    rc, probs = decidir({"aprovado": True, "problemas": [], "texto_visivel": "1 tela"}, [], True)
    assert rc == 3 and "selo" in probs[0]

def test_modelo_reprova():
    assert decidir({"aprovado": False, "problemas": ["texto cortado"], "texto_visivel": ""}, [], False) == (3, ["texto cortado"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_mix.py tests/test_qa.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# pipeline/mix.py
"""Áudio final: narração nos tempos do props.json + trilha em loop que abaixa sob a voz + efeitos nos cortes.

Uso: python3 pipeline/mix.py <video_mudo.mp4> <props.json> <saida.mp4>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def cues(props: dict) -> list[tuple[float, str, int]]:
    fps, cortes, total = props["fps"], props["cortes"], props["total"]
    out = [(0.0, "impact", -9)]
    out += [(round(c / fps - 0.15, 3), "whoosh", -9) for c in cortes[1:]]
    out.append((round(cortes[-1] / fps + 1.0, 3), "ding", -10))
    return out


def main(video: str, props_path: str, saida: str) -> None:
    props = json.loads(Path(props_path).read_text())
    dur = props["total"] / props["fps"]
    trilha = RAIZ / "audio" / "trilhas" / f"{props.get('trilha', 'a-tropical')}.wav"
    ins = ["-i", video, "-stream_loop", "-1", "-t", f"{dur:.3f}", "-i", str(trilha)]
    fil = [f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-4dB,apad,afade=t=out:st={dur - 1.5:.3f}:d=1.5[m]"]
    vozes, k = [], 2
    for f in props["falas"]:
        ins += ["-i", f["arquivo"]]
        ms = round(f["ini"] * 1000)
        fil.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
        vozes.append(f"[v{k}]"); k += 1
    fil.append(f"{''.join(vozes)}amix=inputs={len(vozes)}:normalize=0,apad=whole_dur={dur:.3f},volume=2dB,asplit=2[voz][chave]")
    fil.append("[m][chave]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350:makeup=1[mduck]")
    efx = []
    for t, nome, db in cues(props):
        ins += ["-i", str(RAIZ / "audio" / "sfx" / f"{nome}.wav")]
        ms = max(0, round(t * 1000))
        fil.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={db}dB,adelay={ms}|{ms}[e{k}]")
        efx.append(f"[e{k}]"); k += 1
    fil.append(f"[mduck][voz]{''.join(efx)}amix=inputs={2 + len(efx)}:normalize=0:duration=first,"
               f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{dur:.3f}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fil), "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", saida], check=True)
    print("ok", saida)


if __name__ == "__main__":
    main(*sys.argv[1:4])
```

```python
# pipeline/imagens.py
"""Ilustrações das cenas com Gemini Image, no estilo fixo da marca (marca/estilo-ilustracao.md).

Uso: python3 pipeline/imagens.py <cenas.json> <pasta_img>
Pula cena que já tem PNG (retomada barata depois de falha). IMAGE_MODEL padrão: gemini-2.5-flash-image.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from tts import chave  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def gerar(key: str, prompt: str, destino: Path) -> None:
    modelo = os.environ.get("IMAGE_MODEL", "gemini-2.5-flash-image")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}}
    r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=180)
    if r.status_code == 429:
        raise SystemExit("cota DIÁRIA de imagem esgotada: " + r.text[:160])
    r.raise_for_status()
    for parte in r.json()["candidates"][0]["content"]["parts"]:
        if "inlineData" in parte:
            destino.write_bytes(base64.b64decode(parte["inlineData"]["data"]))
            return
    raise SystemExit("resposta sem imagem: " + r.text[:200])


def main(cenas_path: Path, pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    estilo = (RAIZ / "marca" / "estilo-ilustracao.md").read_text().strip()
    key = chave()
    for cena in json.loads(cenas_path.read_text())["cenas"]:
        if not cena.get("prompt_imagem"):
            continue
        destino = pasta / f"{cena['id']}.png"
        if destino.exists():
            continue
        gerar(key, f"{estilo}\n\nCena: {cena['prompt_imagem']}", destino)
        print("ok", destino)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
```

```python
# pipeline/qa.py
"""QA automático: frames do meio de cada cena julgados pelo Gemini (visão) + varredura do texto visível.

Uso: python3 pipeline/qa.py <card_dir> <out_dir>
Exit 0 aprovado · 3 reprovado · 4 dado sensível. Grava <out_dir>/qa.json.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))
from loop.sensivel import carregar_proibidos, varrer  # noqa: E402
from tts import chave  # noqa: E402

PERGUNTA = """Você revisa frames de um Reel vertical de uma software house (DGC). Responda SÓ JSON:
{"aprovado": bool, "problemas": [str], "texto_visivel": str}
- texto_visivel: TODO texto legível nos frames, literal, separado por " | ".
- Reprove se: texto cortado ou sobreposto, texto ilegível, imagem com texto/logotipo deformado, frame vazio
  ou quebrado, legenda cobrindo informação importante, qualquer marca real de terceiros.
Roteiro esperado: {roteiro}"""


def frames_chave(props: dict) -> list[int]:
    bordas = props["cortes"] + [props["total"]]
    return [(a + b) // 2 for a, b in zip(bordas, bordas[1:])]


def decidir(resposta: dict, proibidos: list[str], selo_exigido: bool) -> tuple[int, list[str]]:
    texto = resposta.get("texto_visivel", "")
    achados = varrer(texto, proibidos)
    if achados:
        return 4, [f"dado sensível na tela: {a.tipo} ({a.trecho})" for a in achados]
    if selo_exigido and "EXEMPLO ILUSTRATIVO" not in texto.upper():
        return 3, ["selo EXEMPLO ILUSTRATIVO não aparece"]
    if not resposta.get("aprovado"):
        return 3, list(resposta.get("problemas") or ["reprovado sem motivo"])
    return 0, []


def main(card_dir: Path, out_dir: Path) -> int:
    props = json.loads((out_dir / "props.json").read_text())
    stills = out_dir / "qa-frames"
    fs = ",".join(str(f) for f in frames_chave(props))
    subprocess.run(["flock", "/tmp/remotion-dgc.lock", "node", "pipeline/render.mjs", "remotion/src/index.ts", "ReelDGC",
                    str(stills), fs, "--props", str(out_dir / "props.json")], check=True, cwd=RAIZ)
    roteiro = " ".join(s["fala"] for s in json.loads((card_dir / "roteiro.json").read_text())["segmentos"])
    partes = [{"text": PERGUNTA.replace("{roteiro}", roteiro)}]
    for jpg in sorted(stills.glob("*.jpg")):
        partes.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(jpg.read_bytes()).decode()}})
    modelo = os.environ.get("QA_MODEL", "gemini-2.5-flash")
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                      headers={"x-goog-api-key": chave(), "Content-Type": "application/json"},
                      json={"contents": [{"parts": partes}], "generationConfig": {"responseMimeType": "application/json"}},
                      timeout=180)
    if r.status_code == 429:
        raise SystemExit("cota DIÁRIA de visão esgotada: " + r.text[:160])
    r.raise_for_status()
    resposta = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    rc, problemas = decidir(resposta, carregar_proibidos(RAIZ / "metodo" / "proibidos.txt"), props["selo_exemplo"])
    (out_dir / "qa.json").write_text(json.dumps({**resposta, "problemas": problemas or resposta.get("problemas", []),
                                                 "aprovado": rc == 0}, ensure_ascii=False, indent=1))
    print("qa", "ok" if rc == 0 else problemas)
    return rc


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_mix.py tests/test_qa.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add pipeline/imagens.py pipeline/mix.py pipeline/qa.py tests/test_mix.py tests/test_qa.py
git commit -m "feat(pipeline): ilustração Gemini, mixagem com ducking e QA visual com bloqueio de dado sensível"
```

---

### Task 10: `loop/selecao.py`, `loop/telegram_fmt.py` e `loop/worker.py`

**Files:**
- Create: `loop/selecao.py`, `loop/telegram_fmt.py`, `loop/worker.py`, `deploy/dgc-reels-worker.service`
- Test: `tests/test_selecao.py`, `tests/test_worker.py`

**Interfaces:**
- Consumes: Tasks 2–6 e os comandos do pipeline (Tasks 7–9).
- Produces:
  - `selecao.proximo_mecanico(cards:list[Card], estado:EstadoLoop, agora:datetime) -> Card|None` — só estados `MECANICOS`, ignora `retomar_em > agora`; sem `metodo_aprovado` só cards `piloto`; prioridade: estado mais avançado, depois menor id.
  - `selecao.pacote(cards, estado) -> list[Card]` — sem método aprovado: `[piloto]` se estiver em `qa_ok`; com método: até 6 `qa_ok` se houver ≥ 6, ou todos os `qa_ok` quando não há nada em produção (`aprovada` ou `MECANICOS`).
  - `selecao.pendencias_hermes(cards, estado) -> list[dict]` — `{"tipo":"roteirizar","id"}` (cards `aprovada`, no máximo 3, só piloto antes do método), `{"tipo":"refazer","id","notas"}`. Saída estável, sem timestamp.
  - `telegram_fmt.cardapio(cards) -> str`, `.item_pacote(card) -> str`, `.rodape_pacote(ids) -> str`, `.alerta_bloqueio(card) -> str`, `.alerta_pausa(estado) -> str`, `.relatorio(cards, estado) -> str`
  - `worker.PASSOS: dict[str, list[str]]` (estado → subpassos), `worker.executar_card(card, ctx) -> None`, `worker.ciclo(ctx) -> bool` (True se fez algo), `worker.main()`
  - `@dataclass Ctx(raiz:Path, estado:EstadoLoop, agora:Callable[[], datetime], rodar:Callable[[list[str], dict, int], tuple[int,str]], enviar:Callable[[str], None], proibidos:list[str])`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_selecao.py
import datetime as dt
from loop.card import Card
from loop.estado import EstadoLoop
from loop.selecao import proximo_mecanico, pacote, pendencias_hermes

AGORA = dt.datetime(2026, 10, 11, 12, 0, tzinfo=dt.timezone.utc)

def c(id, estado, piloto=False, retomar_em=None):
    return Card(id=id, slug="x", serie="A", titulo=f"t{id}", gancho="g", resumo="r", estado=estado, piloto=piloto, retomar_em=retomar_em)

def est(tmp_path, metodo=True):
    return EstadoLoop(metodo_aprovado=metodo, caminho=tmp_path / "e.yaml")

def test_antes_do_metodo_so_o_piloto(tmp_path):
    cs = [c("01", "renderizada"), c("04", "roteirizada", piloto=True)]
    assert proximo_mecanico(cs, est(tmp_path, False), AGORA).id == "04"

def test_prioriza_o_mais_avancado_e_respeita_retomar_em(tmp_path):
    futuro = (AGORA + dt.timedelta(hours=1)).isoformat()
    cs = [c("01", "roteirizada"), c("02", "ilustrada", retomar_em=futuro), c("03", "narrada")]
    assert proximo_mecanico(cs, est(tmp_path), AGORA).id == "03"

def test_pausado_nao_seleciona(tmp_path):
    e = est(tmp_path); e.pausar("x")
    assert proximo_mecanico([c("01", "roteirizada")], e, AGORA) is None

def test_pacote_de_6_ou_flush(tmp_path):
    seis = [c(f"{i:02d}", "qa_ok") for i in range(1, 8)]
    assert [x.id for x in pacote(seis, est(tmp_path))] == ["01", "02", "03", "04", "05", "06"]
    dois = [c("01", "qa_ok"), c("02", "qa_ok"), c("03", "narrada")]
    assert pacote(dois, est(tmp_path)) == []
    assert [x.id for x in pacote(dois[:2], est(tmp_path))] == ["01", "02"]

def test_pacote_do_piloto(tmp_path):
    cs = [c("04", "qa_ok", piloto=True), c("01", "qa_ok")]
    assert [x.id for x in pacote(cs, est(tmp_path, False))] == ["04"]

def test_pendencias(tmp_path):
    cs = [c("01", "aprovada"), c("02", "aprovada"), c("03", "aprovada"), c("05", "aprovada"), c("06", "refazer")]
    cs[4].notas = ["voz mais animada"]
    p = pendencias_hermes(cs, est(tmp_path))
    assert p == [{"tipo": "roteirizar", "id": "01"}, {"tipo": "roteirizar", "id": "02"}, {"tipo": "roteirizar", "id": "03"},
                 {"tipo": "refazer", "id": "06", "notas": ["voz mais animada"]}]
```

```python
# tests/test_worker.py
import datetime as dt
import json
from loop.card import criar, carregar
from loop.estado import EstadoLoop
from loop.worker import Ctx, ciclo

AGORA = dt.datetime(2026, 10, 11, 12, 0, tzinfo=dt.timezone.utc)

def preparar(tmp_path, estado_card="roteirizada", fala="Seu financeiro vive numa planilha?"):
    (tmp_path / "backlog" / "cards").mkdir(parents=True)
    card = criar(tmp_path / "backlog" / "cards", id="4", slug="piloto", serie="A", titulo="t", gancho="g", resumo="r", estado=estado_card, piloto=True)
    (card.dir / "roteiro.json").write_text(json.dumps({"segmentos": [{"id": "s1", "fala": fala}]}))
    (card.dir / "cenas.json").write_text(json.dumps({"cenas": [{"id": "s1", "tipo": "gancho", "headline": ["x"]}]}))
    return card

def ctx(tmp_path, rodar, enviados):
    return Ctx(raiz=tmp_path, estado=EstadoLoop(caminho=tmp_path / "backlog" / "estado.yaml"), agora=lambda: AGORA,
               rodar=rodar, enviar=enviados.append, proibidos=["JASC"])

def test_passo_ok_avanca_o_card(tmp_path):
    card = preparar(tmp_path)
    chamadas = []
    assert ciclo(ctx(tmp_path, lambda cmd, env, t: (chamadas.append(cmd), (0, "ok"))[1], [])) is True
    assert carregar(card.dir).estado == "narrada"
    assert any("tts_unico.py" in " ".join(c) for c in chamadas)
    assert any("conferir_fala.py" in " ".join(c) for c in chamadas)

def test_dado_sensivel_bloqueia_sem_chamar_tts(tmp_path):
    card = preparar(tmp_path, fala="O cliente JASC pagava caro.")
    chamadas, enviados = [], []
    ciclo(ctx(tmp_path, lambda cmd, env, t: (chamadas.append(cmd), (0, ""))[1], enviados))
    c = carregar(card.dir)
    assert c.estado == "bloqueada" and c.erros[-1]["tipo"] == "sensivel"
    assert chamadas == [] and any("#04" in m for m in enviados)

def test_cota_agenda_retomada_sem_contar_falha(tmp_path):
    card = preparar(tmp_path)
    cx = ctx(tmp_path, lambda cmd, env, t: (1, "cota DIÁRIA esgotada"), [])
    ciclo(cx)
    c = carregar(card.dir)
    assert c.estado == "roteirizada" and c.retomar_em is not None and cx.estado.falhas_seguidas == 0

def test_render_falha_refaz_com_concurrency_1(tmp_path):
    card = preparar(tmp_path, estado_card="ilustrada")
    envs = []
    def rodar(cmd, env, t):
        envs.append(env)
        return (137, "Killed") if "render.mjs" in " ".join(cmd) else (0, "")
    cx = ctx(tmp_path, rodar, [])
    ciclo(cx)
    c = carregar(card.dir)
    assert c.estado == "ilustrada" and c.render_concurrency == 1 and c.tentativas == 1
    assert cx.estado.falhas_seguidas == 1

def test_qa_reprovado_volta_para_legendada(tmp_path):
    card = preparar(tmp_path, estado_card="renderizada")
    ciclo(ctx(tmp_path, lambda cmd, env, t: (3, "reprovado"), []))
    c = carregar(card.dir)
    assert c.estado == "legendada" and c.tentativas == 1

def test_circuit_breaker_avisa_uma_vez(tmp_path):
    preparar(tmp_path, estado_card="narrada")
    enviados = []
    cx = ctx(tmp_path, lambda cmd, env, t: (1, "boom"), enviados)
    cx.estado.falhas_seguidas = 2
    ciclo(cx)
    assert cx.estado.pausado and sum("pausado" in m.lower() for m in enviados) == 1

def test_envia_pacote_do_piloto_e_marca_enviada(tmp_path):
    card = preparar(tmp_path, estado_card="qa_ok")
    (tmp_path / "out" / "04").mkdir(parents=True)
    (tmp_path / "out" / "04" / "final.mp4").write_bytes(b"x")
    enviados = []
    assert ciclo(ctx(tmp_path, lambda cmd, env, t: (0, ""), enviados)) is True
    assert carregar(card.dir).estado == "enviada"
    assert any("MEDIA:" in m and "final.mp4" in m for m in enviados)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_selecao.py tests/test_worker.py -q`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# loop/selecao.py
"""Regras de escolha: próximo card mecânico, pacote de revisão e pendências criativas do Hermes."""
from __future__ import annotations

import datetime as dt

from loop.card import ESTADOS, MECANICOS, Card
from loop.estado import EstadoLoop

TAMANHO_PACOTE = 6
MAX_ROTEIROS_POR_TICK = 3


def _liberado(c: Card, estado: EstadoLoop) -> bool:
    return estado.metodo_aprovado or c.piloto


def proximo_mecanico(cards: list[Card], estado: EstadoLoop, agora: dt.datetime) -> Card | None:
    if estado.pausado:
        return None
    prontos = [c for c in cards if c.estado in MECANICOS and _liberado(c, estado)
               and (c.retomar_em is None or dt.datetime.fromisoformat(c.retomar_em) <= agora)]
    prontos.sort(key=lambda c: (-ESTADOS.index(c.estado), c.id))
    return prontos[0] if prontos else None


def pacote(cards: list[Card], estado: EstadoLoop) -> list[Card]:
    prontos = [c for c in cards if c.estado == "qa_ok"]
    if not estado.metodo_aprovado:
        return [c for c in prontos if c.piloto][:1]
    em_producao = any(c.estado in MECANICOS or c.estado == "aprovada" for c in cards)
    if len(prontos) >= TAMANHO_PACOTE or (prontos and not em_producao):
        return prontos[:TAMANHO_PACOTE]
    return []


def pendencias_hermes(cards: list[Card], estado: EstadoLoop) -> list[dict]:
    roteirizar = [c for c in cards if c.estado == "aprovada" and _liberado(c, estado)][:MAX_ROTEIROS_POR_TICK]
    out = [{"tipo": "roteirizar", "id": c.id} for c in roteirizar]
    out += [{"tipo": "refazer", "id": c.id, "notas": c.notas} for c in cards if c.estado == "refazer"]
    return out
```

```python
# loop/telegram_fmt.py
"""Textos curtos e simples das mensagens para o Gabriel."""
from __future__ import annotations

from collections import Counter

from loop.card import Card
from loop.estado import EstadoLoop

SERIES = {"A": "case real", "B": "exemplo Goiás", "C": "pequena automação", "D": "bastidores", "E": "Hermes"}


def cardapio(cards: list[Card]) -> str:
    blocos = [f"#{c.id} · Série {c.serie} ({SERIES.get(c.serie, c.serie)})\n\"{c.titulo}\" — {c.gancho}\n{c.resumo}" for c in cards]
    return "\n\n".join(blocos) + "\n\nResponda: ok tudo · ok 1-12 · corta 7 · muda 3: <o que mudar>"


def item_pacote(c: Card) -> str:
    return f"#{c.id} · {c.titulo} — Série {c.serie}"


def rodape_pacote(ids: list[str]) -> str:
    return f"Pacote com {len(ids)} vídeo(s): {', '.join('#' + i for i in ids)}.\nResponda: ok tudo · ok 1,3 · refaz 5: <o que mudar> · corta 2"


def alerta_bloqueio(c: Card) -> str:
    ult = c.erros[-1] if c.erros else {"passo": "?", "tipo": "?", "msg": ""}
    return f"⚠️ #{c.id} \"{c.titulo}\" travou em {ult['passo']} ({ult['tipo']}): {ult['msg'][:200]}\nResponda: refaz {int(c.id)}: <instrução> · corta {int(c.id)}"


def alerta_pausa(estado: EstadoLoop) -> str:
    return f"⏸️ Loop pausado: {estado.motivo}. Responda 'retoma' quando quiser continuar."


def relatorio(cards: list[Card], estado: EstadoLoop) -> str:
    n = Counter(c.estado for c in cards)
    linhas = [
        f"📊 DGC Reels — {n['aprovada_final']} aprovados de {len(cards) - n['cortada']}",
        f"Em produção: {sum(n[e] for e in ('aprovada', 'roteirizada', 'narrada', 'legendada', 'ilustrada', 'renderizada'))}",
        f"Esperando você: {n['ideia'] + n['enviada']} · Travados: {n['bloqueada']} · Refazendo: {n['refazer']}",
    ]
    if estado.pausado:
        linhas.append(f"⏸️ Pausado: {estado.motivo}")
    return "\n".join(linhas)
```

```python
# loop/worker.py
"""Worker sem LLM: executa os passos mecânicos dos cards, aplica a política de falhas e manda pacotes e alertas.

Uso: .venv/bin/python -m loop.worker     (serviço systemd: deploy/dgc-reels-worker.service)
"""
from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from loop import selecao, telegram_fmt
from loop.card import Card, listar, salvar
from loop.estado import EstadoLoop
from loop.falhas import BRT, classificar, reagir
from loop.sensivel import carregar_proibidos, varrer_card
from loop.trava import Trava

WHISPER_PY = os.environ.get("WHISPER_PYTHON", str(Path.home() / "projects/produto-hermes/.venv-transcribe/bin/python"))
TIMEOUT = {"tts": 600, "conferir_fala": 300, "legendas": 900, "imagens": 900, "tempos": 60, "render": 3600, "mix": 300, "qa": 900}
PASSOS = {
    "roteirizada": ["sensivel", "tts", "conferir_fala"],
    "narrada": ["legendas"],
    "legendada": ["imagens"],
    "ilustrada": ["tempos", "render", "mix"],
    "renderizada": ["qa"],
}


@dataclass
class Ctx:
    raiz: Path
    estado: EstadoLoop
    agora: Callable[[], dt.datetime]
    rodar: Callable[[list[str], dict, int], tuple[int, str]]
    enviar: Callable[[str], None]
    proibidos: list[str]


class FalhaPasso(Exception):
    def __init__(self, passo: str, rc: int, saida: str):
        super().__init__(f"{passo} rc={rc}")
        self.passo, self.rc, self.saida = passo, rc, saida


def _comando(passo: str, card: Card, ctx: Ctx) -> list[str]:
    py, out = str(ctx.raiz / ".venv/bin/python"), ctx.raiz / "out" / card.id
    audio = out / "audio"
    return {
        "tts": [py, "pipeline/tts_unico.py", str(card.dir / "roteiro.json"), str(audio), "Puck", "DGC"],
        "conferir_fala": [py, "pipeline/conferir_fala.py", str(audio)],
        "legendas": [WHISPER_PY, "pipeline/legendas.py", str(audio), str(out / "palavras.json")],
        "imagens": [py, "pipeline/imagens.py", str(card.dir / "cenas.json"), str(out / "img")],
        "tempos": [py, "pipeline/tempos.py", str(card.dir), str(out)],
        "render": ["flock", "/tmp/remotion-dgc.lock", "node", "pipeline/render.mjs", "remotion/src/index.ts", "ReelDGC",
                   "--video", str(out / "mudo.mp4"), "--props", str(out / "props.json")],
        "mix": [py, "pipeline/mix.py", str(out / "mudo.mp4"), str(out / "props.json"), str(out / "final.mp4")],
        "qa": [py, "pipeline/qa.py", str(card.dir), str(out)],
    }[passo]


def executar_card(card: Card, ctx: Ctx) -> None:
    (ctx.raiz / "out" / card.id).mkdir(parents=True, exist_ok=True)
    for passo in PASSOS[card.estado]:
        if passo == "sensivel":
            achados = varrer_card(card.dir, ctx.proibidos)
            if achados:
                raise FalhaPasso("sensivel", 2, "; ".join(f"{a.tipo}: {a.trecho}" for a in achados))
            continue
        env = dict(os.environ)
        if passo == "render" and card.render_concurrency:
            env["RENDER_CONCURRENCY"] = str(card.render_concurrency)
        rc, saida = ctx.rodar(_comando(passo, card, ctx), env, TIMEOUT[passo])
        if rc != 0:
            raise FalhaPasso(passo, rc, saida)
    if card.estado == "ilustrada":  # higiene: só fica o final.mp4
        (ctx.raiz / "out" / card.id / "mudo.mp4").unlink(missing_ok=True)
        shutil.rmtree(ctx.raiz / "remotion" / "public" / "cards" / card.id, ignore_errors=True)


def _tratar_falha(card: Card, f: FalhaPasso, ctx: Ctx) -> None:
    agora = ctx.agora()
    tipo = classificar(f.passo, f.rc, f.saida)
    r = reagir(tipo, f.passo, card.tentativas, agora)
    card.registrar_erro(f.passo, tipo, f.saida, agora)
    if r.acao == "esperar":
        card.retomar_em = (agora + dt.timedelta(seconds=r.espera_s)).isoformat()
        return  # cota não conta para o circuit breaker
    if r.acao == "retry":
        if r.voltar_para:
            card.estado = r.voltar_para
        card.tentativas += 1
        card.render_concurrency = r.concurrency or card.render_concurrency
        card.retomar_em = (agora + dt.timedelta(seconds=r.espera_s)).isoformat() if r.espera_s else None
    else:
        tentativas = card.tentativas
        card.mover("bloqueada")
        card.tentativas = tentativas
        ctx.enviar(telegram_fmt.alerta_bloqueio(card))
        card.notificado = True
    if ctx.estado.registrar_falha(f"#{card.id} {f.passo}"):
        ctx.enviar(telegram_fmt.alerta_pausa(ctx.estado))
        ctx.estado.alerta_pausa_enviado = True


def _enviar_pacote(cards: list[Card], ctx: Ctx) -> None:
    for c in cards:
        ctx.enviar(f"MEDIA:{ctx.raiz / 'out' / c.id / 'final.mp4'}\n{telegram_fmt.item_pacote(c)}")
        c.mover("enviada")
        salvar(c)
    ctx.enviar(telegram_fmt.rodape_pacote([c.id for c in cards]))


def ciclo(ctx: Ctx) -> bool:
    cards = listar(ctx.raiz / "backlog" / "cards")
    lote = selecao.pacote(cards, ctx.estado)
    if lote:
        _enviar_pacote(lote, ctx)
        ctx.estado.salvar()
        return True
    card = selecao.proximo_mecanico(cards, ctx.estado, ctx.agora())
    if card is None:
        return False
    try:
        executar_card(card, ctx)
        card.avancar()
        ctx.estado.registrar_sucesso(ctx.agora())
    except FalhaPasso as f:
        _tratar_falha(card, f, ctx)
    salvar(card)
    ctx.estado.salvar()
    return True


def _rodar(cmd: list[str], env: dict, timeout: int) -> tuple[int, str]:
    raiz = Path(__file__).resolve().parent.parent
    try:
        p = subprocess.run(cmd, cwd=raiz, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-4000:]
    except subprocess.TimeoutExpired:
        return 124, f"timeout de {timeout}s"


def _enviar(texto: str) -> None:
    subprocess.run(["hermes", "send", "-t", "telegram", "-q", texto], check=False, timeout=120)


def main() -> None:
    raiz = Path(__file__).resolve().parent.parent
    trava = Trava(raiz / "loop" / ".lock")
    if not trava.adquirir():
        sys.exit("outro worker está rodando")
    try:
        while True:
            ctx = Ctx(raiz, EstadoLoop.carregar(raiz / "backlog" / "estado.yaml"), lambda: dt.datetime.now(BRT),
                      _rodar, _enviar, carregar_proibidos(raiz / "metodo" / "proibidos.txt"))
            fez = ciclo(ctx)
            trava.bater()
            time.sleep(5 if fez else 60)
    finally:
        trava.liberar()


if __name__ == "__main__":
    main()
```

`deploy/dgc-reels-worker.service`:
```ini
[Unit]
Description=DGC Reels - worker de produção (sem LLM)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/pi/projects/dgc-reels
ExecStart=/home/pi/projects/dgc-reels/.venv/bin/python -m loop.worker
Environment=TZ=America/Sao_Paulo
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
Restart=on-failure
RestartSec=60
Nice=10

[Install]
WantedBy=default.target
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest -q`
Expected: PASS (todos os testes até aqui)

- [ ] **Step 5: Commit**

```bash
git add loop/selecao.py loop/telegram_fmt.py loop/worker.py deploy/dgc-reels-worker.service tests/test_selecao.py tests/test_worker.py
git commit -m "feat(loop): worker sem LLM com seleção, pacotes de revisão, alertas e política de falhas"
```

---

### Task 11: `loop/cli.py`, watchdog, relatório e revisão automática de PR

**Files:**
- Create: `loop/cli.py`, `scripts/watchdog.sh`, `scripts/relatorio.sh`, `scripts/revisar_pr.sh`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Tasks 2–10.
- Produces (todos rodando a partir da raiz do repo com `.venv/bin/python -m loop.cli`):
  - `pendencias` → JSON estável de `selecao.pendencias_hermes` (monitor script do Hermes)
  - `aplicar "<texto>"` → aplica as respostas do Gabriel, salva e imprime JSON `{"mensagens": [...], "tarefas_hermes": [...]}`
  - `criar-card --id N --slug S --serie A --titulo T --gancho G --resumo R [--piloto]`
  - `marcar <id> <estado>` (o Hermes usa depois de escrever `roteiro.json` + `cenas.json` → `roteirizada`)
  - `cardapio` → texto do cardápio (cards em `ideia`)
  - `status` / `relatorio` → `telegram_fmt.relatorio`
  - `pausar "<motivo>"` / `retomar`
  - `saude` → linhas de problema para o watchdog (vazio se estiver tudo bem)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import json
from loop import cli
from loop.card import criar, carregar

def preparar(tmp_path):
    (tmp_path / "backlog" / "cards").mkdir(parents=True)
    return criar(tmp_path / "backlog" / "cards", id="3", slug="clinica", serie="B", titulo="Clínica", gancho="g", resumo="r")

def test_aplicar_salva_e_devolve_json(tmp_path, capsys):
    card = preparar(tmp_path)
    cli.main(["aplicar", "ok 3"], raiz=tmp_path)
    saida = json.loads(capsys.readouterr().out)
    assert saida["mensagens"] == ["#03 aprovada"]
    assert carregar(card.dir).estado == "aprovada"

def test_marcar_exige_roteiro_e_cenas_para_roteirizada(tmp_path, capsys):
    card = preparar(tmp_path)
    assert cli.main(["marcar", "3", "roteirizada"], raiz=tmp_path) == 2
    (card.dir / "roteiro.json").write_text("{}"); (card.dir / "cenas.json").write_text("{}")
    assert cli.main(["marcar", "3", "roteirizada"], raiz=tmp_path) == 0
    assert carregar(card.dir).estado == "roteirizada"

def test_pendencias_e_estavel(tmp_path, capsys):
    card = preparar(tmp_path); card.mover("aprovada")
    from loop.card import salvar; salvar(card)
    from loop.estado import EstadoLoop
    e = EstadoLoop.carregar(tmp_path / "backlog" / "estado.yaml"); e.metodo_aprovado = True; e.salvar()
    cli.main(["pendencias"], raiz=tmp_path); a = capsys.readouterr().out
    cli.main(["pendencias"], raiz=tmp_path); b = capsys.readouterr().out
    assert a == b and json.loads(a) == [{"tipo": "roteirizar", "id": "03"}]

def test_saude_reclama_de_temperatura(tmp_path, capsys):
    preparar(tmp_path)
    linhas = cli.saude(tmp_path, temperatura=82.0, livre_gb=50.0, worker_ativo=True)
    assert any("temperatura" in l for l in linhas)
    assert cli.saude(tmp_path, temperatura=60.0, livre_gb=50.0, worker_ativo=True) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py -q`
Expected: FAIL com `ImportError` / `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# loop/cli.py
"""CLI do loop. Usada pelo Hermes (pendências, aplicar respostas, marcar card) e pelos scripts do cron."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

from loop import selecao, telegram_fmt
from loop.aplicar import aplicar
from loop.card import MECANICOS, criar, listar, normalizar_id, salvar
from loop.estado import EstadoLoop
from loop.falhas import BRT
from loop.respostas import parse

RAIZ = Path(__file__).resolve().parent.parent
SEM_PROGRESSO_S = 2 * 3600


def saude(raiz: Path, temperatura: float, livre_gb: float, worker_ativo: bool) -> list[str]:
    estado = EstadoLoop.carregar(raiz / "backlog" / "estado.yaml")
    cards = listar(raiz / "backlog" / "cards")
    problemas = []
    if not worker_ativo:
        problemas.append("worker parado (systemctl --user status dgc-reels-worker)")
    if temperatura > 80:
        problemas.append(f"temperatura do Pi em {temperatura:.0f} °C: renders pausados")
        estado.pausar(f"temperatura {temperatura:.0f} °C")
    if livre_gb < 10:
        problemas.append(f"só {livre_gb:.1f} GB livres no disco: renders pausados")
        estado.pausar(f"disco com {livre_gb:.1f} GB livres")
    produzindo = any(c.estado in MECANICOS and c.retomar_em is None for c in cards) and not estado.pausado
    if produzindo and estado.ultima_mudanca:
        parado = (dt.datetime.now(BRT) - dt.datetime.fromisoformat(estado.ultima_mudanca)).total_seconds()
        if parado > SEM_PROGRESSO_S:
            problemas.append(f"nenhum card avançou há {parado / 3600:.1f} h")
    if problemas:
        estado.salvar()
    return problemas


def _medir() -> tuple[float, float, bool]:
    temp = float(subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True).stdout.split("=")[1].split("'")[0])
    livre = shutil.disk_usage("/").free / 1e9
    ativo = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "dgc-reels-worker"]).returncode == 0
    return temp, livre, ativo


def main(argv: list[str] | None = None, raiz: Path = RAIZ) -> int:
    ap = argparse.ArgumentParser(prog="loop.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pendencias"); sub.add_parser("cardapio"); sub.add_parser("status"); sub.add_parser("relatorio")
    sub.add_parser("retomar"); sub.add_parser("saude")
    p = sub.add_parser("aplicar"); p.add_argument("texto")
    p = sub.add_parser("pausar"); p.add_argument("motivo")
    p = sub.add_parser("marcar"); p.add_argument("id"); p.add_argument("estado")
    p = sub.add_parser("criar-card")
    for campo in ("id", "slug", "serie", "titulo", "gancho", "resumo"):
        p.add_argument(f"--{campo}", required=True)
    p.add_argument("--piloto", action="store_true")
    a = ap.parse_args(argv)

    cards_dir = raiz / "backlog" / "cards"
    estado = EstadoLoop.carregar(raiz / "backlog" / "estado.yaml")
    cards = listar(cards_dir)

    if a.cmd == "pendencias":
        print(json.dumps(selecao.pendencias_hermes(cards, estado), ensure_ascii=False))
    elif a.cmd == "aplicar":
        r = aplicar(parse(a.texto), cards, estado)
        for c in cards:
            salvar(c)
        estado.salvar()
        print(json.dumps({"mensagens": r.mensagens, "tarefas_hermes": r.tarefas_hermes}, ensure_ascii=False))
    elif a.cmd == "marcar":
        alvo = next((c for c in cards if c.id == normalizar_id(a.id)), None)
        if alvo is None:
            print(f"#{a.id} não existe", file=sys.stderr); return 2
        if a.estado == "roteirizada" and not ((alvo.dir / "roteiro.json").exists() and (alvo.dir / "cenas.json").exists()):
            print("faltam roteiro.json e cenas.json", file=sys.stderr); return 2
        alvo.mover(a.estado); salvar(alvo)
    elif a.cmd == "criar-card":
        criar(cards_dir, id=a.id, slug=a.slug, serie=a.serie, titulo=a.titulo, gancho=a.gancho, resumo=a.resumo, piloto=a.piloto)
    elif a.cmd == "cardapio":
        print(telegram_fmt.cardapio([c for c in cards if c.estado == "ideia"]))
    elif a.cmd in ("status", "relatorio"):
        print(telegram_fmt.relatorio(cards, estado))
    elif a.cmd == "pausar":
        estado.pausar(a.motivo); estado.salvar()
    elif a.cmd == "retomar":
        estado.retomar(); estado.salvar()
    elif a.cmd == "saude":
        for linha in saude(raiz, *_medir()):
            print("⚠️ " + linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/watchdog.sh` (só imprime quando há problema; stdout vazio = cron silencioso):
```bash
#!/usr/bin/env bash
set -uo pipefail
cd /home/pi/projects/dgc-reels
.venv/bin/python -m loop.cli saude
```

`scripts/relatorio.sh`:
```bash
#!/usr/bin/env bash
set -uo pipefail
cd /home/pi/projects/dgc-reels
.venv/bin/python -m loop.cli relatorio
```

`scripts/revisar_pr.sh` (revisão automática pelo `claude-20b` + merge automático só neste repo):
```bash
#!/usr/bin/env bash
# Uso: scripts/revisar_pr.sh <numero_do_pr>
# Exit 0 = mergeado · 10 = pediu mudança (implementador corrige) · 20 = parar e chamar o Gabriel · 1 = erro
set -euo pipefail
cd /home/pi/projects/dgc-reels
PR="$1"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
gh pr diff "$PR" > "$TMP/diff.patch"
cat > "$TMP/prompt.md" <<EOF
Você é o revisor independente do repo dgc-reels. Revise o PR #$PR (diff em $TMP/diff.patch).
Leia CLAUDE.md, metodo/METODO.md e ~/dgc-hub/docs/DGC_REELS_DESIGN.md.
Verifique: bugs de correção, quebra de contrato entre loop/pipeline/remotion, testes cobrindo a mudança,
violação das restrições duras, qualquer dado sensível (telefone, CNPJ, nome de cliente, chave), e se os
segredos continuam fora do git. NÃO edite arquivos.
Termine com UMA linha exatamente assim: "VEREDITO: APROVADO" ou "VEREDITO: MUDANCAS", seguida da lista do que mudar.
EOF
dev run reels --role review --profile 20b --quiet --timeout-min 30 --prompt-file "$TMP/prompt.md" > "$TMP/review.md" || { echo "revisor falhou"; exit 1; }
gh pr comment "$PR" --body-file "$TMP/review.md"
if grep -q "^VEREDITO: APROVADO" "$TMP/review.md"; then
  gh pr checks "$PR" --watch --fail-fast || { hermes send -t telegram -q "⚠️ PR #$PR do dgc-reels: review aprovado mas CI vermelho"; exit 20; }
  gh pr merge "$PR" --squash --delete-branch
  hermes send -t telegram -q "✅ PR #$PR do dgc-reels mergeado (review aprovado + CI verde)"
  exit 0
fi
PEDIDOS=$(gh pr view "$PR" --json comments --jq '[.comments[].body | select(test("^VEREDITO: MUDANCAS"; "m"))] | length')
if [ "$PEDIDOS" -ge 2 ]; then
  hermes send -t telegram -q "🛑 PR #$PR do dgc-reels: revisor pediu mudança 2x. Parei — preciso de você."
  exit 20
fi
exit 10
```
(O veredito é comentário, não review formal: o GitHub não deixa a mesma conta `g-Ac` aprovar o próprio PR.)

```bash
chmod +x scripts/*.sh
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add loop/cli.py tests/test_cli.py scripts
git commit -m "feat(loop): CLI do Hermes, watchdog, relatório e revisão automática de PR"
```

---

### Task 12: Skill do Hermes, serviço, cron e prova ponta a ponta

**Files:**
- Create: `deploy/hermes-skill/SKILL.md` → instalar em `~/.hermes/skills/software-development/dgc-reels/SKILL.md`
- Create: `~/.hermes/scripts/dgc_reels_pendencias.sh`, `~/.hermes/scripts/dgc_reels_watchdog.sh`, `~/.hermes/scripts/dgc_reels_relatorio.sh`
- Install: `~/.config/systemd/user/dgc-reels-worker.service`

**Interfaces:**
- Consumes: tudo da Fase 0.
- Produces: skill `dgc-reels`; jobs `dgc-reels-tick`, `dgc-reels-watchdog`, `dgc-reels-relatorio`; worker ativo.

- [ ] **Step 1: Escrever a skill**

`deploy/hermes-skill/SKILL.md`:
```markdown
---
name: dgc-reels
description: Opera o motor de Reels da DGC — roteiriza cards, aplica respostas do Gabriel no Telegram, abre PR de código com revisão automática. Use para qualquer mensagem sobre vídeos/Reels/cardápio da DGC ou respostas como "ok tudo", "corta 7", "muda 3: ...", "refaz 5: ...", "pausa", "retoma", "status".
---

# dgc-reels

Repo: ~/projects/dgc-reels (sempre `cd` nele). Spec: ~/dgc-hub/docs/DGC_REELS_DESIGN.md. Método: metodo/METODO.md.
CLI: `.venv/bin/python -m loop.cli <comando>`.

## Quem faz o quê
- O **worker** (serviço `dgc-reels-worker`, sem LLM) faz voz, legenda, ilustração, render, QA, e manda os pacotes e alertas.
- **Você** faz só o criativo: cardápio, roteiro e cenas, refações. E aplica as respostas do Gabriel.
- **Nunca** publique no Instagram. **Nunca** commite `out/`, áudio, vídeo ou chaves.

## Resposta do Gabriel no Telegram
1. Rode `loop.cli aplicar "<mensagem exata>"`.
2. Confirme em 1 linha com as `mensagens` do JSON.
3. Para cada `tarefas_hermes`:
   - `reescrever_ideia`: reescreva título/gancho/resumo do card (edite card.yaml), mande só aquele item de novo.
   - `perguntar`: pergunte de volta o que ele quis dizer. Nunca adivinhe.
   - `status`: responda com `loop.cli status`.
4. Commit: `git add backlog && git commit -m "chore(backlog): <resumo>"`.

## Roteirizar (pendência `roteirizar`)
1. Leia card.yaml, metodo/METODO.md e, para série A, os docs do caso em ~/projects/gestao-360/docs/ (somente leitura).
2. Escreva roteiro.json e cenas.json no diretório do card, seguindo o schema do METODO.md (5 atos, s1..s5).
3. Série B: `"selo_exemplo": true`. Fecho sempre com a pergunta "Você imagina uma solução assim na sua empresa?".
4. Confira as restrições duras. Sem R$, sem nome de cliente, sem telefone, sem concorrente pelo nome.
5. `loop.cli marcar <id> roteirizada` e commit do card.

## Refazer (pendência `refazer`)
Leia `notas`. Se a nota for sobre texto/roteiro/cenas → reescreva e `marcar <id> roteirizada`.
Se for só sobre voz → apague out/<id>/audio e `marcar <id> roteirizada`.
Se for sobre visual que o template não suporta → é mudança de código (abaixo); depois `marcar <id> ilustrada`.

## Mudança de código (template, cenas novas, pipeline)
1. `dev run reels --role build --profile 20a --prompt "<tarefa>. Crie branch feat/<slug>, TDD, rode .venv/bin/pytest -q e npm test em remotion/, abra PR com gh."`
2. `scripts/revisar_pr.sh <n>`: exit 0 mergeado · 10 mande o 20a corrigir com os comentários do PR e rode de novo · 20 pare e avise o Gabriel.

## Controle
`loop.cli pausar "<motivo>"` / `loop.cli retomar` · worker: `systemctl --user status dgc-reels-worker` · log: `journalctl --user -u dgc-reels-worker`.
```

```bash
mkdir -p ~/.hermes/skills/software-development/dgc-reels
cp ~/projects/dgc-reels/deploy/hermes-skill/SKILL.md ~/.hermes/skills/software-development/dgc-reels/SKILL.md
```

- [ ] **Step 2: Scripts do cron do Hermes**

```bash
cat > ~/.hermes/scripts/dgc_reels_pendencias.sh <<'EOF'
#!/usr/bin/env bash
cd /home/pi/projects/dgc-reels && .venv/bin/python -m loop.cli pendencias
EOF
cat > ~/.hermes/scripts/dgc_reels_watchdog.sh <<'EOF'
#!/usr/bin/env bash
exec /home/pi/projects/dgc-reels/scripts/watchdog.sh
EOF
cat > ~/.hermes/scripts/dgc_reels_relatorio.sh <<'EOF'
#!/usr/bin/env bash
exec /home/pi/projects/dgc-reels/scripts/relatorio.sh
EOF
chmod +x ~/.hermes/scripts/dgc_reels_*.sh
~/.hermes/scripts/dgc_reels_pendencias.sh
```
Expected: `[]`

- [ ] **Step 3: Prova ponta a ponta com o card de smoke (antes de ligar o serviço)**

```bash
cd ~/projects/dgc-reels
.venv/bin/python -m loop.cli criar-card --id 0 --slug smoke --serie B --titulo "Smoke" --gancho "teste" --resumo "teste ponta a ponta" --piloto
cat > backlog/cards/00-smoke/roteiro.json <<'EOF'
{"titulo": "smoke", "voz": "Puck", "estilo": "Locução animada e natural em português do Brasil. Diga \"está\" e \"para\". Leia apenas o texto.",
 "segmentos": [{"id": "s1", "fala": "Seu financeiro ainda vive numa planilha?"}, {"id": "s2", "fala": "Todo fim de mês são horas conferindo conta por conta."},
  {"id": "s3", "fala": "A gente entende o seu processo, desenha e constrói um sistema sob medida."}, {"id": "s4", "fala": "Tudo numa tela só."},
  {"id": "s5", "fala": "Você imagina uma solução assim na sua empresa? Chama a DGC."}]}
EOF
python3 - <<'EOF'
import json; p = json.load(open("remotion/fixtures/props-smoke.json"))
c = p["cenas"]; c[1]["prompt_imagem"] = "empresário cansado olhando pilhas de papel e uma planilha no notebook"
json.dump({"serie": "B", "selo_exemplo": True, "trilha": "a-tropical", "cenas": c}, open("backlog/cards/00-smoke/cenas.json", "w"), ensure_ascii=False, indent=1)
EOF
.venv/bin/python -m loop.cli marcar 0 roteirizada
for i in 1 2 3 4 5 6; do .venv/bin/python -c "
import datetime as dt; from pathlib import Path
from loop.worker import Ctx, ciclo, _rodar, _enviar
from loop.estado import EstadoLoop; from loop.falhas import BRT; from loop.sensivel import carregar_proibidos
r = Path('.').resolve()
print(ciclo(Ctx(r, EstadoLoop.carregar(r/'backlog/estado.yaml'), lambda: dt.datetime.now(BRT), _rodar, print, carregar_proibidos(r/'metodo/proibidos.txt'))))
"; grep '^estado' backlog/cards/00-smoke/card.yaml; done
```
Expected: o estado avança `narrada → legendada → ilustrada → renderizada → qa_ok → enviada` (o último ciclo imprime `MEDIA:.../out/00/final.mp4`). Se algum passo falhar, o card mostra `tentativas`/`erros`: corrigir a causa antes de seguir. **Assistir `out/00/final.mp4`** (`ffprobe` para conferir duração 9:16 e áudio; extrair 3 frames com `ffmpeg -ss` e abrir com o Read tool).

Depois: `git checkout backlog/estado.yaml && rm -rf backlog/cards/00-smoke out/00` (o smoke não entra no lote).

- [ ] **Step 4: Instalar o worker**

```bash
cp ~/projects/dgc-reels/deploy/dgc-reels-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now dgc-reels-worker
sleep 5 && systemctl --user is-active dgc-reels-worker
```
Expected: `active`

- [ ] **Step 5: Criar os jobs do Hermes (pausados até o Telegram estar configurado)**

```bash
hermes cron create "20m" "Pendências do DGC Reels mudaram (diff acima). Siga a skill dgc-reels: roteirize/refaça os cards indicados, marque, commite. Não mande mensagem ao Gabriel a não ser que precise de decisão dele." \
  --name dgc-reels-tick --skill dgc-reels --monitor-script dgc_reels_pendencias.sh --workdir /home/pi/projects/dgc-reels \
  --deliver local --failure-deliver telegram --paused --paused-reason "aguardando Telegram no gateway"
hermes cron create "30m" --name dgc-reels-watchdog --no-agent --script dgc_reels_watchdog.sh --deliver telegram --paused --paused-reason "aguardando Telegram no gateway"
hermes cron create "0 8 * * *" --name dgc-reels-relatorio --no-agent --script dgc_reels_relatorio.sh --deliver telegram --paused --paused-reason "aguardando Telegram no gateway"
hermes cron list
```
Expected: 3 jobs `paused`.

- [ ] **Step 6: Ativar (depois de `hermes gateway setup` com Telegram)**

```bash
hermes send -t telegram "DGC Reels: teste de canal. Responda 'status'."
hermes cron resume dgc-reels-tick && hermes cron resume dgc-reels-watchdog && hermes cron resume dgc-reels-relatorio
```
Expected: mensagem chega; ao responder "status", o Hermes devolve o relatório (skill acionada pelo gateway).

- [ ] **Step 7: Commit**

```bash
git add deploy/hermes-skill/SKILL.md
git commit -m "docs(deploy): skill dgc-reels do Hermes"
git push
```

---

## Fora da Fase 0 (entram por PR durante o sprint, só se o piloto pedir)

- **Lottie** (`@remotion/lottie`): animações prontas na cena `construcao`/`resultado`, com licença anotada em `trilhas/LICENCAS.md`.
- **Capa por série** (`renderStill` de um quadro do gancho com título grande), enviada junto do MP4 no pacote.
- **Veo**: desligado. Só com decisão explícita do Gabriel (custo/cota).
- **Biome**: se `configs/biome.json` do dgc-hub for de schema antigo, rodar `npx @biomejs/biome migrate --write` no Step 1 da Task 8.

---

# FASE 1 — Operação (executada pelo Hermes, sáb 11 → seg 13)

Pré-condição: Fase 0 completa, worker ativo, Telegram ok, jobs ativos. Toda mensagem ao Gabriel é curta e
simples. Toda mudança de backlog é commitada.

### O1: Identidade DGC (sáb 11, manhã)

- [ ] Gerar 3 propostas. Cada uma tem: nome do conceito, paleta (5 cores no formato de `marca/tokens.json`), fonte (Google Fonts com licença OFL) e bio do Instagram (≤ 150 caracteres, foco em Goiânia e sistemas sob medida). Gerar também 1 conceito de logo por proposta via Gemini Image (`pipeline/imagens.py` adaptado num script avulso em `out/identidade/`).
- [ ] Renderizar o card de smoke com cada paleta (3 stills de gancho) para o Gabriel ver aplicado.
- [ ] Enviar: `hermes send -t telegram "MEDIA:out/identidade/p1.jpg\nProposta 1 — <conceito>"` (×3) + "Responda 1, 2 ou 3 (ou o que mudar)".
- [ ] Com a escolha: gravar `marca/tokens.json` com `"provisorio": false`, salvar o logo em `marca/` e commitar `feat(marca): identidade DGC aprovada`. Se a fonte mudar, trocar `remotion/public/Inter.ttf` e o `FONT` via PR (fluxo de código com revisão).

### O2: Cardápio do lote 01 (sáb 11)

- [ ] Criar 39 cards com `loop.cli criar-card` (ids 01–39) na composição da spec §3:
  - **Série A (8):** tesouraria 32 telas → 1 (**#04, `--piloto`**), controladoria (BI pago com a receita errada), cobrança automática com IA, atendimento centralizado (conversa sem dono), RH saindo do sistema pago, TI saindo da planilha de 101 ativos, marketing com revisão humana, livro-caixa fora do ERP com IA que propõe e humano aprova.
  - **Série B (15):** exemplos de Goiás (pecuária: rebanho, pesagem, vacinação; confecção da Região da 44; clínica; construtora; distribuidora; escritório contábil; autopeças; oficina; imobiliária; escola; restaurante; transportadora; loja de material de construção; agro: estoque de insumos; academia).
  - **Série C (8):** pastas organizadas sozinhas, planilha virando sistema, relatório que chega no WhatsApp, nota fiscal lida automaticamente, agenda sem conflito, backup automático, formulário que vira cadastro, alerta de conta a vencer.
  - **Série D (4):** quem é a DGC, o Método DGC (8 etapas), um dia construindo um sistema, por que sob medida.
  - **Série E (4):** Hermes atende de madrugada, Hermes abre chamado, Hermes chama um humano, Hermes aprende com a base da empresa — **só funcionalidades que existem hoje** no produto-hermes.
- [ ] Ordem do lote: piloto #04 primeiro, depois intercalar as séries (A, B, C, B, A, D…) para o estoque já sair variado.
- [ ] `loop.cli cardapio` → enviar ao Gabriel em 3 mensagens (13 ideias cada).
- [ ] Aplicar as respostas (skill). Meta: cardápio aprovado no sábado.

### O3: Piloto (sáb 11, noite)

- [ ] Roteirizar o #04 (pendência `roteirizar`), marcar `roteirizada`. O worker produz e envia sozinho.
- [ ] Gabriel aprova com "ok 4" → `metodo_aprovado: true` → produção em série liberada automaticamente.
- [ ] Se vier "refaz 4: ...", tratar como refação. Se for visual que o template não suporta → fluxo de código (PR + `scripts/revisar_pr.sh`).

### O4: Produção em série (dom 12 → seg 13)

- [ ] O tick a cada 20 min roteiriza até 3 cards por vez; o worker produz e manda pacotes de 6.
- [ ] Acompanhar o relatório das 8h e os alertas. Card bloqueado → ler o erro e decidir: refazer o roteiro (dado sensível, QA), abrir PR (bug de código) ou pedir decisão ao Gabriel.
- [ ] Meta de segunda: ≥ 12 cards em `aprovada_final`.

### O5: Modo noturno (seg 13, fim do dia)

- [ ] `hermes cron edit dgc-reels-tick` → agenda `*/30 22-23,0-6 * * *`.
- [ ] Mandar resumo final do sprint ao Gabriel (`loop.cli relatorio` + o que falta).
- [ ] Registrar o fechamento do sprint em `~/obsidian-vault/context/projetos/dgc-hub/2026-10-13-dgc-reels-sprint.md`.
