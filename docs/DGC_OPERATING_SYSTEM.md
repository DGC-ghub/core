# DGC Hub — Operating System v0.1

Status: proposta operacional inicial para validação de Gabriel e Danilo.
Data: 2026-06-19

## 1. O que é a DGC Hub

A DGC Hub é uma software house enxuta focada em transformar gargalos operacionais de pequenos e médios negócios em sistemas simples, automações úteis e painéis de gestão.

A DGC não deve nascer como “fábrica de qualquer software”. O posicionamento inicial deve ser:

> Sistemas internos, automações WhatsApp/API e dashboards operacionais para empresas que ainda dependem de planilhas, retrabalho manual e processos sem rastreabilidade.

## 2. O que a DGC vende primeiro

### Oferta principal inicial — Pacote Operação Inteligente

Produto/serviço vendável inicial:

> Diagnóstico + automação/sistema enxuto para resolver um processo operacional específico em até 2 a 4 semanas.

Exemplos de problemas aceitos:

- controle de estoque básico;
- cadastro/consulta de clientes;
- funil de atendimento;
- automação de mensagens WhatsApp;
- geração de relatórios internos;
- painel simples de indicadores;
- fluxo de aprovação interno;
- integração read-only com planilha, ERP ou API;
- portal interno simples para equipe.

### Subofertas

1. **Automação WhatsApp/API**
   - lembretes;
   - confirmação de atendimento/pedido;
   - coleta de dados;
   - status de processo;
   - atendimento semi-automatizado com humano no loop.

2. **Sistema Interno Sob Medida**
   - CRUD operacional;
   - dashboard;
   - permissões simples;
   - exportação CSV/PDF;
   - logs básicos.

3. **Dashboard de Gestão**
   - leitura de dados existentes;
   - indicadores por período;
   - tela executiva para dono/gestor;
   - sem promessa de BI complexo no início.

4. **MVP SaaS para Nicho**
   - transformar uma dor repetida de cliente em produto reaproveitável;
   - só vira SaaS depois de 2 ou 3 entregas parecidas.

## 3. Público-alvo inicial

### ICP primário

Pequenas empresas locais ou regionais com operação já rodando, mas gestão frágil:

- prestadores de serviço;
- clínicas pequenas;
- oficinas;
- lojas e distribuidoras;
- negócios com estoque;
- empresas com atendimento recorrente via WhatsApp;
- empresas que usam planilhas como sistema principal.

### Quem tem maior chance de comprar

- dono sente a dor diretamente;
- equipe perde tempo todo dia com tarefa repetitiva;
- existe dinheiro vazando por falta de controle;
- processo atual cabe em uma planilha ou WhatsApp;
- decisão depende do dono, não de comitê grande;
- ticket de R$ 1.500 a R$ 8.000 é possível.

### Quem recusar no início

- projeto muito grande sem escopo claro;
- marketplace completo;
- app mobile nativo complexo;
- integração bancária/escrita financeira sensível sem contrato forte;
- sistema médico com prontuário/dados sensíveis sem compliance;
- cliente que pede “igual iFood/Uber/ERP completo” com orçamento baixo;
- qualquer projeto que dependa de promessas vagas de equity.

## 4. Primeiro produto vendável

### Nome provisório

**DGC Sprint Operacional**

### Promessa

> Em até 10 dias úteis, mapear um processo manual e entregar uma primeira versão funcional: tela, automação ou dashboard que reduza retrabalho real.

### Entregáveis

- reunião de diagnóstico;
- mapa simples do processo atual;
- escopo fechado de uma dor;
- protótipo funcional web ou automação;
- documentação curta de uso;
- 7 dias de ajustes leves pós-entrega.

### Escopo máximo da primeira venda

- 1 processo;
- 1 perfil de usuário principal;
- 3 a 5 telas no máximo, ou 1 fluxo de automação;
- banco simples;
- deploy simples;
- sem app mobile nativo;
- sem arquitetura enterprise;
- sem refatorar processo inteiro da empresa.

## 5. Precificação inicial

A DGC deve começar simples, com preço por pacote fechado, não por hora.

### Pacote 1 — Diagnóstico Pago

Preço sugerido: R$ 300 a R$ 700

Inclui:
- reunião de 60 a 90 minutos;
- levantamento da dor;
- documento com proposta técnica;
- estimativa de prazo e valor.

Objetivo: filtrar curioso e cliente sem urgência.

### Pacote 2 — Sprint Operacional Lite

