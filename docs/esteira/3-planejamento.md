# Etapa 3 — Planejamento técnico

**🎯 Objetivo:** decidir **o que construir e em que ordem** — usando a stack do playbook.

**✅ O que fazer:**
- Listar as **telas** do produto
- Modelar os **dados** (o que o sistema guarda)
- Listar **integrações** (pagamento, e-mail, login…)
- Quebrar em **tarefas pequenas** (cada uma cabe numa sessão de IA)
- Escolher o template (`dgc-template-*`)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Você é arquiteto de software. Com base nesta regra de negócio: [colar]
e na nossa stack oficial (core/docs/STACK.md),
proponha: lista de telas, modelo de dados, integrações
e uma lista de tarefas pequenas e ordenadas. Ainda SEM código.
```

**🔍 Como conferir que não saiu lixo:**
- Cada tarefa cabe numa sessão (não é gigante)?
- O modelo de dados cobre todas as regras de negócio?
- Nada de tecnologia fora do nosso `STACK.md`?

**📄 Sai daqui:** `docs/plano.md` no repo do produto.
