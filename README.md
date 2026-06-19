# DGC Hub — `core`

Playbook de engenharia da software house **DGC Hub**. Este repositório **não**
hospeda código de produto — a DGC Hub usa **multi-repo puro**, cada sistema em
seu próprio repositório. Aqui ficam apenas os padrões, configs base e o CI
compartilhado.

## Conteúdo

```
core/
├── docs/
│   ├── STACK.md         # stack oficial + versões
│   ├── QUALITY.md       # Biome, TS strict, Vitest, pre-commit, CI
│   ├── REPOS.md         # multi-repo: naming e como criar projeto novo
│   ├── CONVENTIONS.md   # branches, commits, nomeação, PR
│   └── decisions/       # ADRs — registro de decisões
├── configs/             # biome.json e tsconfig.base.json base p/ herdar
└── .github/workflows/   # ci-node.yml — reusable workflow dos repos
```

## Começar um projeto novo

Use **"Use this template"** no repo `dgc-template-ts` (web/TS) ou `dgc-template-py`
(Python). Detalhes em [`docs/REPOS.md`](docs/REPOS.md).

## Padrões

- [Stack oficial](docs/STACK.md)
- [Qualidade de código](docs/QUALITY.md)
- [Estratégia de repositórios](docs/REPOS.md)
- [Convenções de Git](docs/CONVENTIONS.md)
- [Decisões de arquitetura (ADRs)](docs/decisions/)

---
_Repositório privado — uso interno da DGC Hub._
