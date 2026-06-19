# Etapa 6 — Deploy seguro

**🎯 Objetivo:** subir a aplicação **sem expor segredo** nem derrubar o que já está no ar.

**✅ O que fazer:**
- Pôr segredos em **variáveis de ambiente** (`.env`) e garantir que o `.env` está no **`.gitignore`** (não vai pro GitHub)
- Confirmar que o **CI/build está verde** antes de subir
- Subir primeiro num ambiente de **teste (staging)** = uma cópia igual à de produção, mas que só vocês usam — e conferir lá
- Só então subir pra **produção** (o que o cliente/usuário acessa)
- Garantir o **rollback** = um jeito rápido de voltar pra versão anterior se quebrar

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Me guie no deploy seguro deste app na [plataforma, ex: Vercel/Railway].
Liste o passo a passo, o que checar ANTES de ir pra produção
(incluindo confirmar que o .env NÃO foi pro Git) e como reverter
se der errado. Explique pra iniciante.
```

**🔍 Como conferir que não saiu lixo:**
- Os segredos estão fora do código e o `.env` **não foi pro repositório**?
- O **CI/build passou** (verde)?
- Testei em **staging** antes da produção?
- Sei como **reverter** se quebrar?
- **Domínio e HTTPS** (cadeado) funcionando?

**📄 Sai daqui:** `docs/deploy.md` no repo do produto → app no ar, pronto pro **Monitoramento (Etapa 7)**.
