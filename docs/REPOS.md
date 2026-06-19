# Estratégia de repositórios — DGC Hub

A DGC Hub usa **multi-repo puro**: cada sistema, produto ou automação em seu
próprio repositório. O `core` guarda só padrões, configs e CI.

## Convenção de nomes

| Tipo | Padrão | Exemplo |
|---|---|---|
| Template | `dgc-template-*` | `dgc-template-ts` |
| Interno / automação | `dgc-<nome>` | `dgc-ci-bot` |
| Produto de cliente | `<cliente>-<produto>` | `ipeconect-painel` |

## Criar um projeto novo

1. Vá ao template (`dgc-template-ts` para web/TS, `dgc-template-py` para Python).
2. Clique em **"Use this template" → Create a new repository**.
3. Nomeie conforme a convenção acima.
4. Em **Settings → Branches**, proteja a `main`: exija o check de CI verde.
5. Clone, `npm install` (ou `uv sync`) e comece. O CI já está ligado ao `core`.

## Branch protection (padrão)

- `main` protegida; merge exige **CI verde**.
- Review de PR **recomendado** (um dev revisa o outro), não-bloqueante por ora.
