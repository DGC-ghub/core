# Limpeza diária do disco da VM trabalhadora (DGC-497)

O disco encheu em 24/11 (DGC-439) e em 26/11. Esta limpeza roda 1 vez por dia, sem IA e sem custo.
Arquivos: `automations/vm-limpeza/`.

## O que faz

| # | Item | Regra | Quem faz |
|---|------|-------|----------|
| 1 | `/tmp` | Só do usuário `dgc`, sem mudança há mais de 3 dias (pasta: nada dentro mudou), sem processo com cwd ou arquivo aberto dentro, sem ponto de montagem dentro. Ignora nomes com `.` na frente. | `vm-limpeza.sh` (diário) |
| 2 | Pastas de run do Paperclip | Ver "Pastas de run" abaixo. | `~/bin/limpa-runs.sh` (cron, de hora em hora), já existe |
| 3 | Journal | `SystemMaxUse=300M`. | `journald-dgc.conf` (root, 1 vez) |
| 4 | Caches | `~/.npm/_cacache`, `~/.cache/npm`, `~/.cache/pip`, `~/.cache/node-gyp`, `~/.node-gyp`, no máx. 1 vez por 7 dias. Pula se npm/pnpm/pip estiver rodando. **Não** apaga o store do pnpm (DGC-249). | `vm-limpeza.sh` (semanal, por arquivo de estado) |
| 5 | Alerta de 85% | Já existe: `vigia-disco.sh`, a cada 10 min, avisa na mudança (85% sobe, 80% volta). Mesmo canal (`vigia.env`). Não duplicado. | `vigia-disco.sh` |

Nunca toca: `/home/cerebro`, `/srv/cerebro`, `/etc/dgc-cerebro`, `~dgc/apps`, volumes do Docker, `~dgc/hermes-piloto`
(lista de proteção dentro do script, além de só olhar `/tmp` e os caches).

## Pastas de run (item 2): por que não há regra nova

Conferido na VM em 26/11/2026: `~/paperclip/.paperclip-runtime/runs/<run-id>/workspace` é uma **cópia descartável**
do workspace (o resultado volta para a Pi por sync-back). O nome da pasta é só o ID do run; não há ligação com a tarefa
dentro da pasta. O `limpa-runs.sh` (DGC-36, ajustado em DGC-437) já apaga a pasta de run sem mudança há 2 h e sem
processo com cwd dentro. É mais agressivo que "7 dias e tarefa fechada", e seguro: run de tarefa aberta que está
parada volta a ser copiado no próximo run. Os 16 GB de 26/11 eram esse acúmulo antes do ajuste: hoje são 4,6 GB
e o log mostra 19 pastas apagadas e 14 GB liberados na rodada das 20:17 UTC.
Mapear pasta → run → tarefa pela API não acrescenta segurança. Se os sócios preferirem a regra de 7 dias, é só
trocar `LIMITE_MIN` no `limpa-runs.sh`.

## Como usar

```bash
# ensaio (padrão): só lista o que apagaria e o tamanho
~/bin/vm-limpeza.sh
# caches mesmo que a semana não tenha fechado
~/bin/vm-limpeza.sh --forcar-caches
# apagar de verdade
~/bin/vm-limpeza.sh --aplicar
```

Variáveis para teste: `LIMPEZA_TMP_DIR`, `LIMPEZA_TMP_DIAS`, `LIMPEZA_CACHES`, `LIMPEZA_STATE`, `LIMPEZA_LOCK`.

## Instalação (só depois do merge pelos sócios)

```bash
cp automations/vm-limpeza/vm-limpeza.sh ~/bin/ && chmod +x ~/bin/vm-limpeza.sh
cp automations/vm-limpeza/vm-limpeza.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now vm-limpeza.timer
# journal (root, uma vez):
sudo install -D -m 644 automations/vm-limpeza/journald-dgc.conf /etc/systemd/journald.conf.d/dgc-limite.conf
sudo systemctl restart systemd-journald
```

Ver o resultado: `journalctl --user -u vm-limpeza.service -n 50`. Desligar: `systemctl --user disable --now vm-limpeza.timer`.
O timer roda às 05:00 UTC, longe dos backups (03:30, 03:45, 06:30).

## Como voltar atrás

Só apaga arquivo temporário e cache regenerável, então não há restore. Se algo de `/tmp` fizer falta, o agente
recria no próximo run. Para parar: desabilitar o timer (acima).
