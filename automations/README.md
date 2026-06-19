# automations

Scripts e automações da DGC Hub: CI/CD, monitoramento, deploys, ETL, tarefas
agendadas e integrações entre sistemas.

## Organização

Cada automação fica em sua própria subpasta:

```
automations/
└── <nome-da-automacao>/
    ├── README.md      # o que faz, como rodar, dependências
    └── ...            # código
```

## Padrão dos scripts

- Shebang + `--help` + `--dry-run`
- Flags nomeadas (não argumentos posicionais)
- Retry com backoff em chamadas de rede; timeout em operações externas
- Logging com timestamp e nível
- Exit codes significativos (0=ok, 1=erro, 2=uso)
- Idempotência (rodar 2x = mesmo resultado)
- Credenciais via variáveis de ambiente — **nunca** hardcoded
