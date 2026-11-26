#!/usr/bin/env bash
# Atualiza as cópias de LEITURA que o terceiro cérebro (usuário "cerebro") consulta.
# Roda como o usuário "dgc" (timer de usuário cerebro-copias.timer); o "cerebro" só lê.
#
#   /srv/cerebro/repos/<nome>   clone parcial (só leitura) de cada repositório da DGC
#   /srv/cerebro/docs/          cópia dos documentos da cópia de trabalho dos agentes
#
# Os clones são parciais (--filter=blob:none) com sparse-checkout aplicado ANTES do checkout: o conteúdo do que fica de
# fora (.env, chaves, cofre...) nunca é baixado, nem do histórico. Quem lê a cópia não consegue buscar o que falta: o
# .git é do dono das cópias e não aceita escrita de quem só lê.
#
# Preparação única (como root, ver deploy/instalar.md):
#   mkdir -p /srv/cerebro/repos /srv/cerebro/docs
#   chown -R dgc:cerebro /srv/cerebro && chmod 2750 /srv/cerebro /srv/cerebro/repos /srv/cerebro/docs
# O dgc NÃO entra no grupo cerebro; o script usa "sudo -n chgrp/chmod" no fim de cada rodada.
set -uo pipefail
umask 027

DEST="${CEREBRO_COPIAS:-/srv/cerebro}"
ORG="${CEREBRO_ORG:-DGC-ghub}"
RUNS="${CEREBRO_RUNS:-$HOME/paperclip/.paperclip-runtime/runs}"
REPOS=(produto-hermes day-trade-app dgc-reels core dgc-ai-desk Vitrine_DGC dgc-template-ts)

# O que nunca entra na cópia (nem nos repositórios, nem nos documentos).
EXCLUIR=('.env*' '*.env' '*.pem' '*.key' 'node_modules/' '.git/' '*.db' '*.sqlite' '**/pacientes/**' '**/conversas/**'
         '*cofre*' '*saldo*' '*carteira*' '*wallet*' '*vault*')
