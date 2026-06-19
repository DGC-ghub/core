# Etapa 4 — Construção com IA (Claude Code / Codex)

**🎯 Objetivo:** gerar o código **tarefa por tarefa**, guiando a IA — sem ela sair fazendo coisa demais e virar uma bagunça que ninguém entende.

**✅ O que fazer:**
- Criar o repo a partir do template (botão **"Use this template"** no GitHub)
- Abrir o Claude Code / Codex **dentro da pasta do repo**
- Pegar a lista da Etapa 3 e pedir **UMA tarefa por vez**
- Depois de cada tarefa: **revisar → rodar os testes → commitar**, só então ir pra próxima
- Commits pequenos = ponto de save (dá pra voltar atrás fácil se quebrar)
- O `CLAUDE.md` do repo segura o padrão da casa (a IA lê e segue sozinha)

**🤖 Como pedir pra IA** (prompt por tarefa):
```
Implemente SÓ esta tarefa: [colar a tarefa].
Siga os padrões do CLAUDE.md deste repo.
Se algo não estiver claro, me pergunte ANTES de escrever código.
Escreva o teste, rode, e me explique em 2 linhas o que fez.
Não faça nada além desta tarefa.
```

**🔍 Como conferir que não saiu lixo:**
- A IA fez **só** a tarefa pedida (não inventou recurso a mais)?
- Tem **teste** e ele **passou**?
- Você **entende** o que ela fez? (se não, peça pra explicar antes de commitar)
- **Roda sem erro** e passou no lint/CI?
- O commit é **pequeno** e tem mensagem clara (Conventional Commits)?

**📄 Sai daqui:** código commitado no repo do produto, uma tarefa de cada vez → pronto pra **Revisão e Testes (Etapa 5)**.
