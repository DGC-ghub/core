# Qualidade de código — DGC Hub

| Aspecto | Padrão |
|---|---|
| Lint + format | **Biome** (config base em [`/configs/biome.json`](../configs/biome.json)) |
| Tipos | TypeScript `strict: true` (base em [`/configs/tsconfig.base.json`](../configs/tsconfig.base.json)) |
| Testes | Vitest (TS) / pytest (Python) — sem gate de cobertura por ora |
| Pre-commit | Husky + lint-staged: `biome` + `tsc` no que mudou |
| CI | `lint → typecheck → test → build` por PR |

## CI nos repos

Cada repo chama o reusable workflow do `core`:

```yaml
# .github/workflows/ci.yml no repo do projeto
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  ci:
    uses: DGC-ghub/core/.github/workflows/ci-node.yml@main
    with:
      node-version: "22"
```

## Pre-commit (Husky + lint-staged)

`package.json` do projeto:

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx,json}": ["biome check --write"],
    "*.{ts,tsx}": ["bash -c 'tsc --noEmit'"]
  }
}
```
