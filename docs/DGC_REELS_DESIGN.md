# DGC Reels — motor de conteúdo do retorno da DGC

Data: 2026-10-10
Status: design aprovado em conversa (Gabriel), aguardando revisão da spec escrita.
Executor: Hermes Agent (orquestrador) + workers Claude via `dev` (DGC Dev Hub).

## 1. Objetivo

Reativar a DGC mostrando do que ela é capaz: um estoque de **~39 Reels** (3 meses × 3 posts/semana)
produzido e aprovado **antes** do primeiro post. Cada Reel conta uma história "problema → como
construímos → resultado" com narração natural, animação e foco no empresário de Goiás/Goiânia.

Sprint inicial: **sex 10/10 → seg 13/10**, Hermes trabalhando 24h. Depois, modo cron noturno até
completar o estoque.

### Critério de sucesso para segunda 13/10

- Identidade visual DGC aprovada (logo, paleta, fonte, bio).
- Template DGC + vídeo piloto aprovados.
- Cardápio de 39 ideias aprovado.
- **≥ 12 vídeos com aprovação final** (4 semanas de estoque).
- Zero dado sensível de terceiro em qualquer render.
- Loop rodando em modo cron, com watchdog e relatório diário.

Fora deste sprint: publicar no Instagram (o estoque é guardado; publicação entra numa fase
posterior), portar a arquitetura do atendimento do Gestão 360 para o produto Hermes (subprojeto 2).

## 2. Decisões tomadas

| Decisão | Escolha |
|---|---|
| Liberação de uso do Gestão 360 | DGC é empresa do Grupo Ipeconect: cases podem citar a Ipeconect. Clientes do BPO (Start, JASC, SNF…), telefones, CNPJs e valores reais **nunca** aparecem. |
| Formato do loop | Cron + aprovação pelo Telegram. Nada vai ao ar sem ok do Gabriel. |
| Prioridade | Instagram primeiro. |
| Identidade | Não existe: o loop propõe 3 opções; o perfil do Instagram o Gabriel cria manualmente. |
| Cadência | Estoque de 3 meses antes de lançar, depois 3 posts/semana. |
| Aprovador | Gabriel (sozinho, por enquanto). |
| Estrutura | Repo novo `DGC-ghub/dgc-reels` em `~/projects/dgc-reels`, fork do pipeline da campanha HUB. |
| Merge de PR | Automático **somente no dgc-reels**: review do `claude-20b` APROVADO + CI verde → Hermes faz merge e avisa. Dois pedidos de mudança seguidos no mesmo PR → para e chama o Gabriel. Demais repos seguem exigindo ok explícito. |

## 3. O Método DGC de vídeo

Todo Reel tem 45–60 s, 9:16, 1080×1920, 30 fps, legenda queimada palavra a palavra.

| Ato | Tempo | Conteúdo |
|---|---|---|
| 1. Gancho | 0–3 s | A dor numa frase que o empresário goiano reconhece. Texto grande + voz. |
| 2. Problema | 3–15 s | Ilustração/animação do "como era": caos, retrabalho, dinheiro escapando. |
| 3. Construção | 15–35 s | Bastidor profissional: entendemos o processo → desenhamos → construímos → entregamos. Selo "Método DGC" (esteira de 8 etapas do `core`). Telas do sistema recriadas em React. |
| 4. Resultado | 35–45 s | Antes × depois. Número só quando for case real e verificável. |
| 5. Fecho | 45–55 s | *"Você imagina uma solução assim na sua empresa? De organizar pastas a um sistema financeiro ou um atendente com IA. Chama a DGC."* + CTA. |

### Séries (composição do lote 1 — 39 vídeos)

