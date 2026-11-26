"""Máscara de segredos: tudo que o quadro devolve ao agente passa por aqui."""
import re

SEGREDO = "[segredo]"

# Ordem importa: "Bearer ..." e JWT antes do hexadecimal solto.
_PADROES = [re.compile(p) for p in (
    # só mascara "Bearer" seguido de valor com cara de token (16+ caracteres ou com ponto no meio)
    r"(?i:bearer)\s+(?:[A-Za-z0-9._~+/=-]{16,}|[A-Za-z0-9_~+/=-]+\.[A-Za-z0-9._~+/=-]+)",
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    r"sk-ant-[A-Za-z0-9_-]+",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])",
)]


def mascarar(texto: str) -> str:
    for padrao in _PADROES:
        texto = padrao.sub(SEGREDO, texto)
    return texto
