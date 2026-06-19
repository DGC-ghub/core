# systems

Sistemas e produtos da DGC Hub. Cada sistema é independente e vive em sua
própria subpasta, com stack e ciclo de vida próprios.

## Organização

```
systems/
└── <nome-do-sistema>/
    ├── README.md      # visão geral, stack, como rodar
    ├── .env.example   # variáveis necessárias (sem valores reais)
    └── ...            # frontend/, backend/, etc.
```

## Ao criar um sistema novo

1. Crie a subpasta com nome em `kebab-case`.
2. Escreva o `README.md` (o que é, stack, como rodar localmente).
3. Adicione um `.env.example` quando houver configuração sensível.
4. Documente decisões de arquitetura em `docs/` quando relevantes ao grupo.