| Série | Qtde | Conteúdo | Regra |
|---|---|---|---|
| A. Cases reais (Ipeconect) | 8 | Tesouraria (32 telas → 1), Controladoria (BI pago com receita errada), Cobrança automática, Atendimento centralizado, RH (saída da Sólides), TI & inventário, Marketing com revisão, Fingestão. | Fonte: docs do `gestao-360`. Números só os documentados. Cliente do BPO vira "uma empresa do grupo". |
| B. "E se fosse na sua empresa?" | 15 | Goiás: pecuária (rebanho, pesagem, vacinação), confecção da Região da 44, clínica, construtora, distribuidora, escritório contábil, autopeças, etc. | **Sempre** com selo visível "Exemplo ilustrativo". Nunca apresentar como cliente real. |
| C. Pequenas automações | 8 | Organizar pastas, planilha → sistema, relatório que chega sozinho. | Ticket baixo, porta de entrada. |
| D. Bastidores / quem é a DGC | 4 | Quem somos, o método, como uma ideia vira sistema. | — |
| E. Hermes | 4 | Atendente com IA no WhatsApp. | Por último na fila; só demonstra o que funciona de fato. |

### Restrições duras (violar invalida o vídeo)

1. Nenhum dado real de terceiro (nome de cliente do BPO, telefone, CNPJ, valor financeiro, IP, login).
2. Nenhum caso fictício apresentado como real; série B sempre com selo.
3. Nenhuma promessa de ganho garantido, nem "IA substitui funcionário".
4. Nenhum preço ou prazo de entrega.
5. Nenhum claim técnico exagerado sobre o Hermes (só o que roda hoje).
6. Trilha somente royalty-free com licença registrada em `trilhas/LICENCAS.md`.

## 4. Ferramentas

O Remotion é o motor de montagem; as demais são peças que entram nele.

| Peça | Ferramenta | Observação |
|---|---|---|
| Montagem/render | Remotion 4.0.534 (mesma versão da campanha) | `concurrency` 1–2 no Pi 4 (3,7 GB RAM). Licença gratuita para empresa de até 3 pessoas — conferir enquadramento da DGC. |
| Narração | Gemini TTS (`gemini-2.5-flash-preview-tts`), voz definida no piloto (candidatas: Puck, Charon) | Direção de estilo no prompt. Uma chamada por vídeo (`tts_unico`) para poupar cota. `GOOGLE_API_KEY` em `~/.hermes/.env`. |
| Legenda palavra a palavra | faster-whisper (já no Pi) + `@remotion/captions` | Timestamps por palavra. |
| Ilustrações | Gemini Image via API (ou `agy`) | Estilo fixo DGC definido num prompt-base em `marca/estilo-ilustracao.md`. |
| Animações/ícones | Lottie (`@remotion/lottie`) + LottieFiles | Arquivos versionados em `remotion/public/lottie/` com licença anotada. |
| Telas de sistema | Componentes React recriados com dados fictícios | Nunca print do sistema real. |
| Trilha | Pixabay Music / YouTube Audio Library + ducking automático | — |
| B-roll realista | Veo (opcional, **desligado por padrão**) | Só em ganchos, se houver cota. |
| QA automático | Gemini vision julgando frames-chave + `conferir_fala.py` (Whisper confere a fala contra o roteiro) | Herdados da campanha. |
| Capa | `renderStill` do Remotion | Capa padronizada por série. |

## 5. Arquitetura

### 5.1 Repositório `dgc-reels`

```text
~/projects/dgc-reels/
  CLAUDE.md                 # contexto ENXUTO (lição da campanha: não herdar contexto gigante)
  marca/                    # identidade aprovada: logo.svg, tokens.json, fontes, estilo-ilustracao.md
  metodo/METODO.md          # os 5 atos, séries, restrições duras, tom goiano
  backlog/
    lote-01.yaml            # cardápio: 39 ideias (id, série, título, gancho, resumo, status)
    cards/NN-slug/
      card.yaml             # estado, tentativas, erros, notas do Gabriel
      roteiro.json          # falas por segmento
      cenas.json            # o que aparece em cada cena
  pipeline/                 # tts.py, legendas.py, imagens.py, qa.py, conferir_fala.py
  remotion/                 # projeto Remotion: tema DGC, cenas por ato, séries
  loop/
    tick.py                 # máquina de estados determinística: decide o próximo passo
    falhas.py               # classificação de falhas e política de retry
    telegram.py             # formatação das mensagens de aprovação
  scripts/watchdog.sh       # verificação sem LLM
  trilhas/LICENCAS.md
  .github/workflows/ci.yml  # reusa ci-node do core (lint/typecheck/test)
  out/                      # gitignored: renders, frames, áudio
```

