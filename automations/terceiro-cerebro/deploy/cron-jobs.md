# Rodadas de cobrança (cron do Hermes)

Estes jobs precisam do chat do WhatsApp, que só existe depois do pareamento (passo 3 do
`instalar.md`) e do serviço no ar. Crie-os como o usuário `cerebro`, depois que o Gabriel mandar a primeira mensagem
para o número.

## Horário e fuso

O `config.yaml` do `cerebro` tem `timezone: America/Sao_Paulo` (a VM está em UTC). Esse fuso vale para as expressões
cron do Hermes, então os horários abaixo são **de Brasília**: `0 9 * * 1-6` é 09:00 BRT (12:00 UTC).
Confira depois de criar: `hermes cron list` mostra a próxima execução.

## Descobrir o destino

O WhatsApp entrega o chat do Gabriel com um **LID** (`<LID do Gabriel>@lid`), não com o telefone. É esse id que vai no destino:
`whatsapp:<LID do Gabriel>@lid`. O id aparece no log de entrada do gateway (`hermes logs`, linha `inbound ... chat=...@lid`) depois que
ele escreve para o número da DGC. O valor real fica só na VM (`AGENTS.md` instalado em `~/cerebro`), nunca no repositório.

**O Hermes aceita `@lid` como destino de cron**: o parser do destino do WhatsApp (`_SEND_JID_RE` em `plugins/platforms/whatsapp/adapter.py`)
aceita `...@(g.us|s.whatsapp.net|lid|broadcast|newsletter)` e o envio (`to_whatsapp_jid`, `gateway/whatsapp_identity.py`) devolve o JID
com `@` sem mexer. Telefone puro também vira `<numero>@s.whatsapp.net`, mas pode não ser o mesmo chat que o LID do aparelho dele; use o LID.
`/sethome` não serve (começa com "/" e o plugin `barra-do-robo` o descarta).

## Os dois jobs

O prompt é o mesmo nos dois. Troque `<LID do Gabriel>` antes de rodar.

```bash
sudo -u cerebro -i

PROMPT='Rodada de cobrança do Gabriel. Siga na ordem:
1. Rode `quadro cota gabriel` e `quadro pendencias gabriel`.
2. Se a cota vier `esgotada`, se não houver pendência nem ideia útil para a meta de 15/12, ou se o quadro estiver fora do ar, responda somente `[SILENT]`.
3. Se não, escreva UMA mensagem curta no tom do SOUL.md (pendência mais antiga primeiro, por um ângulo diferente das cobranças anteriores) e então rode `quadro enviei gabriel`.
4. Se `quadro enviei gabriel` imprimir `esgotada`, responda somente `[SILENT]` (a mensagem não deve ser enviada).
Sua resposta final é exatamente a mensagem para o WhatsApp, ou `[SILENT]`.'

# manhã: segunda a sábado, 09:00 de Brasília
hermes cron create "0 9 * * 1-6" "$PROMPT" \
  --name cerebro-manha \
  --skill dgc-cerebro \
  --workdir /home/cerebro/cerebro \
  --deliver "whatsapp:<LID do Gabriel>@lid"

# tarde: segunda a sexta, 17:30 de Brasília
hermes cron create "30 17 * * 1-5" "$PROMPT" \
  --name cerebro-tarde \
  --skill dgc-cerebro \
  --workdir /home/cerebro/cerebro \
  --deliver "whatsapp:<LID do Gabriel>@lid"

hermes cron list
```

- `[SILENT]` na resposta final cancela a entrega (o resultado fica só em `~/.hermes/cron/output/`). Falha do job é entregue
  mesmo assim.
- `--workdir` carrega o `AGENTS.md` da pasta `~/cerebro` no job; `--skill dgc-cerebro` carrega a skill.
- Para testar sem esperar o horário: `hermes cron run cerebro-manha`.
- Para o Danilo (depois do aceite dele em 26/11): crie jobs iguais trocando `gabriel` por `danilo` no prompt e o destino (o LID dele);
  ele também precisa estar em `SOCIOS` no `cerebro.env` e em `WHATSAPP_ALLOWED_USERS` no `.env` do Hermes.

## Cópias de conhecimento (não é job do Hermes)

A atualização diária dos repositórios e documentos (03:00 de Brasília) é um timer do systemd do usuário `dgc`
(`cerebro-copias.timer`), instalado e já ativo. O job `cerebro-copias` do plano original **não** existe no cron do Hermes.
