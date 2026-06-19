# Etapa 5 — Revisão & Testes

**🎯 Objetivo:** garantir que **funciona e cumpre a regra de negócio** — não só que "parece pronto".

**✅ O que fazer:**
- Rodar todos os testes
- Passar **à mão** por cada fluxo da regra de negócio (Etapa 1)
- Checar segurança básica: nada de senha/segredo no código
- Pedir uma revisão crítica pra IA

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Revise este código contra esta regra de negócio: [colar].
Aponte bugs, o que está faltando e riscos de segurança.
Seja crítico e direto — não me elogie, só liste problemas.
```

**🔍 Como conferir que não saiu lixo:**
- Todos os fluxos da regra de negócio funcionam de ponta a ponta?
- Os testes passam?
- Sem senha/segredo escrito no código?
- Erros são tratados (não quebra feio na cara do usuário)?

**📄 Sai daqui:** `docs/checklist-revisao.md` marcado como OK.
