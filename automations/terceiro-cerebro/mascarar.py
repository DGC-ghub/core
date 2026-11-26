"""Máscara de segredos: tudo que o quadro devolve ao agente passa por aqui."""
import re

SEGREDO = "[segredo]"

# Antes e depois de um token: nada de letra, dígito, "_" ou "-" grudado (evita cortar palavra no meio).
_ANTES = r"(?<![A-Za-z0-9_-])"
_DEPOIS = r"(?![A-Za-z0-9_-])"

# Ordem importa: bloco de chave privada primeiro (engole tudo até o END, ou até o fim se veio cortado);
# "Bearer ..." e JWT antes do hexadecimal solto.
_PADROES = [re.compile(p) for p in (
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----(?:[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----|[\s\S]*)",
    # só mascara "Bearer" seguido de valor com cara de token (16+ caracteres ou com ponto no meio)
    r"(?i:bearer)\s+(?:[A-Za-z0-9._~+/=-]{16,}|[A-Za-z0-9_~+/=-]+\.[A-Za-z0-9._~+/=-]+)",
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    r"sk-ant-[A-Za-z0-9_-]+",
    _ANTES + r"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}",              # OpenAI
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    _ANTES + r"pcp_[A-Za-z0-9_-]{16,}",                                         # chave do Paperclip
    r"(?<![0-9A-Za-z])\d{8,10}:[A-Za-z0-9_-]{35}" + _DEPOIS,                    # bot do Telegram
    r"(?<![0-9A-Z])(?:AKIA|ASIA)[0-9A-Z]{16}(?![0-9A-Za-z])",                   # AWS
    _ANTES + r"AIza[0-9A-Za-z_-]{35}" + _DEPOIS,                                # Google
    _ANTES + r"xox[abposr]-[A-Za-z0-9-]{10,}",                                  # Slack
    r"(?<![A-Za-z0-9])EAA[0-9A-Za-z]{20,}",                                      # Meta (Graph API)
    r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])",
)]


def mascarar(texto: str) -> str:
    for padrao in _PADROES:
        texto = padrao.sub(SEGREDO, texto)
    return texto
