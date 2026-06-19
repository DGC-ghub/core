# Etapa 1 — Descoberta

**🎯 Objetivo:** virar a ideia numa **regra de negócio clara** — um documento curto que diz, em português, o que o sistema faz, pra quem e quais as regras. É a base de todas as etapas seguintes.

**✅ O que fazer:**
- Responder **5 perguntas** (uma frase cada, sem "etc"):
  1. **Que problema resolve?** (a dor de quem vai usar)
  2. **Pra quem é?** (quem é a pessoa que usa)
  3. **O que ela faz no sistema?** (as ações principais)
  4. **Quais as regras?** (ex: "pagou → libera o acesso")
  5. **O que o sistema NÃO faz?** (o escopo — onde a v1 para)
- Listar os **fluxos principais** = o passo a passo do uso (ex: cadastrar → pagar → acessar)
- Listar os **dados guardados** = o que o sistema precisa lembrar (ex: usuário, assinatura, vídeo)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Você é analista de produto. Minha ideia é: [colar ideia em 2-3 linhas].

Primeiro, me faça as perguntas que faltam pra fechar a regra de negócio —
UMA pergunta por vez, e espere minha resposta antes da próxima.

Quando tiver o suficiente, escreva um doc curto, em linguagem simples
(o cliente é leigo), com estas seções:
problema · público · funcionalidades · regras · fora de escopo · fluxos · dados.
```

**🔍 Como conferir que não saiu lixo:**
- Um leigo entende o produto só lendo o doc? (sem você explicar nada)
- Toda funcionalidade tem **regra clara**? (nenhum "etc" ou "entre outros")
- Tem a seção **fora de escopo** escrita? (senão o projeto vira infinito)
- Os **fluxos** e os **dados** estão listados? (sem isso a próxima etapa trava)

**📄 Sai daqui:** `docs/regra-de-negocio.md` no repo do produto → vira a base da **Etapa 2 (Proposta)**.
