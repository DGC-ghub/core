# Instalação do Hermes na VM (terceiro cérebro da DGC)

Estado em 26/11/2026: tudo instalado e configurado na VM trabalhadora, **menos** os três passos do dono (abaixo). O
serviço `dgc-cerebro` está instalado mas **desligado**, e nenhum job de cron foi criado.

## Como ficou

| Peça | Onde | Observação |
|---|---|---|
| Usuário | `cerebro` (home `/home/cerebro`, modo 700, `loginctl enable-linger`) | Isolado do `dgc`: o terminal do Hermes não lê os segredos do `dgc`. Em 26/11 também foram fechados `/home/pi` (750) e os arquivos do `dgc` em `/tmp` (o-rwx); ver "Isolamento do `cerebro`" abaixo. Teste: `sudo -u cerebro cat /home/dgc/.config/dgc-atendimento/compose.env` dá "Permission denied". |
| Hermes Agent | `/home/cerebro/.hermes/hermes-agent`, método git, commit `9976f4857b72439d79016354d7b6e1a3ee952e2f` | `hermes --version` → `v0.22.5+1722.g9976f48`. Instalado com o `scripts/install.sh` do próprio repositório (`--commit … --non-interactive --skip-browser --skip-computer-use`). **Não rode `hermes update`** sem ok do dono: ele sai do commit fixado. |
| Config do Hermes | `~/.hermes/config.yaml` | `model.provider: openai-codex`, `model.default: gpt-6-sol`, `timezone: America/Sao_Paulo`, `terminal.cwd: /home/cerebro/cerebro`, `whatsapp.unauthorized_dm_behavior: ignore`. |
| `.env` do Hermes | `~/.hermes/.env` (modo 600) | `WHATSAPP_ENABLED=true`, `WHATSAPP_MODE=bot`, `WHATSAPP_ALLOWED_USERS=<telefones dos dois sócios, com e sem o 9º dígito>`, `WHATSAPP_GROUP_POLICY=allowlist`, `WHATSAPP_GROUP_ALLOWED_USERS=<JID do grupo dos sócios>`, `WHATSAPP_REQUIRE_MENTION=true` e `WHATSAPP_MENTION_PATTERNS=["^[ ]*@?hermes(?![a-z])"]` (no grupo só responde a @menção, resposta a ele ou "hermes," no começo da frase). Só o grupo dos sócios é liberado; qualquer outro grupo é ignorado. |
| Personalidade | `~/.hermes/SOUL.md` (fonte: `hermes/SOUL.md`) | |
| Plugin `barra-do-robo` | `~/.hermes/plugins/barra-do-robo/` (fonte: `hermes/plugins/barra-do-robo/`), habilitado em `plugins.enabled` | Gancho `pre_gateway_dispatch`: no WhatsApp, o Hermes descarta (`skip`) qualquer texto que, sem espaços à esquerda, comece com "/" (comandos do robô de vendas), e também mensagem marcada como do dono do aparelho. O resto segue normal. Teste: `python3 -m pytest automations/terceiro-cerebro/test_barra_do_robo.py`. |
| Skill | `~/.hermes/skills/dgc/dgc-cerebro/SKILL.md` (fonte: `hermes/skills/dgc-cerebro/SKILL.md`) | |
| Pasta de trabalho | `/home/cerebro/cerebro` | `AGENTS.md` (fonte: `hermes/AGENTS.md`), `repos -> /srv/cerebro/repos`, `docs -> /srv/cerebro/docs`. |
| CLI `quadro` | `/home/cerebro/ferramentas/terceiro-cerebro/*.py` + wrapper `/home/cerebro/.local/bin/quadro` | Config em `/home/cerebro/.config/dgc-cerebro/cerebro.env` (modo 600). Estado da cota em `~/.local/state/dgc-cerebro/cota.json`. |
| Conhecimento | `/srv/cerebro/{repos,docs}` (dono `dgc`, grupo `cerebro`, pastas 750, arquivos 640) | Atualizado por `deploy/atualizar-copias.sh`, instalado em `~dgc/bin/atualizar-copias-cerebro.sh`. |
| Timer das cópias | `~dgc/.config/systemd/user/cerebro-copias.{service,timer}` (usuário `dgc`) | Todo dia 06:00 UTC = 03:00 de Brasília. Ativo. Rodar à mão: `systemctl --user start cerebro-copias.service`; log: `journalctl --user -u cerebro-copias`. |
| Serviço | `/home/cerebro/.config/systemd/user/dgc-cerebro.service` | Gerado pelo próprio Hermes (`generate_systemd_unit`: `HERMES_SUPERVISED_CHILD=1`, `KillMode=mixed`, `ExecStop`/`ExecStopPost` com limpeza do cgroup, `StartLimitIntervalSec=0`, `RestartPreventExitStatus=78`, `TimeoutStopSec` calculado), mais `WorkingDirectory=%h/cerebro`, `MemoryMax=1500M`, `RestartSec=30`, `RestartSteps=5` e `RestartMaxDelaySec=10min`. **Instalado, desabilitado e parado.** |

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

### Memória do Hermes (só por instrução)

A memória do Hermes é por perfil, não por pessoa: um `MEMORY.md` e uma busca de sessões (`session_search`) que cobre as conversas
de todos. Não existe isolamento por sócio. O que foi feito: `memory.user_profile_enabled: false` (desliga o `USER.md`, onde
cairia o perfil pessoal de cada sócio) e, no SOUL e na skill, a regra de só gravar trabalho na memória, nunca usar
`session_search` de conversa do outro sócio para assunto pessoal e, de uma conversa para a outra, só passar item de trabalho.
**Isso é garantido só por instrução (prompt), não por mecanismo.** Se isso virar problema, o caminho é um perfil do Hermes por sócio.

