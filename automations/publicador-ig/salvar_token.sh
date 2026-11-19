#!/usr/bin/env bash
# Salva o token do Instagram do @dgc_hub no servidor da DGC sem mostrar na tela nem passar pelo chat.
# Uso (na Pi, num terminal SSH): bash ~/dgc-hub/automations/publicador-ig/salvar_token.sh
set -euo pipefail
SERVIDOR=daniloservi@100.117.24.11
read -rsp "Cole o token do Instagram e tecle Enter (não aparece na tela): " T; echo
[ ${#T} -gt 50 ] || { echo "token curto demais; copie de novo"; exit 1; }
printf 'IG_TOKEN=%s\n' "$T" | ssh "$SERVIDOR" 'umask 077; cat > ~/dgc-ig/.env && printf "{\"renovado_em\": \"%s\"}\n" "$(date +%F)" > ~/dgc-ig/token.json'
unset T
echo "Token salvo. Conferindo a conta:"
ssh "$SERVIDOR" 'cd ~/dgc-ig && python3 publicar_ig.py conta'
