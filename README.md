# DGC Hub — `core`

Playbook de engenharia e operação da software house **DGC Hub**.

Este repositório **não** hospeda código de produto — a DGC Hub usa **multi-repo puro**, cada sistema em seu próprio repositório. Aqui ficam padrões, configs base, CI compartilhado, docs operacionais, esteira comercial/técnica e decisões estratégicas.

## Comece aqui — entenda a ideia antes dos detalhes

[Leia o guia simples da DGC](docs/COMECE_AQUI.md): o que queremos vender, um exemplo de automação Microsoft 365, o que ainda não foi feito e o único próximo passo.

Esta é uma proposta de foco para validação, não uma solução pronta ou uma mudança automática de prioridade dos projetos existentes. Os planos anteriores abaixo permanecem como histórico e referência.

## Conteúdo

```text
core/
├── docs/
│   ├── COMECE_AQUI.md                   # ideia M365 em português simples + estado e próximo passo
│   ├── STACK.md                         # stack oficial + versões
│   ├── QUALITY.md                       # Biome, TS strict, Vitest, pre-commit, CI
│   ├── REPOS.md                         # multi-repo: naming e como criar projeto novo
│   ├── CONVENTIONS.md                   # branches, commits, nomeação, PR
│   ├── DGC_OPERATING_SYSTEM.md          # posicionamento, oferta, workflow e stack operacional
│   ├── OFERTAS_E_PRECIFICACAO.md        # pacotes iniciais e faixas de preço
│   ├── PLAYBOOK_COMERCIAL.md            # triagem, perguntas, red flags e fluxo comercial
│   ├── ROADMAP_30_DIAS.md               # plano de 30 dias para operação mínima vendável
│   ├── ESTRATEGIA_PRODUTOS_E_NICHOS.md  # portfólio próprio, nichos e cardápio de soluções
│   ├── PRODUTO_HERMES_ESTRATEGIA_MVP.md # estratégia MVP do WhatsApp IA
│   ├── CHECKPOINT_RETOMADA_2026-06-19.md # ponto exato para retomar o Produto Hermes
│   ├── templates/                       # diagnóstico, proposta, briefing e entrega
│   └── decisions/                       # ADRs — registro de decisões
├── configs/                             # biome.json e tsconfig.base.json base p/ herdar
└── .github/workflows/                   # ci-node.yml — reusable workflow dos repos
```

## Começar um projeto novo

Use **"Use this template"** no repo `dgc-template-ts` (web/TS) ou `dgc-template-py` (Python). Detalhes em [`docs/REPOS.md`](docs/REPOS.md).

## Padrões de engenharia

- [Stack oficial](docs/STACK.md)
- [Qualidade de código](docs/QUALITY.md)
- [Estratégia de repositórios](docs/REPOS.md)
- [Convenções de Git](docs/CONVENTIONS.md)
- [Decisões de arquitetura (ADRs)](docs/decisions/)

## Operação e produto

- [Operating System da DGC](docs/DGC_OPERATING_SYSTEM.md)
- [Ofertas e precificação](docs/OFERTAS_E_PRECIFICACAO.md)
- [Playbook comercial](docs/PLAYBOOK_COMERCIAL.md)
- [Roadmap 30 dias](docs/ROADMAP_30_DIAS.md)
- [Estratégia de produtos e nichos](docs/ESTRATEGIA_PRODUTOS_E_NICHOS.md)
- [Produto Hermes — estratégia MVP](docs/PRODUTO_HERMES_ESTRATEGIA_MVP.md)
- [Checkpoint de retomada — 2026-06-19](docs/CHECKPOINT_RETOMADA_2026-06-19.md)

## Posicionamento inicial

A DGC Hub nasce como uma software house enxuta para transformar processos manuais de pequenos negócios em sistemas internos, automações e dashboards operacionais.

Oferta inicial validada:

> **DGC Sprint Operacional** — diagnóstico + entrega curta para resolver uma dor operacional específica com escopo fechado.

Produto próprio flagship:

> **Produto Hermes** — atendimento WhatsApp por IA, começando por demo dogfood e fluxo vertical antes de virar SaaS completo.

## Comandos de trabalho

```bash
cd ~/dgc-hub
```

Contexto histórico e decisões devem ser espelhados em:

```text
~/obsidian-vault/context/projetos/dgc-hub/
```

## Princípios

- Multi-repo puro: produto não mora no `core`.
- Escopo pequeno antes de sistema grande.
- Diagnóstico antes de proposta.
- Segurança antes de integração sensível.
- TDD/validação escopada na execução técnica.
- Manutenção não é desenvolvimento ilimitado.

---
_Repositório público. Não incluir credenciais, dados de clientes ou negociações internas._
