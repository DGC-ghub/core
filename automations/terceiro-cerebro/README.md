# terceiro-cerebro

Ferramentas em Python 3.12 (só biblioteca padrão) que o Hermes Agent usa, pelo terminal, para ler e agir no
quadro de tarefas (Paperclip) e para respeitar o teto de mensagens espontâneas aos sócios no WhatsApp.

| Arquivo | O que faz |
|---|---|
| `paperclip.py` | cliente da API do quadro; devolve tudo já mascarado |
| `mascarar.py` | esconde tokens, chaves e senhas em qualquer texto |
| `pendencias.py` | junta o que espera cada sócio (bloqueadas, cartões, PAINEL.md) |
| `cota.py` | no máximo 3 mensagens por dia por sócio, entre 08:00 e 21:00 (Brasília) |
| `quadro.py` | a CLI `quadro`, que liga tudo isso |

## Instalar na VM

1. Copie esta pasta para a VM (por exemplo em `<PASTA>/terceiro-cerebro`).
2. Crie o wrapper `quadro` num diretório do PATH:

   ```sh
   #!/bin/sh
   exec python3 <PASTA>/terceiro-cerebro/quadro.py "$@"
   ```

   e torne-o executável (`chmod +x`).
3. Crie `~/.config/dgc-cerebro/cerebro.env` (permissão 600, fora de qualquer Git):

   ```ini
   # chave=valor, uma por linha; # inicia comentário
   PAPERCLIP_URL=<endereço do Paperclip>
   PAPERCLIP_TOKEN=<chave de API do quadro>
   PAPERCLIP_COMPANY=<id da empresa>
   PAINEL_PATH=<caminho do PAINEL.md>
   COTA_PATH=<caminho do arquivo de cota, ex.: ~/.config/dgc-cerebro/cota.json>
   SOCIOS=gabriel:<telefone>,danilo:<telefone>
   ```

   O caminho do arquivo pode ser trocado com a variável de ambiente `CEREBRO_ENV`. Os telefones ficam só aí e
   a CLI nunca os imprime. Se `PAINEL_PATH` não existir, o painel conta como vazio.

## Subcomandos

Toda saída é texto curto e já mascarado.

| Comando | Saída |
|---|---|
| `quadro pendencias <socio>` | uma linha por pendência (`DGC-370 · bloqueada · desde 23/11 · título — detalhe`) ou `nada pendente pro <socio>` |
| `quadro tarefa <DGC-n>` | título, status, 3 últimos comentários e cartões abertos com seus ids |
| `quadro comentar <DGC-n> <texto>` | `ok` |
| `quadro status <DGC-n> <status>` | `ok` |
| `quadro aceitar <DGC-n> <interacao> --socio <nome>` | aceita o cartão, comenta `aprovado pelo <Sócio> via WhatsApp, em <dd/mm/aaaa hh:mm>` e imprime `ok` |
| `quadro aprovar <approval> <DGC-n> --socio <nome>` | aprova, faz o mesmo comentário em `<DGC-n>` e imprime `ok` |
| `quadro cota <socio\|grupo>` | `pode` ou `esgotada` (só consulta) |
| `quadro enviei <socio\|grupo>` | reserva uma mensagem de forma atômica: `pode` (registrou) ou `esgotada` (não registrou) |
| `quadro e-comando "<texto>"` | `sim` se o texto começa com `/`, senão `nao` |

`<socio>` precisa ser um dos nomes em `SOCIOS`; sem `SOCIOS` configurado nenhum nome vale (falha fechada). A chave `grupo` (teto do grupo dos
sócios, contado à parte) vale só em `cota` e `enviei`, não como sócio em `pendencias`, `aprovar` nem `aceitar`; também exige `SOCIOS`.
Em `pendencias`, uma tarefa que o quadro recusa ler (4xx) é pulada e a última linha avisa `(<n> tarefas não lidas)`.

### Regra da barra (cota)

Antes de mandar uma mensagem espontânea a um sócio, o Hermes roda `quadro enviei <socio>`. Só se vier `pode` ele
envia; `esgotada` quer dizer que o teto do dia foi atingido ou que está fora da janela das 08:00 às 21:00. Resposta
a um comando do sócio (texto que começa com `/`, veja `quadro e-comando`) não conta como espontânea.

### Códigos de saída

| Código | Quando | Saída |
|---|---|---|
| 0 | deu certo (inclusive `esgotada`) | |
| 1 | falta configuração (inclui `SOCIOS` vazio), sócio desconhecido ou erro inesperado | mensagem curta (`erro inesperado: <Tipo>`) |
| 2 | quadro fora do ar (ou uso errado) | `quadro fora do ar` (ou uma linha `uso: ...`) |
| 3 | quadro recusou o pedido (4xx) | `quadro recusou: <detalhe>` |
| 4 | `aprovar`/`aceitar` funcionou, mas o comentário de registro falhou | `aprovado, mas o comentário falhou` (ou `aceito, ...`); não repita a ação |

Nunca aparece stack trace.

## Testes

```sh
cd automations/terceiro-cerebro && python3 -m pytest -q
```
