# Instalação do Hermes (terceiro cérebro da DGC)

Como instalar o terceiro cérebro numa máquina Linux. Os detalhes da máquina da DGC (usuários, permissões, onde fica cada
segredo, o que cada usuário consegue ler e os riscos que sobram) ficam no documento interno de infraestrutura, fora deste
repositório.

## Peças

| Peça | Onde | Fonte neste repositório |
|---|---|---|
| Usuário do agente | um usuário Linux só para o Hermes (sem sudo, home 700) | |
| Hermes Agent | `~/.hermes/hermes-agent`, instalado pelo `scripts/install.sh` do próprio Hermes num commit fixado | |
| Personalidade | `~/.hermes/SOUL.md` | `hermes/SOUL.md` |
| Skill | `~/.hermes/skills/dgc/dgc-cerebro/SKILL.md` | `hermes/skills/dgc-cerebro/SKILL.md` |
| Pasta de trabalho | `~/cerebro` com `AGENTS.md`, `repos/` e `docs/` (links para as cópias de leitura) | `hermes/AGENTS.md` (placeholders) |
| Plugins | `~/.hermes/plugins/barra-do-robo/` e `~/.hermes/plugins/trava-de-saida/`, **donos root, só leitura** | `hermes/plugins/*` |
| CLI `quadro` | código em diretório do root, só leitura; wrapper em `/usr/local/bin/quadro`; roda como usuário de serviço próprio | `*.py` desta pasta |
| Lista de destinos | arquivo do root lido pelo `trava-de-saida` (`/etc/dgc-cerebro/destinos.conf`) | |
| Cópias de leitura | clones parciais dos repositórios e cópia dos documentos, atualizados por um timer | `deploy/atualizar-copias.sh`, `deploy/cerebro-copias.{service,timer}` |
| Serviço | unit de usuário `dgc-cerebro` | `deploy/dgc-cerebro.service` |
| Rodadas e rotinas | cron do Hermes | `deploy/cron-jobs.md` |

## Passo a passo

1. **Usuário do agente.** Crie o usuário, `loginctl enable-linger`, home 700. Ele não pode ler segredo de nenhum outro serviço.
2. **Hermes.** Rode o `scripts/install.sh` do Hermes como esse usuário, no commit fixado (`--commit <sha> --non-interactive
   --skip-browser --skip-computer-use`). Configure `model.*`, `timezone: America/Sao_Paulo`, `terminal.cwd` apontando para
   `~/cerebro` e `whatsapp.unauthorized_dm_behavior: ignore`. No `.env` do Hermes: WhatsApp em modo `bot`, allowlist só com os
   sócios, `WHATSAPP_GROUP_POLICY=allowlist` com o grupo dos sócios, `WHATSAPP_REQUIRE_MENTION=false`. Não rode `hermes update` sem
   ok do dono (sai do commit fixado).
3. **CLI `quadro` fora do alcance do agente.** A chave do quadro é do dono e tem os poderes dele, então o agente não pode lê-la
   nem mudar o código que a usa:
   - um usuário de serviço próprio para a CLI (sem login, sem sudo), que é o único a ler o arquivo de configuração
     (`CHAVE=VALOR`: `PAPERCLIP_URL`, `PAPERCLIP_TOKEN`, `PAPERCLIP_COMPANY`, `PAINEL_PATH`, `COTA_PATH`, `SOCIOS`; ver `README.md`);
   - código copiado para um diretório do root, só leitura; um wrapper do root em `/usr/local/bin/quadro` que fixa `CEREBRO_ENV`
     e roda `python3 -E -s -B .../quadro.py` como esse usuário;
   - uma regra única de sudo, sem senha, que deixa o usuário do agente rodar só esse wrapper como o usuário da CLI (validar com
     `visudo -cf` antes de instalar);
   - a cota (`COTA_PATH`) num diretório do usuário da CLI.
   Confira, como o usuário do agente: `quadro pendencias gabriel` funciona, ler o arquivo de configuração dá "Permission
   denied", escrever no diretório do código dá "Permission denied" e `sudo -n -l` mostra só a regra do `quadro`.
4. **Plugins.** Copie os dois plugins para `~/.hermes/plugins/` com dono root (pastas 755, arquivos 644) e habilite:
   `hermes plugins enable barra-do-robo` e `hermes plugins enable trava-de-saida`. Crie a lista de destinos do `trava-de-saida`
   (dono root, legível pelo usuário do agente, não gravável): uma linha por destino, o JID do grupo (`<id>@g.us`), o LID de cada
   sócio (`<id>@lid`) e os telefones (com e sem o 9º dígito); `#` começa comentário.