Preço sugerido: R$ 1.500 a R$ 3.000

Inclui:
- automação simples ou dashboard básico;
- 1 fluxo principal;
- entrega em 5 a 10 dias úteis;
- suporte de ajuste leve por 7 dias.

### Pacote 3 — Sprint Operacional Pro

Preço sugerido: R$ 3.500 a R$ 8.000

Inclui:
- sistema interno pequeno;
- autenticação simples se necessário;
- CRUD + dashboard + exportação;
- integração read-only simples;
- entrega em 2 a 4 semanas.

### Recorrência opcional

Manutenção/suporte: R$ 300 a R$ 1.500/mês, conforme:
- hospedagem;
- monitoramento;
- pequenas melhorias;
- correções;
- backup;
- suporte operacional.

Regra: nunca vender manutenção ilimitada.

## 6. MVP interno da DGC

Antes de criar produto SaaS, a DGC precisa de um sistema operacional interno mínimo.

### MVP interno v1

Criar dentro do repo `~/dgc-hub`:

```text
docs/
  DGC_OPERATING_SYSTEM.md
  OFERTAS_E_PRECIFICACAO.md
  PLAYBOOK_COMERCIAL.md
  ROADMAP_30_DIAS.md
  templates/
    diagnostico_cliente.md
    proposta_sprint_operacional.md
    briefing_projeto.md
    checklist_entrega.md

automations/
  README.md

systems/
  README.md
```

### O que esse MVP resolve

- Gabriel/Danilo sabem o que vender;
- Hermes sabe como transformar conversa em proposta;
- cada lead vira um diagnóstico estruturado;
- cada projeto começa com escopo pequeno;
- decisões ficam registradas no Obsidian;
- evita aceitar projeto bucha.

## 7. Stack padrão inicial

A stack deve priorizar velocidade, baixo custo e manutenção simples.

### Frontend

- React + Vite;
- Tailwind CSS;
- shadcn/ui quando fizer sentido;
- dashboards simples, sem overengineering.

### Backend

- Node.js + Express ou Fastify para sistemas web simples;
- Python/FastAPI quando o projeto tiver automação, scraping, dados ou IA;
- SQLite para MVP/local/sistema pequeno;
- PostgreSQL quando precisar multiusuário sério ou produção mais robusta.

### Automações

- Python para scripts e integrações;
- filas simples só quando necessário;
- cron/systemd para rotinas no Pi/VPS;
- logs em arquivo + painel básico.

### Deploy

- VPS simples ou Raspberry Pi quando fizer sentido;
- Docker só quando simplificar, não por moda;
- GitHub Actions apenas depois de primeiro deploy manual entendido;
- backup documentado desde o início.

### Integrações

- WhatsApp: começar com provedores/API estáveis; evitar gambiarra frágil em projeto pago.
- ERPs/financeiro: read-only primeiro; escrita só com contrato, logs e rollback.

## 8. Templates reaproveitáveis prioritários

1. Template de diagnóstico de cliente.
2. Template de proposta comercial.
3. Template de briefing técnico.
4. Checklist de aceite/entrega.
5. Base React dashboard.
6. Base backend CRUD + auth simples.
7. Base automação WhatsApp com logs.
8. Template de contrato/termos — precisa validação jurídica externa.

## 9. Workflow operacional

```text
Lead
  -> Diagnóstico pago ou triagem gratuita curta
  -> Documento de dor/processo
  -> Proposta fechada com escopo pequeno
  -> Sinal de entrada
  -> Plano técnico markdown
  -> Execução TDD/validação escopada
  -> Demonstração
  -> Ajustes leves
  -> Entrega + aceite
  -> Manutenção opcional
```

## 10. Regra de ouro

A DGC deve vender clareza operacional, não “software bonito”.

Toda entrega precisa responder:

1. Qual retrabalho isso reduz?
2. Qual erro isso evita?
3. Qual número/processo isso deixa visível?
4. Quem usa isso amanhã?
5. Como sabemos que funcionou?

Se não responder essas perguntas, o projeto ainda não está pronto para venda.

## 11. Decisões abertas

Estas decisões ainda precisam de validação humana:

- Nome comercial final dos pacotes.
- Faixas de preço finais.
- Se o diagnóstico será sempre pago ou pode ser gratuito no início.
- Quem será o primeiro nicho atacado.
- Se o primeiro case será Gestão/Estoque, WhatsApp ou Dashboard.
- Divisão operacional Gabriel/Danilo: comercial, técnico, atendimento, entrega.
