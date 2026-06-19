# DGC Hub — `core`

Repositório central da software house **DGC Hub**. Reúne automações, sistemas e
documentação compartilhada num único monorepo.

## Estrutura

```
core/
├── automations/   # Scripts e automações (CI/CD, monitoramento, deploys, ETL)
├── systems/       # Sistemas e produtos (cada um em sua subpasta)
├── docs/          # Documentação técnica, de arquitetura e de processo
├── .editorconfig  # Padrão de formatação entre editores
└── .gitignore     # Ignora artefatos, segredos e dependências
```

Cada item dentro de `automations/` e `systems/` vive em sua própria subpasta,
com README e dependências próprias (o monorepo não impõe uma stack única).

## Como começar

```bash
git clone git@github.com:DGC-ghub/core.git
cd core
```

Depois entre na subpasta do sistema/automação em que vai trabalhar e siga o
README local.

## Convenções

Padrões de branch, commit e nomeação em [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Roadmap de automações

- [ ] Pipeline de CI/CD (GitHub Actions)
- [ ] Monitoramento de logs
- [ ] Deploy automático

---
_Repositório privado — uso interno da DGC Hub._
