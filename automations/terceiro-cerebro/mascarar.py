"""Máscara de segredos: tudo que o quadro devolve ao agente passa por aqui."""
import re

SEGREDO = "[segredo]"

# Ordem importa: "Bearer ..." e JWT antes do hexadecimal solto.
_PADROES = [re.compile(p) for p in (
    r"Bearer\s+[A-Za-z0-9._~+/=-]+",
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    r"sk-ant-[A-Za-z0-9_-]+",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"\b[0-9a-fA-F]{32,}\b",
)]


def mascarar(texto: str) -> str:
    for padrao in _PADROES:
        texto = padrao.sub(SEGREDO, texto)
    return texto
