# terceiro-cerebro

Ferramentas em Python 3.12 (só biblioteca padrão) que o Hermes Agent usa, pelo terminal, para ler e agir no
quadro de tarefas (Paperclip) e para respeitar o teto de mensagens espontâneas aos sócios no WhatsApp.

| Arquivo | O que faz |
|---|---|
| `paperclip.py` | cliente da API do quadro; devolve tudo já mascarado |
| `mascarar.py` | esconde tokens, chaves e senhas em qualquer texto |
| `pendencias.py` | junta o que espera cada sócio (bloqueadas, cartões, PAINEL.md) |
| `cota.py` | no máximo 3 mensagens espontâneas por dia por chave (sócio ou `grupo`), entre 08:00 e 21:00 (Brasília), e no máximo 1 intervenção espontânea por hora no grupo |
| `quadro.py` | a CLI `quadro`, que liga tudo isso |

## Instalar

O passo a passo está em `deploy/instalar.md`. Em resumo: o código vai para um diretório do root, só leitura; um wrapper do root
em `/usr/local/bin/quadro` roda `quadro.py` como um usuário de serviço próprio, o único que lê o arquivo de configuração; o
usuário do agente chama esse wrapper por uma regra única de sudo.

Arquivo de configuração (caminho em `CEREBRO_ENV`; padrão `~/.config/dgc-cerebro/cerebro.env`), fora de qualquer Git:

```ini
# chave=valor, uma por linha; # inicia comentário
PAPERCLIP_URL=<endereço do Paperclip>
PAPERCLIP_TOKEN=<chave de API do quadro>
PAPERCLIP_COMPANY=<id da empresa>
PAINEL_PATH=<caminho do PAINEL.md>
COTA_PATH=<caminho do arquivo de cota>
SOCIOS=gabriel:<telefone>,danilo:<telefone>
```

Os telefones ficam só aí e a CLI nunca os imprime. Se `PAINEL_PATH` não existir, o painel conta como vazio.

## Subcomandos

Toda saída é texto curto e já mascarado.

| Comando | Saída |
|---|---|
| `quadro pendencias <socio>` | uma linha por pendência (`DGC-370 · bloqueada · desde 23/11 · título — detalhe`) ou `nada pendente pro <socio>` |
| `quadro tarefa <DGC-n>` | título, status, 3 últimos comentários e cartões abertos com seus ids |
| `quadro comentar <DGC-n> <texto>` | `ok`; o comentário sai com `[Hermes via WhatsApp] ` na frente |
| `quadro status <DGC-n> <status>` | `ok` |
| `quadro aceitar <DGC-n> <interacao> --socio <nome>` | só para cartão `request_confirmation` ou `request_checkbox_confirmation` (fica com as opções que já vêm marcadas): aceita, comenta `[Hermes via WhatsApp] aprovado pelo <Sócio> via WhatsApp, em <dd/mm/aaaa hh:mm>` e imprime `ok`. Outro tipo (perguntas, sugestão de tarefas, veredito, conexão) ou cartão que não está na tarefa: código 3, nada é aceito |
| `quadro aprovar <approval> <DGC-n> --socio <nome>` | aprova, faz o mesmo comentário em `<DGC-n>` e imprime `ok` |
| `quadro cota <socio\|grupo>` | `pode` ou `esgotada` (só consulta) |
| `quadro enviei <socio\|grupo>` | reserva uma mensagem de forma atômica: `pode` (registrou) ou `esgotada` (não registrou) |
| `quadro intervir` | reserva uma intervenção espontânea no grupo: `pode` (registrou a hora e gastou uma das 3 do `grupo`), `espera` (menos de 60 min da última intervenção) ou `esgotada` (teto do dia ou fora da janela); `espera` e `esgotada` não registram |
| `quadro e-comando "<texto>"` | `sim` se o texto começa com `/`, senão `nao` |

`<socio>` precisa ser um dos nomes em `SOCIOS`; sem `SOCIOS` configurado nenhum nome vale (falha fechada). A chave `grupo` (teto do grupo dos
sócios, contado à parte) vale só em `cota` e `enviei`, não como sócio em `pendencias`, `aprovar` nem `aceitar`; também exige `SOCIOS`.
Em `pendencias`, uma tarefa que o quadro recusa ler (4xx) é pulada e a última linha avisa `(<n> tarefas não lidas)`.

### Teto de mensagens (cota)

Rodada automática ou rotina: antes de mandar, `quadro enviei grupo`; só com `pode` a mensagem sai. Intervenção no grupo sem
ninguém ter chamado: `quadro intervir`; só com `pode`. As duas contam no mesmo teto de 3 por dia do `grupo`; a hora da última
intervenção fica à parte (as rodadas não a mexem). `esgotada` quer dizer teto do dia atingido ou fora das 08:00 às 21:00.
Resposta a quem chamou o Hermes não conta.

### Códigos de saída

| Código | Quando | Saída |
|---|---|---|
| 0 | deu certo (inclusive `esgotada`) | |
| 1 | falta configuração (inclui `SOCIOS` vazio), sócio desconhecido ou erro inesperado | mensagem curta (`erro inesperado: <Tipo>`) |
| 2 | quadro fora do ar (ou uso errado) | `quadro fora do ar` (ou uma linha `uso: ...`) |
| 3 | quadro recusou o pedido (4xx), ou `aceitar` num cartão que não é de confirmação simples | `quadro recusou: <detalhe>` ou `cartão do tipo <kind>: ...` |
| 4 | `aprovar`/`aceitar` funcionou, mas o comentário de registro falhou | `aprovado, mas o comentário falhou` (ou `aceito, ...`); não repita a ação |

Nunca aparece stack trace.

## Testes

```sh
cd automations/terceiro-cerebro && python3 -m pytest -q   # inclui os plugins barra-do-robo e trava-de-saida
```
