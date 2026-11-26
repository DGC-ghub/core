"""Pendências dos sócios: o que está esperando o Gabriel ou o Danilo no quadro.

Três fontes, todas já lidas pelo chamador (esta função não faz rede):
  - tarefas bloqueadas cujo último comentário diz que esperam um sócio;
  - cartões (interações) abertos, que hoje só a conta do Gabriel responde;
  - itens abertos do PAINEL.md, nas seções "Precisa do Gabriel/Danilo".
"""
import re
from dataclasses import dataclass
from datetime import datetime, timezone

SOCIOS = ("gabriel", "danilo")
TITULO_MAX = 120

_ESPERA = re.compile(
    r"\b(esperando|espera|depende|falta|aguard\w*|waiting for|ask)\W+(o |a |do |da )?(gabriel|danilo)\b",
    re.IGNORECASE,
)
_ITEM = re.compile(r"^\d+[a-z]?\.\s+(.*\S)\s*$")
_REF = re.compile(r"DGC-\d+")


@dataclass
class Pendencia:
    socio: str
    origem: str  # "cartao", "bloqueada" ou "painel"
    ref: str
    titulo: str
    desde: str
    detalhe: str


def _cortar(texto, limite: int = TITULO_MAX) -> str:
    texto = " ".join(str(texto or "").split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def _da_bloqueada(socio, issue, comentarios):
    if not comentarios:
        return None
    ultimo = comentarios[0]  # a lista vem do mais novo para o mais velho
    corpo = ultimo.get("body") or ""
    for achado in _ESPERA.finditer(corpo):
        if achado.group(3).lower() == socio:
            return Pendencia(
                socio=socio,
                origem="bloqueada",
                ref=issue.get("identifier") or "",
                titulo=_cortar(issue.get("title") or ""),
                desde=ultimo.get("createdAt") or "",
                detalhe=_cortar(corpo, 300),
            )
    return None


def _do_cartao(socio, issue, cartao):
    if socio != "gabriel" or cartao.get("status") != "pending":
        return None
    return Pendencia(
        socio=socio,
        origem="cartao",
        ref=issue.get("identifier") or "",
        titulo=_cortar(cartao.get("title") or issue.get("title") or ""),
        desde=cartao.get("createdAt") or "",
        detalhe=_cortar(cartao.get("summary") or "", 300),
    )


def _do_painel(socio, painel_md):
    cabecalho = f"## precisa do {socio}"
    dentro = False
    for linha in painel_md.splitlines():
        if linha.startswith("## "):
            dentro = linha.lower().startswith(cabecalho)
            continue
        if not dentro:
            continue
        item = _ITEM.match(linha)  # sem recuo: linhas recuadas continuam o item anterior
        if not item or "✅" in item.group(1):
            continue
        texto = item.group(1)
        achado = _REF.search(texto)
        yield Pendencia(
            socio=socio,
            origem="painel",
            ref=achado.group(0) if achado else "",
            titulo=_cortar(texto),
            desde="",
            detalhe="",
        )


def _chave_de_ordem(p: Pendencia):
    """Datadas da mais antiga para a mais nova; sem data (painel) por último."""
    try:
        quando = datetime.fromisoformat(p.desde)
        if quando.tzinfo is None:
            quando = quando.replace(tzinfo=timezone.utc)
        return (0, quando)
    except (ValueError, TypeError):  # data ausente, vazia ou de tipo estranho: vai para o fim
        return (1, datetime.max.replace(tzinfo=timezone.utc))


def pendencias_do_socio(socio, bloqueadas, cartoes, painel_md):
    """Pendências de `socio` ("gabriel" ou "danilo"), da mais antiga para a mais nova.

    bloqueadas: [(issue, comentarios_do_mais_novo_ao_mais_velho)]
    cartoes: [(issue, interacao)]
    painel_md: texto do PAINEL.md ("" se não houver).
    """
    achadas = []
    for issue, comentarios in bloqueadas:
        p = _da_bloqueada(socio, issue, comentarios)
        if p:
            achadas.append(p)
    for issue, cartao in cartoes:
        p = _do_cartao(socio, issue, cartao)
        if p:
            achadas.append(p)
    achadas.extend(_do_painel(socio, painel_md or ""))
    return sorted(achadas, key=_chave_de_ordem)  # sorted é estável: o painel mantém a ordem
