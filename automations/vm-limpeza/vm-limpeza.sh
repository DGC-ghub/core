#!/usr/bin/env bash
# Limpeza diária do disco da VM trabalhadora (DGC-497). Sem IA, sem custo.
# Padrão é ENSAIO: só lista o que apagaria e o tamanho. Para apagar de verdade: --aplicar.
#   vm-limpeza.sh [--aplicar] [--forcar-caches]
# Regras:
#   1. /tmp: só o que é do usuário atual, sem modificação há mais de TMP_DIAS (3) dias
#      (pasta: nada dentro modificado nesse prazo), sem processo com cwd/arquivo aberto dentro
#      e sem ponto de montagem dentro. Entradas que começam com "." são ignoradas.
#   2. Pastas de run do Paperclip: NÃO é feito aqui. O ~/bin/limpa-runs.sh (cron, de hora em hora)
#      já apaga run parado há 2 h e sem processo. Ver docs.
#   3. Journal: limite fixo em journald.conf (precisa de root, ver docs). Aqui só se confere.
#   4. Caches regeneráveis (npm, pip, node-gyp): no máx. 1 vez por semana. O store do pnpm NÃO entra (DGC-249).
#   5. Alerta de 85%: já é do vigia-disco.sh (a cada 10 min). Aqui só se imprime o uso.
# Nunca toca: /home/cerebro, /srv/cerebro, /etc/dgc-cerebro, ~/apps, volumes do Docker, ~/hermes-piloto.
set -u
APLICAR=0; FORCAR=0
for a in "$@"; do case "$a" in
  --aplicar) APLICAR=1 ;; --forcar-caches) FORCAR=1 ;;
  -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
  *) echo "argumento desconhecido: $a" >&2; exit 2 ;; esac; done

TMP_DIR=${LIMPEZA_TMP_DIR:-/tmp}
TMP_DIAS=${LIMPEZA_TMP_DIAS:-3}
CACHE_DIAS=${LIMPEZA_CACHE_DIAS:-7}
STATE=${LIMPEZA_STATE:-$HOME/.local/state/vm-limpeza.caches}
PROC_DIR=${LIMPEZA_PROC:-/proc}
MOUNTINFO=${LIMPEZA_MOUNTINFO:-/proc/self/mountinfo}
CACHES=(${LIMPEZA_CACHES:-"$HOME/.npm/_cacache" "$HOME/.cache/npm" "$HOME/.cache/pip" "$HOME/.cache/node-gyp" "$HOME/.node-gyp"})
# Lista de proteção: nunca apagar nada que seja ou esteja dentro disto (defesa extra).
PROTEGIDOS=(/home/cerebro /srv/cerebro /etc/dgc-cerebro "$HOME/apps" "$HOME/hermes-piloto" /var/lib/docker "$HOME/.cache/pnpm")

mkdir -p "$(dirname "$STATE")"
exec 9>"${LIMPEZA_LOCK:-$HOME/.local/state/vm-limpeza.lock}"; flock -n 9 || { echo "já em execução"; exit 0; }

modo=ENSAIO; [ $APLICAR = 1 ] && modo=APLICAR
echo "== vm-limpeza $(date -u +%FT%TZ) modo=$modo"
echo "disco antes: $(df -h --output=pcent,avail / | tail -1 | tr -s ' ')"

total=0; n=0
humano() { numfmt --to=iec --suffix=B "${1:-0}" 2>/dev/null || echo "${1:-0}B"; }

