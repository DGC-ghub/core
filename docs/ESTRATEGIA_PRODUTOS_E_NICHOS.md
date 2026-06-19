# DGC Hub — Estratégia de Produtos e Nichos v0.1

Data: 2026-06-19
Status: proposta estratégica inicial, baseada na decisão de criar um cardápio próprio de soluções apresentáveis.

## 1. Decisão central

A DGC não deve começar procurando leads com uma oferta genérica de “fazemos sistemas”.

A melhor rota inicial é construir um pequeno portfólio próprio de produtos/demos funcionais, usando o template da DGC e dogfooding interno, para depois vender soluções derivadas desses produtos.

Estrutura atual no GitHub:

- `DGC-ghub/core` — manual, esteira, operação, docs e playbooks.
- `DGC-ghub/dgc-template-ts` — kit/template técnico reutilizável.
- `DGC-ghub/produto-hermes` — primeiro produto: atendimento WhatsApp por IA.

## 2. Tese de portfólio

A DGC deve ter 3 camadas:

```text
Produto próprio flagship
  -> Produto Hermes: atendimento WhatsApp por IA

Produtos/soluções derivadas
  -> CRM leve, dashboard operacional, agenda/orçamento/funil

Motor interno de aquisição
  -> conteúdo automático/assistido por IA para Instagram e prospecção
```

Não criar 10 produtos. Criar 1 produto principal, 1 a 2 soluções derivadas e 1 motor de aquisição.

## 3. Produto 1 — Produto Hermes

### O que é

SaaS de atendimento no WhatsApp por IA, com base de conhecimento por cliente, CRM leve e passagem configurável para humano.

### Por que faz sentido

- O WhatsApp é o canal real de venda/atendimento de pequenos negócios.
- Atendimento manual não escala.
- Negócio pequeno não tem equipe dedicada.
- A DGC pode usar internamente primeiro.
- O produto vira vitrine técnica e comercial.

### Risco principal

Escopo grande demais.

Se tentar começar com SaaS multi-cliente completo + CRM + inbox + campanhas + billing + painel perfeito, vira projeto grande demais antes de vender.

### Forma correta de começar

Começar como produto interno/dogfood + demo verticalizada, não como SaaS completo.

MVP real:

```text
WhatsApp oficial/sandbox ou canal simulado
  -> recebe mensagem
  -> identifica intenção
  -> consulta base de conhecimento do cliente
  -> responde com tom configurado
  -> registra conversa/lead
  -> sinaliza quando precisa humano
```

## 4. Nicho inicial recomendado

### Escolha recomendada: negócios de serviço com agendamento/orçamento via WhatsApp

Não começar com “todos os pequenos negócios”. Começar com uma categoria operacional parecida.

Nicho inicial sugerido:

> Prestadores de serviço locais que vendem por conversa e precisam qualificar/agendar/orçar via WhatsApp.

Exemplos:

- estética e beleza premium;
- clínicas/consultórios somente se não tratar dados médicos sensíveis no MVP;
- oficinas e assistência técnica;
- instalação/manutenção de ar-condicionado;
- energia solar e serviços residenciais;
- escolas/cursos livres;
- imobiliárias pequenas/corretores.

### Melhor primeiro subnicho para MVP

Recomendação inicial:

> Serviços com agendamento e orçamento, evitando dados sensíveis de saúde na primeira versão.

Exemplo prático para demo:

**Assistência técnica / serviço residencial**

Por quê:

- tem perguntas repetidas;
- precisa qualificar o problema;
- precisa coletar bairro, tipo de serviço, urgência, fotos/descrição;
- pode gerar orçamento/agendamento;
- menos LGPD sensível que clínica médica;
- fluxo é demonstrável.

Segundo subnicho possível:

**Estética/beleza premium**

Bom para venda e Instagram, mas exige cuidado com promessas e dados pessoais.

## 5. Cardápio inicial de soluções apresentáveis

### A. Hermes Atendimento IA

Produto principal.

Entregável demo:

- conversa no WhatsApp ou simulador;
- base de conhecimento editável;
- coleta de lead;
- resumo da conversa;
- status: resolvido / precisa humano;
- painel simples de leads.

Vende como:

- atendimento automático;
- pré-venda;
- qualificação;
- FAQ inteligente;
- agendamento/orçamento assistido.

