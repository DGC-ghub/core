# Rodadas de cobrança (cron do Hermes)

As duas rodadas diárias vão para o **grupo dos sócios** ("DGC Hub · Sócios + Hermes"): uma mensagem por rodada, citando pelo nome quem
tem pendência (Gabriel, Danilo ou os dois). Crie-as como o usuário `cerebro`, com o serviço no ar.

## Horário e fuso

O `config.yaml` do `cerebro` tem `timezone: America/Sao_Paulo` (a VM está em UTC). Esse fuso vale para as expressões
cron do Hermes, então os horários abaixo são **de Brasília**: `0 9 * * 1-6` é 09:00 BRT (12:00 UTC).
Confira depois de criar: `hermes cron list` mostra a próxima execução.

## Destino

O destino é o JID do grupo: `whatsapp:<JID do grupo>` (algo como `<numero>@g.us`). O parser de destino do WhatsApp
(`_SEND_JID_RE` em `plugins/platforms/whatsapp/adapter.py:1250-1252`) aceita `@g.us`, `@lid`, `@s.whatsapp.net`, `@broadcast` e
`@newsletter`, e `to_whatsapp_jid` (`gateway/whatsapp_identity.py`) devolve o JID com `@` sem mexer. O valor real do grupo e do LID de cada
sócio fica só na VM (`AGENTS.md` instalado em `~/cerebro`, jobs do cron), nunca no repositório. `/sethome` não serve (começa com "/" e o
plugin `barra-do-robo` o descarta).

## Os dois jobs

O prompt é o mesmo nos dois. Troque `<JID do grupo>` antes de rodar.

```bash
sudo -u cerebro -i

PROMPT='Rodada de cobrança no grupo dos sócios (Gabriel e Danilo). Siga na ordem:
1. Rode `quadro cota grupo`, `quadro pendencias gabriel` e `quadro pendencias danilo`.
2. Se qualquer comando `quadro` sair com código diferente de 0 (fora do ar, recusa, configuração), se a cota do grupo vier `esgotada`, ou se nenhum dos dois tiver pendência nem houver ideia útil para a meta de 15/12, responda somente `[SILENT]`.
3. Se não, escreva UMA mensagem curta para o grupo, no tom do SOUL.md, citando pelo nome quem tem pendência (um ou os dois), a mais antiga de cada um primeiro, com a prova (DGC-n, desde quando) e por um ângulo diferente das cobranças anteriores. Depois rode `quadro enviei grupo`.
4. Se `quadro enviei grupo` imprimir `esgotada` ou sair com código diferente de 0, responda somente `[SILENT]` (a mensagem não deve ser enviada).
Sua resposta final é exatamente a mensagem para o grupo, ou `[SILENT]`.'

# manhã: segunda a sábado, 09:00 de Brasília
hermes cron create "0 9 * * 1-6" "$PROMPT" \
  --name cerebro-manha \
  --skill dgc-cerebro \
  --workdir /home/cerebro/cerebro \
  --deliver "whatsapp:<JID do grupo>"

# tarde: segunda a sexta, 17:30 de Brasília
hermes cron create "30 17 * * 1-5" "$PROMPT" \
  --name cerebro-tarde \
  --skill dgc-cerebro \
  --workdir /home/cerebro/cerebro \
  --deliver "whatsapp:<JID do grupo>"

hermes cron list
```

- Para trocar o prompt de um job que já existe: `hermes cron edit <id> --prompt "$PROMPT"` (o `edit` mantém id, horário e
  destino). Para trocar de destino, apague (`hermes cron remove <id>`) e crie de novo.
- `[SILENT]` na resposta final cancela a entrega (o resultado fica só em `~/.hermes/cron/output/`). Falha do job é entregue
  mesmo assim.
- `--workdir` carrega o `AGENTS.md` da pasta `~/cerebro` no job; `--skill dgc-cerebro` carrega a skill.
- Para testar sem esperar o horário: `hermes cron run cerebro-manha` (manda de verdade para o grupo, se houver o que dizer).
- Teto: no máximo 3 mensagens espontâneas por dia no grupo, em `quadro cota grupo` / `quadro enviei grupo` (contado à parte da cota de
  cada sócio, que ficou sem uso nas rodadas).

## Balanço da meta em 15/12 (uma vez só)

O spec pede um balanço da meta (1º cliente pagante até 15/12/2026) no próprio dia. Job de uma vez só (o Hermes apaga depois de
rodar), às 10:00 de Brasília, no grupo, dentro das mesmas travas:

```bash
BALANCO='Hoje é 15/12/2026, o prazo da meta da DGC: 1º cliente pagante. Faça o balanço no grupo dos sócios.
1. Rode `quadro cota grupo`, `quadro pendencias gabriel`, `quadro pendencias danilo` e leia `docs/foco/PAINEL.md`.
2. Se qualquer `quadro` sair com código diferente de 0 ou a cota vier `esgotada`, responda somente `[SILENT]`.
3. Escreva UMA mensagem curta, no tom do SOUL.md: bateu ou não bateu a meta, com a prova (DGC-n, placar do PAINEL, data), o que
   faltou ou o que funcionou, e o próximo passo mais importante. Sem inventar número: se não achou, diga que não achou.
4. Rode `quadro enviei grupo`; se imprimir `esgotada` ou sair com código diferente de 0, responda somente `[SILENT]`.
Sua resposta final é exatamente a mensagem para o grupo, ou `[SILENT]`.'

hermes cron create "2026-12-15T10:00:00" "$BALANCO" \
  --name balanco-15-12 \
  --skill dgc-cerebro \
  --workdir /home/cerebro/cerebro \
  --deliver "whatsapp:<JID do grupo>"
```

## Rotinas criadas pelo próprio Hermes

Quando um sócio pede uma rotina no grupo ("todo domingo me faz um papo reto da semana"), o Hermes cria o job com a ferramenta de cron dele
(entrega no grupo), confirma no grupo e guarda a preferência na memória. Travas (no SOUL e na skill): nunca manda para quem não é sócio
nem para fora do grupo e dos sócios, respeita o teto do `grupo` e só cria o que foi pedido. O plugin `trava-de-saida` garante parte
disso por mecanismo: recusa job entregando fora da lista de destinos, mais frequente que de hora em hora, ou com script/monitor.
Ver os jobs: `hermes cron list`. Depois de mudar a regra do prompt (por exemplo, código diferente de 0 = `[SILENT]`), atualize também
os jobs que o Hermes criou (`hermes cron edit <id> --prompt ...`).

## Cópias de conhecimento (não é job do Hermes)

A atualização dos repositórios e documentos (a cada 3 horas) é um timer do systemd do dono das cópias
(`cerebro-copias.timer`). O job `cerebro-copias` do plano original **não** existe no cron do Hermes.