# Padrão que a trava final procura, e o padrão estrito (chave de verdade, não código que apenas a detecta). Mesma família
# do mascarar.py: Anthropic, GitHub, OpenAI, bloco de chave privada, AWS, Google, Slack, Meta, Paperclip e bot do Telegram.
LONGOS='(^|[^A-Za-z0-9_-])sk-(proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----'
LONGOS+='|(^|[^A-Za-z0-9])(AKIA|ASIA)[0-9A-Z]{16}([^A-Za-z0-9]|$)|(^|[^A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}'
LONGOS+='|(^|[^A-Za-z0-9_-])xox[abposr]-[A-Za-z0-9-]{10,}|(^|[^A-Za-z0-9+/])EAA[0-9A-Za-z]{20,}'
LONGOS+='|(^|[^A-Za-z0-9_-])pcp_[A-Za-z0-9_-]{16,}|(^|[^0-9A-Za-z])[0-9]{8,10}:[A-Za-z0-9_-]{35}([^A-Za-z0-9_-]|$)'
PADRAO="sk-ant-|ghp_|github_pat_|$LONGOS"
ESTRITO="sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|$LONGOS"
# Arquivo de teste com chave de mentira (fixture) sai da cópia, mas não vira ERRO.
e_teste() { case "$1" in */test_*|*_test.*|*.test.*|*.spec.*|*/tests/*|*/test/*|*/fixtures/*|*/__tests__/*) return 0 ;; esac; return 1; }
# Arquivos tirados do checkout por parecerem segredo ficam anotados aqui (pasta do dono das cópias, fora de $DEST): o
# clone seguinte já nasce sem eles.
ESTADO="${CEREBRO_COPIAS_ESTADO:-$HOME/.local/state/cerebro-copias}"
mkdir -p "$ESTADO"
# Mesmo filtro para o checkout dos repositórios (sparse-checkout, estilo .gitignore, vale em qualquer profundidade).
SPARSE=('/*' '!.env*' '!*.env' '!*.pem' '!*.key' '!node_modules/' '!*.db' '!*.sqlite' '!pacientes/' '!conversas/')

# O acesso ao GitHub é o que o dgc já tem (credential.helper store, renovado pela própria VM). A chave SSH
# ~/.ssh/id_github_trabalhadora não tem mais acesso. Nenhum segredo é gravado nas cópias: a URL guardada no clone não tem token.
export GIT_TERMINAL_PROMPT=0
# Frente de trade (day-trade-app, dgc-ai-desk): Mesa BTC e Laboratório são simulação e podem ser lidos; cofre, chaves e
# saldos reais não. Qualquer arquivo ou pasta com esses nomes sai do checkout (em 26/11 não havia nenhum, é preventivo).
SPARSE_TRADE=('!*cofre*' '!*vault*' '!*saldo*' '!*carteira*' '!*wallet*')
sparse_do_repo() {  # imprime um padrão por linha: o filtro geral e, nos repos de trade, o filtro do cofre
  printf '%s\n' "${SPARSE[@]}"
  case "$1" in day-trade-app|dgc-ai-desk) printf '%s\n' "${SPARSE_TRADE[@]}" ;; esac
}
erros=0
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }

[ -d "$DEST/repos" ] && [ -d "$DEST/docs" ] || { log "ERRO: $DEST/repos e $DEST/docs precisam existir (veja o cabeçalho)"; exit 1; }

# 1. Repositórios
padroes_do_repo() {  # filtro geral + filtro do cofre + o que já foi tirado por parecer segredo
  sparse_do_repo "$1"
  [ -f "$ESTADO/$1.extras" ] && cat "$ESTADO/$1.extras"
}

clonar() {  # clone parcial novo, sparse antes do checkout; troca a pasta antiga só se tudo deu certo
  local nome="$1" pasta="$2" novo="$2.novo"
  rm -rf "$novo"
  git clone --quiet --filter=blob:none --no-checkout "https://github.com/$ORG/$nome.git" "$novo" || { rm -rf "$novo"; return 1; }
  git -C "$novo" config core.fileMode false
  git -C "$novo" remote set-url --push origin no_push
  mapfile -t padroes < <(padroes_do_repo "$nome")
  if ! git -C "$novo" sparse-checkout set --no-cone "${padroes[@]}" || ! git -C "$novo" checkout --quiet; then
    rm -rf "$novo"; return 1
  fi
  rm -rf "$pasta" && mv "$novo" "$pasta"
}

parcial() { [ "$(git -C "$1" config --get remote.origin.partialclonefilter 2>/dev/null)" = "blob:none" ]; }

for nome in "${REPOS[@]}"; do
  pasta="$DEST/repos/$nome"
  if [ ! -d "$pasta/.git" ] || ! parcial "$pasta"; then
    # sem clone, ou clone antigo completo (com o conteúdo de tudo no .git): clona de novo, parcial
    log "clonando $nome (parcial)"
    clonar "$nome" "$pasta" || { log "ERRO: clone de $nome falhou"; erros=$((erros+1)); }
  else
    mapfile -t padroes < <(padroes_do_repo "$nome")
    git -C "$pasta" sparse-checkout set --no-cone "${padroes[@]}" 2>/dev/null
    if git -C "$pasta" pull --quiet --ff-only; then
      log "ok $nome"
    else
      log "ERRO: pull de $nome falhou (não é avanço simples?)"; erros=$((erros+1))
    fi
  fi
  # Cópia só de leitura: nenhum push sai daqui.
  git -C "$pasta" remote set-url --push origin no_push 2>/dev/null
done

# 1b. Arquivo de repositório que casa com o padrão de segredo sai do checkout (o cérebro não o vê) e fica anotado; como o
# conteúdo já foi baixado para o .git, o repositório é clonado de novo sem ele. Se for chave de verdade, vira ERRO; se for
# só código que detecta chaves (regex) ou teste com chave de mentira, fica só fora da cópia.
for nome in "${REPOS[@]}"; do
  pasta="$DEST/repos/$nome"
  [ -d "$pasta/.git" ] || continue
  novos=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rel="${f#$pasta/}"
    if grep -qIE "$ESTRITO" "$f" && ! e_teste "/$rel"; then
      log "ERRO: chave de verdade em repos/$nome/$rel (tirada da cópia; avisar o dono do repositório)"; erros=$((erros+1))
    else
      log "aviso: repos/$nome/$rel tirado da cópia (parece segredo, é só código que procura segredo ou teste)"
    fi
    grep -qxF "!/$rel" "$ESTADO/$nome.extras" 2>/dev/null || { printf '%s\n' "!/$rel" >> "$ESTADO/$nome.extras"; novos=1; }
  done < <(grep -rlIE "$PADRAO" --exclude-dir=.git "$pasta" 2>/dev/null)
  if [ "$novos" -eq 1 ]; then
    log "clonando $nome de novo, sem os arquivos tirados"
    clonar "$nome" "$pasta" || { log "ERRO: novo clone de $nome falhou"; erros=$((erros+1)); }
  fi
done

# 2. Documentos: cópia de trabalho mais recente dos agentes (tem docs/foco/PAINEL.md); senão, o clone do core.
origem=""
if [ -d "$RUNS" ]; then
  for w in $(ls -td "$RUNS"/*/workspace 2>/dev/null); do
    if [ -f "$w/docs/foco/PAINEL.md" ]; then origem="$w/docs"; break; fi
  done
fi
if [ -z "$origem" ] && [ -d "$DEST/repos/core/docs" ]; then
  origem="$DEST/repos/core/docs"
  log "aviso: sem cópia de trabalho dos agentes; usando repos/core/docs"
fi
if [ -n "$origem" ]; then
  args=()
  for e in "${EXCLUIR[@]}"; do args+=(--exclude="$e"); done
  log "docs de $origem"
  if ! rsync -rlt --delete --delete-excluded --no-group --no-owner --no-perms "${args[@]}" "$origem/" "$DEST/docs/"; then
    log "ERRO: rsync dos documentos falhou"; erros=$((erros+1))
  fi
else
  log "ERRO: nenhuma origem de documentos encontrada"; erros=$((erros+1))
fi

# 3. Permissões: dono dgc, grupo cerebro, pastas 750 e arquivos 640, nada para os outros. O dgc não pertence ao grupo
# cerebro (de propósito), então o chgrp e o chmod passam pelo sudo sem senha que o dgc já tem.
sudo -n chgrp -Rh cerebro "$DEST" || { log "ERRO: chgrp falhou"; erros=$((erros+1)); }
sudo -n find "$DEST" -type d ! -perm 750 ! -perm 2750 -exec chmod 750 {} +
sudo -n find "$DEST" -type f ! -perm 640 -exec chmod 640 {} +

# 4. Última trava: nada que pareça chave pode ficar nas cópias (não imprime o conteúdo, só o nome do arquivo).
achados=$(grep -rlIE "$PADRAO" --exclude-dir=.git "$DEST" 2>/dev/null)
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    "$DEST/docs/"*) rm -f -- "$f"; log "aviso: removido de docs/ por parecer segredo: ${f#$DEST/}" ;;
    *) log "ERRO: possível segredo em ${f#$DEST/} (revisar no repositório)"; erros=$((erros+1)) ;;
  esac
done <<< "$achados"

log "fim, erros=$erros"
[ "$erros" -eq 0 ]
