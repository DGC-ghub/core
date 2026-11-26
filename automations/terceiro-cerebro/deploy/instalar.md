# Instalação do Hermes na VM (terceiro cérebro da DGC)

Estado em 26/11/2026: tudo instalado e configurado na VM trabalhadora, **menos** os três passos do dono (abaixo). O
serviço `dgc-cerebro` está instalado mas **desligado**, e nenhum job de cron foi criado.

## Como ficou

| Peça | Onde | Observação |
|---|---|---|
| Usuário | `cerebro` (home `/home/cerebro`, modo 700, `loginctl enable-linger`) | Isolado do `dgc`: o terminal do Hermes não lê os segredos do `dgc`. Teste: `sudo -u cerebro cat /home/dgc/.config/dgc-atendimento/compose.env` dá "Permission denied". |
| Hermes Agent | `/home/cerebro/.hermes/hermes-agent`, método git, commit `9976f4857b72439d79016354d7b6e1a3ee952e2f` | `hermes --version` → `v0.22.5+1722.g9976f48`. Instalado com o `scripts/install.sh` do próprio repositório (`--commit … --non-interactive --skip-browser --skip-computer-use`). **Não rode `hermes update`** sem ok do dono: ele sai do commit fixado. |
| Config do Hermes | `~/.hermes/config.yaml` | `model.provider: openai-codex`, `model.default: gpt-6-sol`, `timezone: America/Sao_Paulo`, `terminal.cwd: /home/cerebro/cerebro`, `whatsapp.unauthorized_dm_behavior: ignore`. |
| `.env` do Hermes | `~/.hermes/.env` (modo 600) | `WHATSAPP_ENABLED=true`, `WHATSAPP_MODE=bot`, `WHATSAPP_ALLOWED_USERS=<numero do Gabriel>`, `WHATSAPP_GROUP_POLICY=pairing` (grupos fechados: não repassa nada de grupo). Danilo entra depois do aceite dele. |
| Personalidade | `~/.hermes/SOUL.md` (fonte: `hermes/SOUL.md`) | |
| Plugin `barra-do-robo` | `~/.hermes/plugins/barra-do-robo/` (fonte: `hermes/plugins/barra-do-robo/`), habilitado em `plugins.enabled` | Gancho `pre_gateway_dispatch`: no WhatsApp, o Hermes descarta (`skip`) qualquer texto que, sem espaços à esquerda, comece com "/" (comandos do robô de vendas), e também mensagem marcada como do dono do aparelho. O resto segue normal. Teste: `python3 -m pytest automations/terceiro-cerebro/test_barra_do_robo.py`. |
| Skill | `~/.hermes/skills/dgc/dgc-cerebro/SKILL.md` (fonte: `hermes/skills/dgc-cerebro/SKILL.md`) | |
| Pasta de trabalho | `/home/cerebro/cerebro` | `AGENTS.md` (fonte: `hermes/AGENTS.md`), `repos -> /srv/cerebro/repos`, `docs -> /srv/cerebro/docs`. |
| CLI `quadro` | `/home/cerebro/ferramentas/terceiro-cerebro/*.py` + wrapper `/home/cerebro/.local/bin/quadro` | Config em `/home/cerebro/.config/dgc-cerebro/cerebro.env` (modo 600). Estado da cota em `~/.local/state/dgc-cerebro/cota.json`. |
| Conhecimento | `/srv/cerebro/{repos,docs}` (dono `dgc`, grupo `cerebro`, pastas 750, arquivos 640) | Atualizado por `deploy/atualizar-copias.sh`, instalado em `~dgc/bin/atualizar-copias-cerebro.sh`. |
| Timer das cópias | `~dgc/.config/systemd/user/cerebro-copias.{service,timer}` (usuário `dgc`) | Todo dia 06:00 UTC = 03:00 de Brasília. Ativo. Rodar à mão: `systemctl --user start cerebro-copias.service`; log: `journalctl --user -u cerebro-copias`. |
| Serviço | `/home/cerebro/.config/systemd/user/dgc-cerebro.service` | `hermes gateway run --external-supervisor` em primeiro plano, `MemoryMax=1500M`, `Restart=on-failure`, `RestartSec=30`. **Instalado, desabilitado e parado.** |

### Detalhes das cópias

- Repositórios (de `DGC-ghub`): produto-hermes, day-trade-app, dgc-reels, core, dgc-ai-desk, Vitrine_DGC, dgc-template-ts.
  Clonados por HTTPS com o acesso GitHub que o `dgc` já tem na VM (`credential.helper store`); a chave
  `~/.ssh/id_github_trabalhadora` não tem mais acesso. Em cada cópia: `git remote set-url --push origin no_push` (nenhum
  push sai dali) e um sparse-checkout que deixa de fora `.env*`, `*.env`, `*.pem`, `*.key`, `node_modules/`, `*.db`,
  `*.sqlite`, `pacientes/` e `conversas/`.
