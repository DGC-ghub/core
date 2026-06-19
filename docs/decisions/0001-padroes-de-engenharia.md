# ADR 0001 — Padrões de engenharia da DGC Hub

- **Status:** Aceito
- **Data:** 2026-06-18
- **Decisores:** Gabriel, Danilo

## Contexto

A DGC Hub é uma software house tocada por 2 desenvolvedores (Gabriel e Danilo)
que atende clientes externos. Sem um padrão comum, cada projeto nasceria
diferente — o que atrapalha onboarding, revisão de PR um do outro e manutenção.
Este ADR fixa o padrão de engenharia e a natureza do repositório `core`.

O padrão é calibrado para **2 devs**: claro o bastante para alinhar os dois, sem
a burocracia de uma empresa grande.

## Decisões

### 1. `core` é o playbook, não um monorepo de código

A DGC Hub adota **multi-repo puro**: cada sistema, produto ou automação vive em
seu próprio repositório. O `core` guarda apenas padrões, documentação, configs
base compartilhadas e o índice dos demais repos.

```
core/
├── README.md
├── docs/
│   ├── STACK.md           # frameworks oficiais + versões
│   ├── CONVENTIONS.md     # branches, commits, nomeação, PR
│   ├── QUALITY.md         # Biome, TS strict, Vitest, pre-commit, CI
│   ├── REPOS.md           # multi-repo: naming, como criar projeto novo
│   └── decisions/         # ADRs (este arquivo é o 0001)
├── .github/workflows/
│   └── ci-node.yml        # reusable workflow chamado pelos outros repos
├── configs/               # biome.json e tsconfig.base.json base p/ herdar
├── .editorconfig
└── .gitignore
```

As pastas `automations/` e `systems/` do esqueleto inicial (pensadas para
monorepo) são removidas.

> **Por quê multi-repo:** isolamento de deploy e de acesso por cliente — um
> freela/cliente vê só o repo dele, não todos os projetos.
>
> **Como manter consistência sem monorepo:** `configs/` + o reusable workflow
> `ci-node.yml`. Muda-se num lugar e vale para todos os repos que herdam.

### 2. Stack oficial

| Camada       | Tecnologias |
|--------------|-------------|
| Frontend     | React 19 + Vite + TypeScript + Tailwind + Shadcn/ui + React Router v7 + TanStack Query + Zustand + React Hook Form + Zod |
| Backend      | Node + Fastify + Prisma + PostgreSQL (prod) / SQLite (dev) + Zod + JWT + Pino |
| Python (nichos) | FastAPI ou script puro · `uv` (deps) · `ruff` (lint/format) · `pytest` |
| Infra        | Docker Compose + GitHub Actions + Caddy (auto-SSL) / Nginx |

**Política de linguagem:** TypeScript/Node em tudo que é web/API/produto. Python
entra só onde brilha — IA/ML, scraping pesado, data.

### 3. Templates via GitHub Template Repositories

Cada template é um repo próprio marcado como _Template_ no GitHub. Projeto novo =
botão **"Use this template"**.

- **`dgc-template-ts`** — base TS fullstack com pastas `web/` e `api/`; apaga-se a
  que não for usada (produto só-front, só-api ou fullstack saem todos daqui).
- **`dgc-template-py`** — Python enxuto: script/automação, com opção de virar
  API FastAPI.

Cada template nasce com: Biome, `tsconfig` strict (herdando de `core/configs`),
Vitest/pytest, Husky + lint-staged, CI apontando para o reusable workflow do
`core`, `.env.example`, README e estrutura de pastas.

### 4. Qualidade

- **Lint + format:** Biome (uma ferramenta só).
- **Tipos:** TypeScript `strict: true`.
- **Testes:** Vitest (TS) / pytest (Python). Sem gate de cobertura por ora —
  pragmático para 2 devs; pode endurecer depois.
- **Pre-commit:** Husky + lint-staged rodando `biome` + `tsc` apenas no que mudou.
- **CI (por PR):** `lint → typecheck → test → build`.

### 5. Git e fluxo de trabalho

- Branches: `main` + `feature/<x>`, `fix/<x>`, `hotfix/<x>` (ver `CONVENTIONS.md`).
- Commits: Conventional Commits.
- `main` protegida: **CI verde obrigatório** para merge.
- **PR review recomendado** (um revisa o outro), porém **não-bloqueante** — para
  não travar quando um dev estiver ausente. Pode-se exigir 1 review no futuro.

### 6. Convenção de nomes de repositório

| Tipo               | Padrão              | Exemplo            |
|--------------------|---------------------|--------------------|
| Template           | `dgc-template-*`    | `dgc-template-ts`  |
| Interno / automação| `dgc-<nome>`        | `dgc-ci-bot`       |
| Produto de cliente | `<cliente>-<produto>` | `ipeconect-painel` |

## Consequências

- **Positivas:** repos novos nascem idênticos e prontos (stack, lint, CI);
  isolamento por cliente; padrão de revisão e onboarding claro para os 2 devs.
- **Custos:** manter os 2 template repos e o reusable workflow atualizados;
  código compartilhado entre repos exige publicar pacote ou copiar (aceito por
  ora — YAGNI).

## Próximos passos (implementação)

1. Reestruturar o `core`: remover `automations/` e `systems/`, criar `docs/STACK.md`,
   `docs/QUALITY.md`, `docs/REPOS.md`, `configs/` e `.github/workflows/ci-node.yml`.
2. Criar os repos `dgc-template-ts` e `dgc-template-py` e marcá-los como Template.
3. Configurar branch protection (CI obrigatório) na `main` dos repos.
