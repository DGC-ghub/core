# Checkpoint de Retomada — DGC Hub / Produto Hermes

Data: 2026-06-19
Status: parar por hoje e voltar exatamente deste ponto.

## Onde estamos

A DGC foi estruturada como operação + portfólio próprio antes de prospecção fria.

Repositórios GitHub atuais:

- `DGC-ghub/core` — manual, esteira, operação, docs e playbooks.
- `DGC-ghub/dgc-template-ts` — kit/template técnico reutilizável.
- `DGC-ghub/produto-hermes` — primeiro produto: WhatsApp IA.

Nome da oferta da software house validado por Gabriel:

- **DGC Sprint Operacional**.

## Decisão estratégica principal

Não montar lista de leads ainda.

Antes disso, a DGC precisa criar portfólio apresentável:

1. produto flagship funcional;
2. demo dogfood;
3. demo vertical por nicho;
4. conteúdo/Instagram mostrando a dor e a solução;
5. só depois abordagem de leads.

## Produto principal

**Produto Hermes** — SaaS de atendimento no WhatsApp por IA.

### Dor

Negócios pequenos atendem clientes manualmente no WhatsApp. Isso não escala, demora, perde venda e consome tempo.

### Resultado esperado

Atendimento automático e humanizado por IA no WhatsApp, com o mínimo de interação humana.

### Modelo

- SaaS para vender para vários clientes;
- uso interno da DGC como dogfooding;
- personalizável por cliente;
- agente de IA chamado “Hermes”.

## Prioridade funcional definida por Gabriel

Ordem de prioridade do produto:

```text
IA > CRM > caixa de entrada > campanhas
```

## Roadmap conceitual do Produto Hermes

### Fase 0 — Base / encanamento

Conectar WhatsApp, receber e enviar mensagens.

Observação importante: para produto pago, usar API oficial da Meta/provedor confiável. Atalho não oficial tem risco de ban e não serve como base comercial.

### Fase 1 — Núcleo Hermes IA

IA atendendo via base de conhecimento por cliente, estilo RAG:

- achar tópico;
- buscar resposta;
- responder;
- tirar dúvidas;
- qualificar venda/agendamento;
- chamar humano quando necessário.

### Fase 2 — CRM

- cadastro de clientes;
- histórico;
- etiquetas;
- funil.

### Fase 3 — Caixa de entrada da equipe

Painel para atendente humano assumir quando precisar.

### Fase 4 — Campanhas/disparos

Fora de escopo do v1. Entra no roadmap depois.

## Regra de negócio inicial

- Cada cliente tem sua própria base de conhecimento.
- A IA resolve o que estiver na base.
- Se não souber, pergunta mais ou chama humano.
- Passagem para humano deve ser mínima, mas não zero.
- Handoff deve ser configurável por cliente.
- A IA não deve inventar preço, prazo, garantia, política ou promessa.

## Escopo recomendado para MVP

Não começar como SaaS completo.

Começar como:

> Demo dogfood + fluxo vertical funcional + arquitetura preparada para virar SaaS.

### MVP inclui

- modo simulado antes da API WhatsApp oficial;
- base de conhecimento da própria DGC;
- RAG simples;
- resposta com guardrails;
- salvar conversa/lead;
- status de handoff humano;
- painel mínimo.

### MVP não inclui

- campanhas;
- billing;
- multi-tenant completo;
- CRM avançado;
- inbox completa;
- app mobile;
- analytics complexo;
- integração profunda com ERP;
- promessa de atendimento 100% autônomo.

## Nicho inicial recomendado

Não começar com “todos que usam WhatsApp”.

Começar com:

> Serviços locais com agendamento/orçamento via WhatsApp.

Primeira demo recomendada:

> Assistência técnica / serviço residencial.

Motivos:

- perguntas repetidas;
- fluxo claro de qualificação;
- coleta bairro, urgência, tipo de problema, descrição/foto;
- pode gerar orçamento/agendamento;
- menor risco LGPD que saúde/clínica;
- fácil de demonstrar em vídeo.

Segundo nicho possível:

- estética/beleza premium.

Saúde/clínicas: deixar para depois por LGPD e sensibilidade de dados.

## Fluxo da primeira demo vertical

```text
Cliente chama no WhatsApp
  -> IA cumprimenta
  -> identifica o problema
  -> coleta bairro
  -> coleta urgência
  -> coleta tipo de equipamento/serviço
  -> responde dúvidas básicas
  -> propõe orçamento/agendamento
  -> salva lead
  -> chama humano se fugir da base
```

## Instagram / conteúdo com IA

A ideia é boa, mas deve entrar como motor interno, não distração.

Ordem recomendada:

```text
Fase 1: IA gera posts + Gabriel/Danilo aprovam manualmente
Fase 2: fila de posts com aprovação
Fase 3: publicação automática só para formatos seguros
```

Formatos seguros iniciais:

- bastidores da construção;
- dores comuns de atendimento manual;
- mini demos do Produto Hermes;
- carrosséis antes/depois;
- checklists para pequenos negócios.

Evitar:

- prometer aumento garantido de venda;
- dizer que IA substitui funcionário;
- claims jurídicos/LGPD sem validação;
- conteúdo agressivo estilo guru.

## Próximo passo exato

Quando retomar, não voltar para brainstorming amplo.

Próxima ação recomendada:

> Abrir ou clonar o repo `DGC-ghub/produto-hermes` localmente e criar o plano técnico do MVP simulado.

Plano técnico a criar no `produto-hermes`:

```text
Etapa 0: simulador de conversa
Etapa 1: base de conhecimento da DGC
Etapa 2: RAG simples
Etapa 3: resposta com guardrails
Etapa 4: salvar lead/conversa
Etapa 5: painel mínimo
Etapa 6: demo vertical assistência técnica
Etapa 7: preparação para WhatsApp oficial
```

## Arquivos relevantes no core

- `docs/DGC_OPERATING_SYSTEM.md`
- `docs/OFERTAS_E_PRECIFICACAO.md`
- `docs/PLAYBOOK_COMERCIAL.md`
- `docs/ROADMAP_30_DIAS.md`
- `docs/ESTRATEGIA_PRODUTOS_E_NICHOS.md`
- `docs/PRODUTO_HERMES_ESTRATEGIA_MVP.md`
- `docs/CHECKPOINT_RETOMADA_2026-06-19.md`

## Frase de retomada sugerida

Se Gabriel voltar em outra sessão, pode dizer:

> Hermes, retoma o DGC pelo checkpoint de 2026-06-19 e vamos criar o plano técnico do Produto Hermes no repo produto-hermes.