protegido() { # $1 caminho real
  local p
  for p in "${PROTEGIDOS[@]}"; do [[ "$1" == "$p" || "$1" == "$p"/* ]] && return 0; done; return 1
}

# Caminhos em uso: cwd e arquivos abertos de qualquer processo que a gente consiga ler.
EM_USO=$(mktemp); trap 'rm -f "$EM_USO"' EXIT
for p in "$PROC_DIR"/[0-9]*; do
  readlink "$p/cwd" 2>/dev/null
  for f in "$p"/fd/*; do readlink "$f" 2>/dev/null; done
done | grep '^/' | sort -u > "$EM_USO"
# Sockets Unix em uso: o fd aparece como socket:[inode], então lemos os caminhos em /proc/net/unix.
awk 'NR>1 && $NF ~ /^\// {print $NF}' "${LIMPEZA_UNIX:-/proc/net/unix}" 2>/dev/null | sort -u >> "$EM_USO"

em_uso() { # $1 = caminho (arquivo ou pasta)
  awk -v d="$1" '$0==d || index($0, d "/")==1 {f=1; exit} END{exit !f}' "$EM_USO"
}
tem_montagem() { # $1 = pasta; há ponto de montagem nela ou dentro?
  awk -v d="$1" '{m=$5; gsub(/\\040/," ",m); if (m==d || index(m, d "/")==1) {f=1; exit}} END{exit !f}' "$MOUNTINFO"
}
tamanho() { du -sb --apparent-size -- "$1" 2>/dev/null | cut -f1; }

apagar() { # $1 caminho, $2 motivo
  local t; t=$(tamanho "$1"); t=${t:-0}
  total=$((total+t)); n=$((n+1))
  if [ $APLICAR = 1 ]; then
    rm -rf --one-file-system -- "$1" && echo "APAGADO  $(humano "$t")  $1  ($2)"
  else
    echo "APAGARIA $(humano "$t")  $1  ($2)"
  fi
}

echo "-- 1. $TMP_DIR (do usuário $(id -un), > ${TMP_DIAS} dias, fora de uso)"
tmp_real=$(readlink -f "$TMP_DIR")
while IFS= read -r -d '' e; do
  b=${e##*/}
  case "$b" in .*|vm-limpeza*|limpa-runs.lock) continue ;; esac
  real=$(readlink -f "$e"); protegido "$real" && { echo "PULADO   protegido  $e"; continue; }
  if [ -L "$e" ]; then # link: só o link, se velho
    [ -n "$(find "$e" -maxdepth 0 -mtime -"$TMP_DIAS" -print)" ] && continue
    apagar "$e" "link antigo"; continue
  fi
  # recente: o próprio item ou (se pasta) qualquer coisa dentro modificada no prazo
  [ -n "$(find "$e" -mtime -"$TMP_DIAS" -print -quit 2>/dev/null)" ] && continue
  [ -d "$e" ] && tem_montagem "$real" && { echo "PULADO   ponto de montagem  $e"; continue; }
  em_uso "$real" && { echo "PULADO   em uso  $e"; continue; }
  apagar "$e" "sem mudança há >${TMP_DIAS}d"
done < <(find "$tmp_real" -mindepth 1 -maxdepth 1 -user "$(id -un)" -print0)
tmp_total=$total; echo "   subtotal /tmp: $(humano "$tmp_total")"

echo "-- 3. journal"
echo "   uso atual: $(journalctl --disk-usage 2>/dev/null | grep -o '[0-9.]*[KMG]' | tail -1)"
if grep -rhs '^SystemMaxUse=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d/ 2>/dev/null | tail -1 | grep -q .; then
  echo "   limite configurado: $(grep -rhs '^SystemMaxUse=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d/ | tail -1)"
else
  echo "   AVISO: sem SystemMaxUse em journald.conf (precisa de root; ver docs/vm-limpeza-disco.md)"
fi

echo "-- 4. caches regeneráveis (semanal)"
agora=$(date +%s); ultimo=$(cat "$STATE" 2>/dev/null || echo 0)
if [ $FORCAR = 1 ] || [ $((agora-ultimo)) -ge $((CACHE_DIAS*86400)) ]; then
  if pgrep -u "$(id -u)" -f '(^|/)(npm|pnpm|pip3?|node-gyp)( |$)' >/dev/null 2>&1; then
    echo "   PULADO: npm/pnpm/pip em execução agora"
  else
    for c in "${CACHES[@]}"; do
      [ -e "$c" ] || continue
      real=$(readlink -f "$c"); protegido "$real" && { echo "PULADO   protegido  $c"; continue; }
      apagar "$c" "cache regenerável"
    done
    [ $APLICAR = 1 ] && echo "$agora" > "$STATE"
  fi
else
  echo "   pulado: última limpeza há $(( (agora-ultimo)/86400 )) dia(s) (< ${CACHE_DIAS})"
fi

echo "== itens: $n  total $( [ $APLICAR = 1 ] && echo apagado || echo 'que seria apagado'): $(humano "$total")"
echo "disco depois: $(df -h --output=pcent,avail / | tail -1 | tr -s ' ')"
