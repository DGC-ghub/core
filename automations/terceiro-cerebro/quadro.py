#!/usr/bin/env python3
"""quadro: CLI do Hermes para ler e agir no quadro de tarefas (Paperclip) e respeitar o teto
de mensagens espontâneas aos sócios.

Pensada para o terminal do agente: saída em texto curto, simples e já mascarada. Só biblioteca padrão.

Subcomandos:
  quadro pendencias <socio>                          o que espera esse sócio, uma linha por item
  quadro tarefa <DGC-n>                              título, status, 3 últimos comentários, cartões abertos
  quadro comentar <DGC-n> <texto>
  quadro status <DGC-n> <status>
  quadro aceitar <DGC-n> <interacao> --socio <nome>  aceita o cartão e comenta quem aprovou
  quadro aprovar <approval> <DGC-n> --socio <nome>   aprova e comenta quem aprovou
  quadro cota <socio|grupo>                          "pode" ou "esgotada" (só leitura)
  quadro enviei <socio|grupo>                        reserva uma mensagem: "pode" (registrou) ou "esgotada"
  quadro e-comando "<texto>"                         "sim" se o texto começa com "/", senão "nao"

Códigos de saída: 0 ok; 1 configuração ou sócio inválido; 2 quadro fora do ar (ou uso errado);
3 quadro recusou o pedido; 4 aprovou/aceitou mas o comentário falhou (não repetir a ação).

Configuração: ~/.config/dgc-cerebro/cerebro.env (ou o caminho em CEREBRO_ENV), linhas CHAVE=VALOR:
  PAPERCLIP_URL, PAPERCLIP_TOKEN, PAPERCLIP_COMPANY, PAINEL_PATH, COTA_PATH, SOCIOS=nome:telefone,nome:telefone
Os telefones nunca são impressos.
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from cota import FUSO, Cota
from mascarar import mascarar
from paperclip import Paperclip, QuadroForaDoAr, QuadroRecusou
from pendencias import pendencias_do_socio

ENV_PADRAO = Path("~/.config/dgc-cerebro/cerebro.env")
COTA_PADRAO = Path("~/.config/dgc-cerebro/cota.json")
ESTADOS_COM_CARTAO = ["blocked", "in_review", "in_progress", "todo"]
DETALHE_NA_LINHA = 160
COMENTARIO_NA_TAREFA = 300


class ErroDeUso(Exception):
    """Configuração ou argumento inválido (saída 1)."""


def e_comando(texto: str) -> bool:
    return texto.strip().startswith("/")


def ler_env(caminho: Path) -> dict:
    """Lê linhas CHAVE=VALOR, ignorando vazias e comentários (#)."""
    valores = {}
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip()
    return valores


def _carregar_config() -> dict:
    caminho = Path(os.environ.get("CEREBRO_ENV") or ENV_PADRAO).expanduser()
    try:
        return ler_env(caminho)
    except (OSError, ValueError):  # ValueError cobre UnicodeDecodeError
        raise ErroDeUso("quadro sem configuração: arquivo cerebro.env não encontrado") from None


def _nomes_dos_socios(config: dict) -> list[str]:
    bruto = config.get("SOCIOS", "")
    nomes = [item.partition(":")[0].strip().lower() for item in bruto.split(",") if item.strip()]
    return nomes


def _socio(config: dict, nome: str) -> str:
    nome = nome.strip().lower()
    validos = _nomes_dos_socios(config)
    if not validos:  # falha fechada: sem lista de sócios configurada, nenhum nome vale
        raise ErroDeUso("falta SOCIOS no cerebro.env")
    if nome not in validos:
        raise ErroDeUso(f"sócio desconhecido: {mascarar(nome)[:40]} (use: {', '.join(validos)})")
    return nome


GRUPO = "grupo"  # chave de cota do grupo dos sócios: vale só em `cota` e `enviei`, nunca como sócio


def _chave_de_cota(config: dict, nome: str) -> str:
    """Nome de sócio ou `grupo`. Sem SOCIOS configurado, nada vale (falha fechada), `grupo` inclusive."""
    if nome.strip().lower() == GRUPO:
        if not _nomes_dos_socios(config):
            raise ErroDeUso("falta SOCIOS no cerebro.env")
        return GRUPO
    return _socio(config, nome)


def _cliente(config: dict) -> Paperclip:
    faltam = [c for c in ("PAPERCLIP_URL", "PAPERCLIP_TOKEN", "PAPERCLIP_COMPANY") if not config.get(c)]
    if faltam:
        raise ErroDeUso(f"quadro sem configuração: falta {', '.join(faltam)}")
    return Paperclip(config["PAPERCLIP_URL"], config["PAPERCLIP_TOKEN"], config["PAPERCLIP_COMPANY"])


def _cota(config: dict) -> Cota:
    return Cota(Path(config.get("COTA_PATH") or COTA_PADRAO).expanduser())


def _ler_painel(config: dict) -> str:
    caminho = config.get("PAINEL_PATH")
    if not caminho:
        return ""
    try:
        return Path(caminho).expanduser().read_text(encoding="utf-8")
    except (OSError, ValueError):
        return ""


def _data(iso: str, com_hora: bool = False) -> str:
    try:
        quando = datetime.fromisoformat(iso).astimezone(FUSO)
    except (ValueError, TypeError):
        return ""
    return quando.strftime("%d/%m %H:%M" if com_hora else "%d/%m")


def _cortar(texto: str, limite: int) -> str:
    texto = " ".join(str(texto or "").split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def _saida(texto: str) -> None:
    print(mascarar(texto))


# --- subcomandos ---------------------------------------------------------------
def _linha_pendencia(p) -> str:
    origem = {"bloqueada": "bloqueada", "cartao": "cartão", "painel": "painel"}.get(p.origem, p.origem)
    partes = [p.ref, origem] if p.ref else [origem]
    desde = _data(p.desde)
    if desde:
        partes.append(f"desde {desde}")
    linha = " · ".join(partes + [p.titulo])
    if p.detalhe:
        linha += f" — {_cortar(p.detalhe, DETALHE_NA_LINHA)}"
    return linha


def _cmd_pendencias(args, config, pc, agora) -> int:
    socio = _socio(config, args.socio)
    nao_lidas = set()  # tarefas que o quadro recusou ler (4xx); rede e 5xx continuam abortando tudo
    bloqueadas = []
    for i in pc.issues(["blocked"]) or []:
        try:
            bloqueadas.append((i, pc.comentarios(i["identifier"], limite=1) or []))
        except QuadroRecusou:
            nao_lidas.add(i["identifier"])
    cartoes = []
    for i in pc.issues(ESTADOS_COM_CARTAO) or []:
        try:
            abertos = [c for c in pc.interacoes(i["identifier"]) or [] if c.get("status") == "pending"]
        except QuadroRecusou:
            nao_lidas.add(i["identifier"])
            continue
        cartoes.extend((i, c) for c in abertos)
    achadas = pendencias_do_socio(socio, bloqueadas, cartoes, _ler_painel(config))
    linhas = [_linha_pendencia(p) for p in achadas] or [f"nada pendente pro {socio}"]
    if nao_lidas:
        linhas.append(f"({len(nao_lidas)} tarefas não lidas)")
    _saida("\n".join(linhas))
    return 0


def _cmd_tarefa(args, config, pc, agora) -> int:
    t = pc.issue(args.ident)
    ident = t.get("identifier", args.ident)
    linhas = [f"{ident} · {t.get('status', '?')} · {_cortar(t.get('title', ''), 200)}"]
    comentarios = pc.comentarios(ident, limite=3)
    if comentarios:
        linhas.append("últimos comentários:")
        for c in comentarios:
            linhas.append(f"- {_data(c.get('createdAt', ''), True)} · {_cortar(c.get('body', ''), COMENTARIO_NA_TAREFA)}")
    abertos = [c for c in pc.interacoes(ident) if c.get("status") == "pending"]
    if abertos:
        linhas.append("cartões abertos:")
        for c in abertos:
            detalhe = f" — {_cortar(c['summary'], DETALHE_NA_LINHA)}" if c.get("summary") else ""
            linhas.append(f"- {c.get('id')} · {c.get('kind', '')} · {_cortar(c.get('title', ''), 120)}{detalhe}")
    _saida("\n".join(linhas))
    return 0


def _cmd_comentar(args, config, pc, agora) -> int:
    pc.comentar(args.ident, args.texto)
    _saida("ok")
    return 0


def _cmd_status(args, config, pc, agora) -> int:
    pc.mudar_status(args.ident, args.status)
    _saida("ok")
    return 0


def _registrar_quem_aprovou(pc, ident, socio, agora) -> None:
    quando = agora.astimezone(FUSO).strftime("%d/%m/%Y %H:%M")
    pc.comentar(ident, f"aprovado pelo {socio.capitalize()} via WhatsApp, em {quando}")


def _comentar_aprovacao(pc, ident, socio, agora, feito: str) -> int:
    """A ação já aconteceu; se só o comentário falhar, avisa com saída 4 para o agente NÃO repetir a ação."""
    try:
        _registrar_quem_aprovou(pc, ident, socio, agora)
    except Exception:
        _saida(f"{feito}, mas o comentário falhou")
        return 4
    _saida("ok")
    return 0


def _cmd_aprovar(args, config, pc, agora) -> int:
    socio = _socio(config, args.socio)
    pc.aprovar(args.approval)
    return _comentar_aprovacao(pc, args.ident, socio, agora, "aprovado")


def _cmd_aceitar(args, config, pc, agora) -> int:
    socio = _socio(config, args.socio)
    pc.aceitar_interacao(args.ident, args.interacao)
    return _comentar_aprovacao(pc, args.ident, socio, agora, "aceito")


def _cmd_cota(args, config, pc, agora) -> int:
    socio = _chave_de_cota(config, args.socio)
    _saida("pode" if _cota(config).pode_enviar(socio, agora) else "esgotada")
    return 0


def _cmd_enviei(args, config, pc, agora) -> int:
    socio = _chave_de_cota(config, args.socio)
    _saida("pode" if _cota(config).reservar(socio, agora) else "esgotada")
    return 0


def _cmd_e_comando(args, config, pc, agora) -> int:
    _saida("sim" if e_comando(args.texto) else "nao")
    return 0


# Quais subcomandos não precisam falar com o quadro (nem ter token configurado)
_SEM_REDE = {"cota", "enviei", "e-comando"}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ErroDeUso(f"uso: quadro <pendencias|tarefa|comentar|status|aceitar|aprovar|cota|enviei|e-comando> ... ({message})")


def _parser() -> argparse.ArgumentParser:
    p = _Parser(prog="quadro", add_help=False)
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_Parser)

    def novo(nome, func, *posicionais, socio=False):
        s = sub.add_parser(nome, add_help=False)
        for pos in posicionais:
            s.add_argument(pos)
        if socio:
            s.add_argument("--socio", required=True)
        s.set_defaults(func=func)

    novo("pendencias", _cmd_pendencias, "socio")
    novo("tarefa", _cmd_tarefa, "ident")
    novo("comentar", _cmd_comentar, "ident", "texto")
    novo("status", _cmd_status, "ident", "status")
    novo("aceitar", _cmd_aceitar, "ident", "interacao", socio=True)
    novo("aprovar", _cmd_aprovar, "approval", "ident", socio=True)
    novo("cota", _cmd_cota, "socio")
    novo("enviei", _cmd_enviei, "socio")
    novo("e-comando", _cmd_e_comando, "texto")
    return p


def _detalhe_da_recusa(e: QuadroRecusou) -> str:
    """O texto do servidor, sem o prefixo "Paperclip recusou o pedido (HTTP n): " (já vem mascarado)."""
    return str(e).split(f"(HTTP {e.codigo}): ", 1)[-1]


def main(argv: list[str], pc: Paperclip | None = None, config: dict | None = None,
         agora: datetime | None = None) -> int:
    """Roda um subcomando e devolve o código de saída. Nunca deixa subir exceção esperada.

    `config` e `agora` existem para os testes; em uso normal o arquivo cerebro.env só é lido
    quando `pc` não foi dado.
    """
    agora = agora or datetime.now(FUSO)
    try:
        args = _parser().parse_args(argv)
        if config is None:
            config = _carregar_config() if pc is None else {}
        if pc is None and args.cmd not in _SEM_REDE:
            pc = _cliente(config)
        return args.func(args, config, pc, agora)
    except ErroDeUso as e:
        _saida(str(e))
        return 2 if str(e).startswith("uso:") else 1
    except QuadroForaDoAr:
        print("quadro fora do ar")
        return 2
    except QuadroRecusou as e:
        _saida(f"quadro recusou: {_detalhe_da_recusa(e)}")
        return 3
    except Exception as e:  # último recurso: o agente nunca vê stack trace
        _saida(f"erro inesperado: {type(e).__name__}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
