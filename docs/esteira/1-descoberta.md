# Etapa 1 — Descoberta

**🎯 Objetivo:** virar a ideia numa **regra de negócio clara** (o que faz, pra quem, regras).

**✅ O que fazer:**
- Responder 5 perguntas: que problema resolve? pra quem? o que a pessoa faz no sistema? quais as regras (ex: "pagou → libera")? o que **não** faz (escopo)?
- Listar os fluxos principais (ex: cadastrar → pagar → acessar)
- Listar os dados guardados (ex: usuário, assinatura, vídeo)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Você é analista de produto. A partir desta ideia: [colar ideia],
me faça as perguntas que faltam pra fechar a regra de negócio.
Depois escreva um doc curto com: problema, público,
funcionalidades, regras, fora de escopo, fluxos e dados.
```

**🔍 Como conferir que não saiu lixo:**
- Um leigo entende o produto só lendo o doc?
- Toda funcionalidade tem regra clara (sem "etc")?
- Tem o "fora de escopo" escrito? (senão o projeto vira infinito)

**📄 Sai daqui:** `docs/regra-de-negocio.md` no repo do produto.
