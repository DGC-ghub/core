# Etapa 3 — Planejamento técnico

**🎯 Objetivo:** decidir **o que construir e em que ordem**, usando a stack do playbook. Aqui ainda **não tem código** — é a planta da obra antes de levantar parede.

**✅ O que fazer:**
- Listar as **telas** do produto (cada coisa que o usuário vê)
- Modelar os **dados** = quais "fichas" o sistema guarda e o que tem em cada uma (ex: usuário → nome, e-mail, plano)
- Listar **integrações** = serviços de fora que a gente usa (pagamento, e-mail, login…)
- Quebrar em **tarefas pequenas** — cada uma cabe numa sessão de IA e dá pra dizer quando está pronta
- Escolher o template: `dgc-template-ts` (web/app) ou `dgc-template-py` (IA/scraping/dados)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Você é arquiteto de software. Use:
- regra de negócio: [colar]
- fases da proposta: [colar] (planeje só a Fase 1 por enquanto)
- nossa stack oficial: [colar o conteúdo de core/docs/STACK.md]

Proponha: lista de telas, modelo de dados, integrações
e uma lista de tarefas pequenas, ORDENADAS por dependência
(o que precisa existir antes do quê). Ainda SEM código.
Não use nenhuma tecnologia fora da stack acima.
```

**🔍 Como conferir que não saiu lixo:**
- Cada tarefa **cabe numa sessão** (não é "construir o app inteiro")?
- As tarefas estão **na ordem certa** (nada depende de algo que vem depois)?
- O modelo de dados cobre **todas as regras** da Etapa 1?
- Nada de tecnologia **fora do `STACK.md`**?

**📄 Sai daqui:** `docs/plano.md` no repo do produto → o roteiro que a gente segue na **Construção com IA (Etapa 4)**.
