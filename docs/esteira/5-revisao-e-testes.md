# Etapa 5 — Revisão & Testes

**🎯 Objetivo:** garantir que **funciona e cumpre a regra de negócio** — não só que "parece pronto".

**✅ O que fazer:**
- Rodar **todos os testes**
- Passar **à mão** por cada fluxo da regra de negócio (Etapa 1) = usar o sistema como um usuário de verdade, clicando tudo (no celular também, se for app)
- Conferir os **segredos**: senha, token e chave de API vão em variável de ambiente (`.env`), **nunca** escritos no código
- Pedir uma **revisão crítica** pra IA (no Claude Code dá pra usar o `/review`)

**🤖 Como pedir pra IA** (prompt pronto pra colar):
```
Revise este código contra esta regra de negócio: [colar].
Aponte bugs, o que está faltando, o que NÃO tem teste e riscos de segurança.
Liste os problemas por gravidade: crítico, médio, baixo.
Seja crítico e direto — não me elogie, só liste problemas.
```

**🔍 Como conferir que não saiu lixo:**
- Todos os fluxos da regra de negócio funcionam **de ponta a ponta**?
- Os testes **passam** e os fluxos principais **têm teste**?
- Tudo que era **crítico** foi corrigido?
- Sem senha/segredo escrito no código (estão no `.env`)?
- Erros são tratados (não quebra feio na cara do usuário)?

**📄 Sai daqui:** `docs/checklist-revisao.md` marcado como OK → liberado pro **Deploy seguro (Etapa 6)**.
