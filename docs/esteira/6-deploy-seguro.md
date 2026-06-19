# Etapa 6 — Deploy seguro

**🎯 Objetivo:** subir a aplicação **sem expor segredo** nem derrubar o que já está no ar.

**✅ O que fazer:**
- Pôr segredos em **variáveis de ambiente** (`.env`) — nunca no código
- Subir primeiro num ambiente de **teste (staging)** e conferir
- Só então subir pra **produção**
- Garantir um jeito de **voltar atrás** (rollback)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Me guie no deploy seguro deste app na [plataforma, ex: Vercel/Railway].
Liste o passo a passo, o que checar ANTES de ir pra produção,
e como reverter se der errado. Explique pra iniciante.
```

**🔍 Como conferir que não saiu lixo:**
- Os segredos estão fora do código (em variáveis de ambiente)?
- Testei em staging antes da produção?
- Sei como reverter se quebrar?
- Domínio e HTTPS (cadeado) funcionando?

**📄 Sai daqui:** `docs/deploy.md` no repo do produto.
