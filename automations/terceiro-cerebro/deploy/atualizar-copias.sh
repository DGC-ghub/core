#!/usr/bin/env bash
# Atualiza as cópias de LEITURA que o terceiro cérebro (usuário "cerebro") consulta.
# Roda como o usuário "dgc" (timer de usuário cerebro-copias.timer); o "cerebro" só lê.
#
#   /srv/cerebro/repos/<nome>   clone (só leitura) de cada repositório da DGC
#   /srv/cerebro/docs/          cópia dos documentos da cópia de trabalho dos agentes
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
EXCLUIR=('.env*' '*.env' '*.pem' '*.key' 'node_modules/' '.git/' '*.db' '*.sqlite' '**/pacientes/**' '**/conversas/**')
# Padrão que a trava final procura, e o padrão estrito (chave de verdade, não código que apenas a detecta).
PADRAO='sk-ant-|ghp_|github_pat_'
ESTRITO='sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}'
# Mesmo filtro para o checkout dos repositórios (sparse-checkout, estilo .gitignore, vale em qualquer profundidade).
SPARSE=('/*' '!.env*' '!*.env' '!*.pem' '!*.key' '!node_modules/' '!*.db' '!*.sqlite' '!pacientes/' '!conversas/')

# O acesso ao GitHub é o que o dgc já tem (credential.helper store, renovado pela própria VM). A chave SSH
# ~/.ssh/id_github_trabalhadora não tem mais acesso. Nenhum segredo é gravado nas cópias: a URL guardada no clone não tem token.
export GIT_TERMINAL_PROMPT=0
erros=0
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }

[ -d "$DEST/repos" ] && [ -d "$DEST/docs" ] || { log "ERRO: $DEST/repos e $DEST/docs precisam existir (veja o cabeçalho)"; exit 1; }

# 1. Repositórios
for nome in "${REPOS[@]}"; do
  pasta="$DEST/repos/$nome"
  if [ ! -d "$pasta/.git" ]; then
    log "clonando $nome"
    if ! git clone --quiet --no-checkout "https://github.com/$ORG/$nome.git" "$pasta"; then
      log "ERRO: clone de $nome falhou"; erros=$((erros+1)); rm -rf "$pasta"; continue
    fi
    git -C "$pasta" config core.fileMode false
    git -C "$pasta" sparse-checkout set --no-cone "${SPARSE[@]}"
    git -C "$pasta" checkout --quiet || { log "ERRO: checkout de $nome falhou"; erros=$((erros+1)); }
  else
    git -C "$pasta" config core.fileMode false
    git -C "$pasta" sparse-checkout set --no-cone "${SPARSE[@]}" 2>/dev/null
    if git -C "$pasta" pull --quiet --ff-only; then
      log "ok $nome"
    else
      log "ERRO: pull de $nome falhou (não é avanço simples?)"; erros=$((erros+1))
    fi
  fi
  # Cópia só de leitura: nenhum push sai daqui.
  git -C "$pasta" remote set-url --push origin no_push 2>/dev/null
done

# 1b. Arquivo de repositório que casa com o padrão de segredo sai do checkout (o cérebro não o vê). Se for chave de
# verdade, vira ERRO; se for só código que detecta chaves (regex), fica só fora da cópia.
for nome in "${REPOS[@]}"; do
  pasta="$DEST/repos/$nome"
  [ -d "$pasta/.git" ] || continue
  extras=()
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rel="${f#$pasta/}"
    extras+=("!/$rel")
    if grep -qIE "$ESTRITO" "$f"; then
      log "ERRO: chave de verdade em repos/$nome/$rel (tirada da cópia; avisar o dono do repositório)"; erros=$((erros+1))
    else
      log "aviso: repos/$nome/$rel tirado da cópia (parece segredo, é só código que procura segredo)"
    fi
  done < <(grep -rlIE "$PADRAO" --exclude-dir=.git "$pasta" 2>/dev/null)
  if [ "${#extras[@]}" -gt 0 ]; then
    git -C "$pasta" sparse-checkout set --no-cone "${SPARSE[@]}" "${extras[@]}"
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
