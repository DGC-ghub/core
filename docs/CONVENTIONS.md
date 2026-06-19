# Convenções — DGC Hub

Padrões compartilhados por todo o monorepo `core`.

## Branches

| Tipo      | Padrão              | Origem   |
|-----------|---------------------|----------|
| Principal | `main`              | —        |
| Feature   | `feature/<descricao>` | `main` |
| Correção  | `fix/<descricao>`   | `main`   |
| Hotfix    | `hotfix/<descricao>`| `main`   |

- `main` sempre estável.
- Descrição em `kebab-case` (ex: `feature/monitoramento-logs`).

## Commits

Formato [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<escopo>): <descrição curta no imperativo>
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
O escopo é a pasta afetada — ex: `feat(automations): adiciona monitor de logs`.

## Nomeação

- Pastas de sistemas/automações: `kebab-case`.
- Variáveis de ambiente: `UPPER_SNAKE_CASE`, documentadas em `.env.example`.
- Nada de segredos no repositório — apenas `.env.example` com valores fictícios.

## Pull Requests

- Um PR por mudança coesa; descreva o quê e o porquê.
- Referencie a issue quando houver.