5. **Cópias de leitura.** Prepare `/srv/cerebro/{repos,docs}` (ver o cabeçalho de `deploy/atualizar-copias.sh`), instale o script
   e as units `cerebro-copias.{service,timer}` no usuário dono das cópias e ligue o timer (a cada 3 horas).
6. **SOUL, skill, AGENTS.** Copie os arquivos. No `AGENTS.md` instalado troque os placeholders (`<JID do grupo>`, `<LID do Gabriel>`,
   nomes de contato) pelos valores reais, só na máquina.
7. **Os 3 passos do dono:** chave do quadro (abaixo), logins do Codex (`hermes auth add openai-codex`, duas contas diferentes) e
   pareamento do WhatsApp (`hermes whatsapp`, modo `bot`, como segundo aparelho do número da DGC).
8. **Serviço e cron.** `systemctl --user enable --now dgc-cerebro` (com `XDG_RUNTIME_DIR` do usuário do agente) e as rodadas de
   `deploy/cron-jobs.md`.

### Chave do quadro (Paperclip)

A chave de API do quadro (board API key) é da conta do Gabriel, e o `quadro` age como ele. Todo comentário que a CLI posta sai com
`[Hermes via WhatsApp] ` na frente, para ficar claro no quadro que foi o Hermes, não o Gabriel.

1. Logado no Paperclip da DGC, no console do navegador (F12):
   ```js
   fetch('/api/board-api-keys', {method:'POST', headers:{'content-type':'application/json'},
     body: JSON.stringify({name:'cerebro-vm'})}).then(r=>r.json()).then(k=>console.log(k.token, k.expiresAt))
   ```
   O `token` aparece só uma vez; anote `expiresAt` para renovar.
2. Cole o valor depois de `PAPERCLIP_TOKEN=` no arquivo de configuração da CLI, com um editor rodando como root (nunca no chat,
   nunca em comentário, nunca num comando que fique no histórico ou na lista de processos).
3. Teste como o usuário do agente: `quadro pendencias gabriel`.

## Depois de qualquer atualização do Hermes

Os plugins **falham abertos**: se um não carregar (atualização do Hermes, plugin desligado, pasta movida), o Hermes segue
rodando sem a trava, sem erro visível. Depois de qualquer `hermes update`, reinstalação ou mudança de config:

```sh
hermes plugins list | grep -E 'barra-do-robo|trava-de-saida'   # os dois têm de dizer "enabled"
```

e, no log do gateway, `whatsapp connected`. Sem o `barra-do-robo`, o `[SILENT]` do grupo vira mensagem padrão e os "/comandos" do
robô de vendas voltam a ser respondidos; sem o `trava-de-saida`, envio e rotina para fora do grupo deixam de ser barrados.

Também depois de update: a ponte do WhatsApp precisa do `link-preview-js` (o Baileys o importa ao enviar mensagem com URL e o
`package.json` da ponte não o lista). Como o usuário do agente:

```sh
cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge && npm install --no-save link-preview-js@3
```

e reinicie o serviço. `--no-save` não suja o Git do Hermes, mas um update que refaça o `node_modules` apaga o pacote.

## Como o Hermes se comporta (resumo)

- **Grupo dos sócios:** lê toda mensagem e decide pelo contexto. Chamada explícita (@menção, resposta a ele, mensagem começando
  com "hermes") sempre tem resposta; conversa entre os sócios fica em `[SILENT]` (o `barra-do-robo` marca `reply_expected=False`
  para o gateway aceitar o silêncio). Intervenção sem ser chamado: `quadro intervir` (no máximo 1 por hora, dentro do teto de 3
  por dia do grupo).
- **Privado:** sempre responde. O `[SILENT]` só vale no grupo, quando não é com ele, e nas rodadas automáticas.
- **Rodadas e rotinas (cron):** entregam no grupo; qualquer `quadro` com código diferente de 0 vira `[SILENT]`. O `trava-de-saida`
  recusa rotina entregando fora da lista de destinos, mais frequente que de hora em hora, ou com script/monitor.
- **Comandos com "/":** são do robô de vendas; o `barra-do-robo` os descarta antes do Hermes. Por isso o destino do cron é sempre
  explícito (`whatsapp:<JID do grupo>`), nunca `/sethome`.
- **Mensagens do próprio número** (robô via Evolution): a ponte em modo `bot` as descarta (`WHATSAPP_FORWARD_OWNER_MESSAGES`
  desligado; não ligar), e o `barra-do-robo` descarta o que vier marcado como do dono.