### B. DGC CRM Lite

Produto derivado do Hermes, não produto separado no início.

Entregável demo:

- lista de contatos;
- histórico de conversa;
- tags;
- estágio do funil;
- observações;
- export CSV.

Vende como parte do Hermes Pro ou Sprint Operacional.

### C. DGC Dashboard Operacional

Solução secundária derivada do template.

Entregável demo:

- painel com indicadores simples;
- cadastros;
- filtros;
- exportação;
- visão semanal/mensal.

Serve para vender Sprint Operacional fora do WhatsApp.

### D. DGC Social Engine

Motor interno para postar conteúdo da DGC.

Não vender no começo.

Objetivo:

- gerar posts com IA;
- manter Instagram vivo;
- testar posicionamento;
- criar autoridade;
- atrair leads.

Regra importante:

> Começar com IA assistida e aprovação humana. Não publicar 100% automático sem revisão no início.

Motivo: risco de conteúdo ruim, promessa exagerada, erro comercial ou desalinhamento de marca.

## 6. Ordem correta de execução

### Fase 1 — Produto Hermes demo dogfood

Meta: provar que a DGC consegue atender seu próprio WhatsApp com IA.

Entregas:

- base de conhecimento da DGC;
- simulador ou integração WhatsApp sandbox;
- IA respondendo perguntas da DGC;
- captura de lead;
- handoff humano;
- painel simples.

### Fase 2 — Demo vertical

Meta: criar demo vendável para um nicho.

Escolher um fluxo:

- assistência técnica qualifica problema e agenda visita; ou
- estética qualifica interesse e agenda avaliação; ou
- curso livre responde dúvidas e capta matrícula.

### Fase 3 — Conteúdo e prospecção

Meta: usar o que foi construído como portfólio.

Entregas:

- posts mostrando dores reais;
- vídeos curtos da demo;
- carrosséis com antes/depois;
- CTA para diagnóstico.

### Fase 4 — Primeiro cliente piloto

Meta: vender ou implantar com desconto controlado.

Regras:

- escopo fechado;
- sem campanhas em massa;
- sem prometer autonomia total;
- cobrança mínima ou permuta com case bem documentado.

## 7. Modelo de cobrança para Produto Hermes

Não decidir preço final antes do MVP, mas usar hipótese inicial.

### Setup

- R$ 800 a R$ 3.000 para implantação, base de conhecimento e fluxo inicial.

### Mensalidade

- Lite: R$ 197 a R$ 397/mês
- Pro: R$ 497 a R$ 997/mês
- Custom: acima disso, com integrações e suporte.

### Custos variáveis

Separar custos de:

- WhatsApp API oficial;
- provedor de IA;
- hospedagem;
- mensagens/conversas.

Regra: custo variável nunca pode ficar invisível no preço.

## 8. Decisão sobre Instagram automático

A ideia é boa, mas precisa entrar como motor interno, não como distração.

Recomendação:

```text
Semana 1-2: gerar conteúdo com IA + aprovação manual
Semana 3-4: automatizar publicação com fila e revisão
Depois: publicar automático apenas formatos seguros
```

Formatos seguros iniciais:

- bastidores da construção;
- explicação de dores comuns;
- mini cases fictícios sinalizados como exemplo;
- demonstrações do Produto Hermes;
- checklists para pequenos negócios.

Evitar:

- promessas de ganho garantido;
- “IA substitui funcionário”;
- claims técnicos exagerados;
- conteúdo jurídico/LGPD sem validação.

## 9. Decisões tomadas

- Nome da oferta da software house pode ficar como **DGC Sprint Operacional**.
- O primeiro produto próprio será o **Produto Hermes**, focado em WhatsApp IA.
- Antes de buscar lista de leads, a DGC vai criar portfólio/demos funcionais.
- O GitHub já está dividido em `core`, `dgc-template-ts` e `produto-hermes`.

## 10. Próxima decisão pendente

Escolher o primeiro fluxo vertical da demo Hermes.

Recomendação técnica/comercial:

1. Primeira demo: assistência técnica/serviço residencial.
2. Segunda demo: estética/beleza premium.
3. Só depois: clínica/saúde, por causa de LGPD e sensibilidade dos dados.