- Documentos: `rsync` de `docs/` da cópia de trabalho mais recente dos agentes (`~dgc/paperclip/.paperclip-runtime/runs/*/workspace/docs`,
  a que tem `docs/foco/PAINEL.md`), com os mesmos excludes mais `.git/` e `**/pacientes/**`, `**/conversas/**`. Sem cópia
  de trabalho, usa `repos/core/docs`.
- Trava final: arquivo que casa com `sk-ant-|ghp_|github_pat_` sai da cópia (em `docs/`, é apagado; em `repos/`, sai do
  checkout) e, se tiver chave de verdade, o serviço falha e avisa no log.
- O `cerebro` roda `git` nessas cópias (`safe.directory '*'` no `.gitconfig` dele); `git push` falha de propósito.

## Os 3 passos do dono (Gabriel)

Nenhuma chave passa pelo chat. Faça um, confira, e só então o próximo.

### 1. Chave do quadro (Paperclip)

A chave de API do quadro (board API key) é da conta do Gabriel, e o `quadro` age como ele.

1. Entre no Paperclip no navegador, logado com a sua conta: o endereço do Paperclip da DGC (o do servidor do Danilo, só na tailnet).
2. Abra o console do navegador (F12) e rode:
   ```js
   fetch('/api/board-api-keys', {method:'POST', headers:{'content-type':'application/json'},
     body: JSON.stringify({name:'cerebro-vm'})}).then(r=>r.json()).then(k=>console.log(k.token, k.expiresAt))
   ```
   O `token` aparece só uma vez. Confira também `expiresAt` (a chave tem validade por padrão; anote a data para renovar).
3. Na VM, como `cerebro`, cole o valor depois de `PAPERCLIP_TOKEN=` (sem aspas, sem espaço):
   ```sh
   ssh -t dgc@<IP-da-VM> 'sudo -u cerebro -i nano /home/cerebro/.config/dgc-cerebro/cerebro.env'
   ```
   O arquivo é modo 600 e fora de qualquer Git. Não cole a chave no chat nem em comentário de tarefa.
4. Teste: `ssh dgc@<IP-da-VM> 'sudo -u cerebro -i quadro pendencias gabriel'` deve listar pendências (não "falta PAPERCLIP_TOKEN").

### 2. Logins do Codex (duas contas do Gabriel)

```sh
ssh -t dgc@<IP-da-VM> 'sudo -u cerebro -i hermes auth add openai-codex'
ssh -t dgc@<IP-da-VM> 'sudo -u cerebro -i hermes auth add openai-codex'
```

Faça o login da **primeira conta** na primeira vez e da **segunda conta** (outra) na segunda. Se aparecer o aviso
"same OpenAI account", a segunda conta não serve: use outra. Confira com `hermes auth list`. O pool passa para a outra
conta quando uma bate o limite.

### 3. Parear o WhatsApp (QR)

```sh
ssh -t dgc@<IP-da-VM> 'sudo -u cerebro -i hermes whatsapp'
```

Escolha o modo `bot` e leia o QR com o celular da DGC (Aparelhos conectados). Ele entra como **segundo aparelho** do
número da DGC; a Evolution segue como o outro aparelho do robô de vendas.

## Depois dos 3 passos (quem constrói)

1. Subir o serviço (o `systemctl --user` do `cerebro` precisa do `XDG_RUNTIME_DIR`):
   ```sh
   ssh dgc@<IP-da-VM> 'sudo -u cerebro env XDG_RUNTIME_DIR=/run/user/$(id -u cerebro) systemctl --user enable --now dgc-cerebro'
   ```
   Confira `active (running)` (mesmo comando com `status`) e `free -h` com mais de 3 GB disponíveis.
2. Criar as rodadas de cobrança: `deploy/cron-jobs.md`.

## Convivência com o robô de vendas (resolvido)

- **Comandos com "/":** o plugin `barra-do-robo` (acima) faz o Hermes nunca responder a eles no WhatsApp. Sem o plugin,
  o gateway executaria `/status`, `/help` etc. ou responderia "comando desconhecido" por cima do robô.
- **Mensagens do próprio número (robô via Evolution, alertas):** o bridge do Hermes em modo `bot` já descarta
  mensagens `fromMe` (`scripts/whatsapp-bridge/bridge.js`, linhas 557 a 594: `drop_echo`/`drop_disabled` em
  `owner_message_gate.js`), a menos que `WHATSAPP_FORWARD_OWNER_MESSAGES` seja ligado (padrão desligado; **não ligar**).
  Se ligar, o plugin ainda descarta o que vier marcado como do dono (`whatsapp_from_owner`).
- **Outros números** (clínicas): fora da `WHATSAPP_ALLOWED_USERS`, o Hermes ignora (`unauthorized_dm_behavior: ignore`).
- Pendência: `/sethome` (para entrega do cron sem chat id) também começa com "/" e seria descartado pelo plugin; use o
  `<CHAT_ID>` explícito no `cron-jobs.md`.