Versionado: código, marca, método, backlog e cards (texto). Fora do git: MP4, WAV, PNG de frames.

### 5.2 Ciclo de vida de um card

```text
ideia → aprovada → roteirizada → narrada → legendada → ilustrada → renderizada
      → qa_ok → enviada → aprovada_final
Desvios: refazer (nota do Gabriel; volta ao passo indicado)
         falha (com contador de tentativas)
         bloqueada (precisa de humano)
         cortada (Gabriel removeu do lote)
```

`loop/tick.py` é **determinístico** (sem LLM): lê os cards, escolhe o próximo passo de maior
prioridade e o executa ou o delega. O LLM entra só nos passos criativos: cardápio, roteiro/cenas,
prompts de ilustração, julgamento de QA e propostas de identidade.

Prioridade do tick: (1) responder ao Gabriel/aplicar decisões pendentes, (2) terminar card em
andamento, (3) enviar pacote de revisão quando houver 6 cards em `qa_ok`, (4) iniciar o próximo card
`aprovada` na ordem do lote.

### 5.3 Papéis

| Quem | Faz |
|---|---|
| Hermes (cron) | Roda `tick.py`, executa passos criativos, fala com o Gabriel no Telegram, aplica decisões nos cards, commita mudanças de backlog/cards. |
| `claude-20a` (via `dev run`) | Mudanças de **código** (template, cenas, pipeline) em branch/worktree → abre PR. |
| `claude-20b` (via `dev run`) | Revisa o PR automaticamente (correção, restrições duras, dados sensíveis, testes). |
| CI do GitHub | Lint, typecheck, testes, `remotion still` de smoke. |
| Gabriel | Aprova identidade, cardápio, piloto e pacotes de vídeo. |

Commits de **conteúdo** (cards, backlog) vão direto para `main` pelo Hermes. Mudanças de **código**
sempre passam por PR + review + CI. Código e docs em commits separados.

### 5.4 Protocolo do Telegram

Mensagens curtas, linguagem simples. Formatos:

**Cardápio** (um bloco por ideia):
```text
#04 · Série A (case real)
"32 telas por dia" — contador abria 4 telas × 8 clientes.
A DGC juntou tudo numa tela só.
```

**Pacote de revisão:** capa + MP4 de cada vídeo (limite de 50 MB por arquivo do bot; renders
ficam abaixo disso) e uma linha por vídeo.

Respostas que o Hermes entende:

| Resposta | Efeito |
|---|---|
| `ok tudo` / `ok 1-12` | aprova itens |
| `corta 7` | card → cortada |
| `muda 3: <instrução>` | reescreve a ideia/roteiro |
| `refaz 5: <instrução>` | card → refazer, com nota |
| `pausa` / `retoma` | pausa ou retoma o loop |
| `status` | resumo imediato |

Resposta ambígua: o Hermes pergunta de volta, nunca adivinha.

### 5.5 Controle de falhas