### Isolamento do `cerebro` (o que ele consegue ler na VM)

- Fechado em 26/11: `chmod 750 /home/pi` (era 755; dados antigos do Paperclip de 15/11, `dgc-hub`, projetos) e `chmod -R o-rwx` nos
  arquivos do `dgc` em `/tmp` (81 mil arquivos de trabalho dos agentes). Nada do `dgc` roda como outro usuário, então os serviços não foram afetados. O `/tmp` privado (abaixo) fecha o resto para o serviço.
- Ainda legível, de propósito ou fora do alcance: `/srv/cerebro` (as cópias), `/etc` e `/var/lib` do sistema (só arquivos padrão do Ubuntu),
  os serviços em `127.0.0.1` (Paperclip 3100, Chatwoot, robô: pedem token que o `cerebro` não tem) e o `tailscale status`. O `docker.sock` é do grupo `docker` (o `cerebro` não está).
- **/tmp privado e teto de memória (drop-ins de sistema, uid 1002 = `id -u cerebro`):**
  - `deploy/systemd/user@1002.service.d/cerebro.conf` -> `/etc/systemd/system/user@1002.service.d/cerebro.conf` (`PrivateTmp=yes`).
    Tudo que o gerenciador de usuário do `cerebro` sobe (o serviço do Hermes, workers, crons) vê um `/tmp` vazio e só dele.
    `PrivateTmp` dentro da unit de usuário não funciona nesta VM (`apparmor_restrict_unprivileged_userns=1`), por isso vai no `user@1002.service`.
  - `deploy/systemd/user-1002.slice.d/memoria.conf` -> `/etc/systemd/system/user-1002.slice.d/memoria.conf` (`MemoryHigh=1500M`, `MemoryMax=1800M`):
    teto para tudo do usuário, inclusive os escopos `hermes-worker-*` que escapam do `MemoryMax=1500M` da unit.
  - Aplicar: copiar os dois arquivos, `sudo systemctl daemon-reload` e `sudo systemctl restart user@1002.service` (com nada do `cerebro` rodando).
  - Resíduo: uma sessão interativa do `cerebro` (SSH, `sudo -u cerebro -i`) **não** passa pelo gerenciador de usuário e ainda vê o `/tmp` real; ali só
    vale o `chmod -R o-rwx` de 26/11 nos arquivos do `dgc` que já existiam, e arquivos novos do `dgc` com umask 022 ficam legíveis.
    Não use sessão interativa do `cerebro` para tarefas do agente.
- Frente de trade: o `atualizar-copias.sh` tira da cópia de `day-trade-app` e `dgc-ai-desk` qualquer arquivo ou pasta com `cofre`, `vault`, `saldo`, `carteira` ou `wallet` no nome (em 26/11 não havia nenhum).

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

## Grupo dos sócios

Desde 26/11 o Hermes está no grupo "DGC Hub · Sócios + Hermes" (Gabriel, Danilo e o número da DGC). Trabalho (cobrança, crítica, erros e
vitórias, sempre com prova) vai para o grupo; o privado fica para assunto pessoal. As duas rodadas diárias (`deploy/cron-jobs.md`) falam no grupo,
com teto de 3 mensagens espontâneas por dia (`quadro cota grupo` / `quadro enviei grupo`). Os sócios podem pedir rotinas novas no grupo e o Hermes
mesmo cria o job de cron. O Danilo está em `SOCIOS` (`danilo:<telefone>`) e na allowlist; o nome e o LID dele o Hermes aprende na primeira
mensagem e guarda na memória. O robô de vendas (Evolution) usa o mesmo número: como ele só trata "/comandos" de sócio e o plugin
`barra-do-robo` descarta os "/" no Hermes, os dois não se atropelam, mas vale conferir no primeiro dia como o robô trata mensagens do grupo.

## Quem é quem no WhatsApp (só na VM)

O Gabriel chega ao Hermes com outro nome de contato e com um LID, não com o telefone, e a allowlist leva o telefone com e sem o 9º dígito.
O mapeamento real (nome de contato e LID) vive só no `AGENTS.md` instalado em `/home/cerebro/cerebro/AGENTS.md`; no repositório ficam
placeholders (`<nome do Gabriel no WhatsApp>`, `<LID do Gabriel>`). Ao reinstalar o `AGENTS.md`, troque os placeholders com `sed` na VM.
Em conversa o Hermes **sempre responde** (o `[SILENT]` é só do cron): o gateway rejeita silêncio em resposta a sócio e manda uma mensagem padrão.

## Convivência com o robô de vendas (resolvido)

- **Comandos com "/":** o plugin `barra-do-robo` (acima) faz o Hermes nunca responder a eles no WhatsApp. Sem o plugin,
  o gateway executaria `/status`, `/help` etc. ou responderia "comando desconhecido" por cima do robô.
- **Mensagens do próprio número (robô via Evolution, alertas):** o bridge do Hermes em modo `bot` já descarta
  mensagens `fromMe` (`scripts/whatsapp-bridge/bridge.js`, linhas 557 a 594: `drop_echo`/`drop_disabled` em
  `owner_message_gate.js`), a menos que `WHATSAPP_FORWARD_OWNER_MESSAGES` seja ligado (padrão desligado; **não ligar**).
  Se ligar, o plugin ainda descarta o que vier marcado como do dono (`whatsapp_from_owner`).
- **Outros números** (clínicas): fora da `WHATSAPP_ALLOWED_USERS`, o Hermes ignora (`unauthorized_dm_behavior: ignore`).
- Pendência: `/sethome` (para entrega do cron sem chat id) também começa com "/" e seria descartado pelo plugin; use o
  destino explícito (`whatsapp:<LID do Gabriel>@lid`) no `cron-jobs.md`.
