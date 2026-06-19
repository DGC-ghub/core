# Produto Hermes — Estratégia MVP v0.1

Data: 2026-06-19
Status: estratégia inicial para transformar o briefing do WhatsApp IA em produto/demonstração vendável.

## 1. Princípio

Produto Hermes não deve começar como SaaS completo. Deve começar como:

> Demo dogfood + fluxo vertical funcional + arquitetura preparada para virar SaaS.

Isso reduz risco, gera portfólio e permite vender antes de construir demais.

## 2. Escopo do MVP

### Inclui

- base de conhecimento por cliente;
- chat via WhatsApp oficial/sandbox ou simulador inicial;
- IA respondendo com RAG simples;
- coleta de lead;
- resumo da conversa;
- status de handoff humano;
- painel mínimo de conversas/leads.

### Não inclui no MVP

- campanhas/disparos em massa;
- billing/assinatura;
- multi-tenant completo;
- app mobile;
- CRM avançado;
- analytics complexo;
- integrações profundas com ERP;
- promessa de atendimento 100% autônomo.

## 3. Ordem de construção recomendada

### Etapa 0 — Modo simulado

Antes de depender da Meta/WhatsApp oficial:

- criar uma tela ou CLI que simula mensagens recebidas;
- usar uma base de conhecimento local;
- testar RAG/resposta/handoff;
- salvar conversas no banco.

Critério de pronto:

- Gabriel consegue simular 20 perguntas e ver respostas coerentes.

### Etapa 1 — Dogfood DGC

Base de conhecimento da própria DGC:

- o que é a DGC;
- serviços;
- preços iniciais;
- como funciona diagnóstico;
- como pedir proposta;
- perguntas frequentes;
- red flags e quando chamar humano.

Critério de pronto:

- o Hermes atende um lead fictício da DGC sem inventar promessa.

### Etapa 2 — Demo vertical

Criar uma base de conhecimento fictícia para um nicho escolhido.

Recomendação inicial:

- assistência técnica/serviço residencial.

Fluxo exemplo:

```text
Cliente chama no WhatsApp
  -> IA cumprimenta
  -> identifica tipo de problema
  -> coleta bairro, urgência, aparelho/serviço, descrição
  -> responde dúvidas básicas
  -> propõe agendamento/orçamento
  -> salva lead
  -> se não souber, marca para humano
```

Critério de pronto:

- demo pode ser gravada em vídeo curto e mostrada para prospect.

### Etapa 3 — WhatsApp oficial

Só depois do modo simulado e dogfood:

- validar custo da API oficial;
- validar aprovação Meta;
- escolher provedor;
- implementar webhook;
- testar recebimento/envio real.

Critério de pronto:

- mensagem real entra e sai via canal oficial, sem gambiarra que gere ban.

### Etapa 4 — SaaS mínimo

Depois de primeiro piloto:

- separar clientes/tenants;
- painel de configuração da base;
- planos e limites;
- cobrança;
- logs/auditoria;
- termos/LGPD.

## 4. Arquitetura conceitual

```text
WhatsApp/API ou Simulador
  -> Webhook/Message Ingest
  -> Conversation Store
  -> Intent Router
  -> Knowledge Retrieval
  -> AI Response Composer
  -> Safety/Handoff Rules
  -> Message Out
  -> CRM Lead Record
```

## 5. Modelo de base de conhecimento

Cada cliente deve ter uma pasta/base própria.

Exemplo:

```text
knowledge/{cliente}/
  perfil_do_negocio.md
  faq.md
  precos_servicos.md
  horarios_e_localizacao.md
  politica_agendamento.md
  tom_de_voz.md
  handoff.md
```

Regra:

- a IA responde o que está na base;
- se a resposta não estiver clara, pergunta mais ou chama humano;
- não inventa preço, prazo, garantia ou política.

## 6. Handoff humano

Casos para humano:

- cliente pede humano;
- IA não encontrou resposta;
- cliente está irritado;
- pedido envolve negociação fora da política;
- dados sensíveis;
- reclamação;
- cancelamento;
- pergunta jurídica/financeira sensível.

## 7. Métricas do MVP

Medir desde cedo:

- total de conversas;
- % respondida sem humano;
- % enviada para humano;
- perguntas sem resposta;
- leads qualificados;
- tempo médio de resposta;
- satisfação manual/anotada.

## 8. Riscos

### WhatsApp

API oficial pode ter custo, aprovação e template policy.

Mitigação:
- começar com simulador;
- depois sandbox/oficial;
- nunca usar atalho não-oficial em produto pago.

### IA inventando

Mitigação:
- base de conhecimento pequena e revisada;
- resposta conservadora;
- fallback para humano;
- logs de perguntas sem resposta.

### LGPD

Mitigação:
- evitar saúde/dados sensíveis no primeiro piloto;
- coletar mínimo necessário;
- documentar retenção;
- não expor conversas sem permissão.

### Escopo

Mitigação:
- CRM e inbox ficam mínimos;
- campanhas fora do v1;
- multi-tenant só depois de piloto.

## 9. Próximo passo técnico

Criar um plano de implementação no repo `produto-hermes` com esta ordem:

1. estruturar app pelo `dgc-template-ts`;
2. criar modelo de `knowledge base`;
3. criar simulador de conversa;
4. criar retrieval simples;
5. criar resposta IA com guardrails;
6. salvar conversas/leads;
7. criar painel mínimo;
8. preparar integração WhatsApp oficial.

## 10. Próximo passo comercial

Antes de leads frios, criar material de portfólio:

- vídeo demo de 1 minuto;
- carrossel “como um atendimento por IA qualifica cliente no WhatsApp”;
- landing simples com CTA para diagnóstico;
- roteiro de abordagem para 10 conversas quentes.