| Falha | Detecção | Reação |
|---|---|---|
| Cota Gemini (TTS/imagem) esgotada | resposta 429 / mensagem "cota DIÁRIA" (já tratada no `tts.py`) | Card fica em espera até a renovação; o loop segue com passos que não usam a cota (render, QA de outros cards). |
| Erro transitório de API | timeout / 5xx | Retry com backoff (30 s, 2 min, 10 min), até 3 tentativas. |
| Render travou/OOM | exit code ≠ 0, processo morto, timeout de 60 min | Refaz com `concurrency=1`; segunda falha → `bloqueada` + alerta. |
| QA reprovou | Gemini vision ou `conferir_fala` abaixo do limiar | Regenera o passo culpado até 2×; depois → `bloqueada` com o motivo. |
| Dado sensível detectado | varredura de regex (telefone, CNPJ, e-mail, nomes da lista proibida) no roteiro/cenas + QA visual | **Bloqueio imediato**, sem retry automático. |
| Review do PR pediu mudança 2× | estado do PR | Para e chama o Gabriel. |
| Circuit breaker | 3 falhas seguidas em qualquer passo | Loop pausa sozinho e manda alerta. |
| Sem progresso | watchdog: nenhum card mudou de estado em 2 h | Alerta no Telegram. |
| Saúde do Pi | watchdog: temperatura > 80 °C, disco < 10 GB livres | Pausa renders e alerta. |
| Dois writers | lock em `loop/.lock` com PID + heartbeat | Tick não roda se houver lock vivo; lock antigo (> 30 min sem heartbeat) é removido com registro. |

Higiene: frames apagados após o mux de cada vídeo; cada card guarda um log próprio em `out/logs/`.

**Relatório diário às 8h:** prontos, em produção, falhas, o que espera o Gabriel.

### 5.6 Agendamento

- **Sprint (até seg 13/10):** job `dgc-reels-tick` a cada 20 min.
- **Watchdog:** job `dgc-reels-watchdog` a cada 30 min, `--no-agent` (script puro, só fala se houver problema).
- **Relatório:** job `dgc-reels-relatorio` às 8h.
- **Depois do sprint:** tick passa para a janela noturna (22h–7h, a cada 30 min) até completar o estoque.

## 6. Cronograma do sprint

| Quando | Entrega | Portão do Gabriel |
|---|---|---|
| Sex 10 | Spec + plano executável; pré-requisitos (seção 7); repo criado; jobs prontos | Aprovar o plano e ligar o gateway |
| Sáb 11 manhã | 3 propostas de identidade | Escolher 1 |
| Sáb 11 | Fork do pipeline com tema DGC + cardápio dos 39 | Aprovar cardápio |
| Sáb 11 noite | Piloto: case Ipeconect "32 telas" | Aprovar método e voz |
| Dom 12 → Seg 13 | Produção em série, pacotes de 6 | Aprovar pacotes |
| Após seg 13 | Modo cron noturno até completar o estoque | — |

Teto físico: Pi 4 leva de 10 a 30 min por vídeo de 40 s; a cota diária do Gemini TTS também limita.
Por isso a meta de segunda é ≥ 12 vídeos aprovados, não 39.

## 7. Pré-requisitos (dependem do Gabriel)

1. Ligar o gateway do Hermes (`hermes gateway install` + start) e confirmar o chat do Telegram.
2. Autorizar a criação do repo `DGC-ghub/dgc-reels` (privado).
3. Opcional: decidir se o Veo entra (custo/cota).

## 8. Testes

- `tick.py`, `falhas.py` e o parser de respostas do Telegram com testes unitários (TDD): transições
  de estado, política de retry, circuit breaker, lock.
- Varredura de dados sensíveis com testes de casos positivos e negativos.
- CI roda um `remotion still` de cada tipo de cena como smoke.
- O piloto é o teste de aceitação do método.

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Template ruim replicado em 39 vídeos | Portão do piloto antes da série. |
| Cota gratuita do Gemini insuficiente | `tts_unico`, fila por cota, aceitar meta de ≥ 12. |
| Hermes interpreta mal uma resposta | Parser estrito; ambiguidade → pergunta de volta. |
| Vazamento de dado real | Lista proibida + regex + QA visual + bloqueio sem retry. |
| Pi superaquecer em 4 dias de render | Watchdog de temperatura; `concurrency` baixo. |
| Licença do Remotion | Conferir enquadramento da DGC antes de publicar. |
