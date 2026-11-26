import http.client
import io
import json
import urllib.error

import pytest

from paperclip import Paperclip, QuadroForaDoAr, QuadroRecusou

TOKEN = "pcp_board_SEGREDINHO_123"
EMPRESA = "00000000-0000-4000-8000-000000000000"
GHP = "ghp_0123456789abcdefABCDEF0123456789abcd"


class Resp:
    def __init__(self, corpo):
        self._b = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Abrir:
    """abrir falso: guarda os pedidos e devolve/levanta o que for combinado."""

    def __init__(self, resposta=None, erro=None):
        self.resposta, self.erro, self.pedidos = resposta, erro, []

    def __call__(self, req, timeout=None):
        self.pedidos.append(req)
        if self.erro:
            raise self.erro
        return Resp(self.resposta if self.resposta is not None else b"")


def cliente(abrir):
    return Paperclip("http://127.0.0.1:3100/", TOKEN, EMPRESA, abrir=abrir)


def test_comentarios_vem_mascarados():
    ab = Abrir([{"id": "c1", "body": f"use {GHP} agora", "createdAt": "2026-11-26T10:00:00Z"}])
    r = cliente(ab).comentarios("DGC-370")
    assert r[0]["body"] == "use [segredo] agora"
    assert r[0]["id"] == "c1"


def test_mascara_tambem_em_dados_aninhados():
    ab = Abrir([{"id": "i1", "kind": "x", "payload": {"itens": [f"{GHP}"]}}])
    assert cliente(ab).interacoes("DGC-1")[0]["payload"]["itens"] == ["[segredo]"]


def test_comentarios_pede_os_mais_novos_com_limite():
    ab = Abrir([])
    cliente(ab).comentarios("DGC-370", limite=3)
    req = ab.pedidos[0]
    assert req.get_method() == "GET"
    assert req.full_url == "http://127.0.0.1:3100/api/issues/DGC-370/comments?order=desc&limit=3"
    assert req.get_header("Authorization") == f"Bearer {TOKEN}"


def test_issues_filtra_status_separado_por_virgula():
    ab = Abrir([{"identifier": "DGC-1", "status": "blocked"}])
    r = cliente(ab).issues(["blocked", "in_review"])
    assert r == [{"identifier": "DGC-1", "status": "blocked"}]
    assert ab.pedidos[0].full_url == f"http://127.0.0.1:3100/api/companies/{EMPRESA}/issues?status=blocked,in_review"


def test_issue_aceita_identificador():
    ab = Abrir({"id": "u", "identifier": "DGC-370"})
    assert cliente(ab).issue("DGC-370")["identifier"] == "DGC-370"
    assert ab.pedidos[0].full_url == "http://127.0.0.1:3100/api/issues/DGC-370"


def test_interacoes_rota():
    ab = Abrir([])
    cliente(ab).interacoes("DGC-370")
    assert ab.pedidos[0].full_url == "http://127.0.0.1:3100/api/issues/DGC-370/interactions"


@pytest.mark.parametrize("chamar, metodo, caminho, corpo", [
    (lambda c: c.comentar("DGC-1", "oi"), "POST", "/api/issues/DGC-1/comments", {"body": "oi"}),
    (lambda c: c.mudar_status("DGC-1", "done"), "PATCH", "/api/issues/DGC-1", {"status": "done"}),
    (lambda c: c.aceitar_interacao("DGC-1", "int-9"), "POST", "/api/issues/DGC-1/interactions/int-9/accept", {}),
    (lambda c: c.aprovar("ap-7"), "POST", "/api/approvals/ap-7/approve", {}),
])
def test_escritas(chamar, metodo, caminho, corpo):
    ab = Abrir(b"")  # corpo vazio também é aceito
    assert chamar(cliente(ab)) is None
    req = ab.pedidos[0]
    assert req.get_method() == metodo
    assert req.full_url == "http://127.0.0.1:3100" + caminho
    assert json.loads(req.data) == corpo
    assert req.get_header("Content-type") == "application/json"
    assert req.get_header("Authorization") == f"Bearer {TOKEN}"


def test_erro_de_rede_vira_quadro_fora_do_ar():
    ab = Abrir(erro=urllib.error.URLError("connection refused"))
    with pytest.raises(QuadroForaDoAr) as e:
        cliente(ab).issues(["blocked"])
    assert str(e.value) == "Paperclip fora do ar: <urlopen error connection refused>"


def test_timeout_vira_quadro_fora_do_ar():
    with pytest.raises(QuadroForaDoAr) as e:
        cliente(Abrir(erro=TimeoutError("lento"))).issues(["blocked"])
    assert str(e.value) == "Paperclip fora do ar: lento"


def test_5xx_vira_quadro_fora_do_ar():
    erro = urllib.error.HTTPError("http://x", 503, "Service Unavailable", {}, io.BytesIO(b"{}"))
    with pytest.raises(QuadroForaDoAr) as e:
        cliente(Abrir(erro=erro)).issues(["blocked"])
    assert str(e.value) == "Paperclip fora do ar (HTTP 503)"


@pytest.mark.parametrize("erro", [
    http.client.IncompleteRead(b"parcial"),
    http.client.BadStatusLine("lixo"),
])
def test_resposta_cortada_vira_quadro_fora_do_ar(erro):
    with pytest.raises(QuadroForaDoAr):
        cliente(Abrir(erro=erro)).issues(["blocked"])


def test_resposta_que_nao_e_json_vira_quadro_fora_do_ar():
    with pytest.raises(QuadroForaDoAr) as e:
        cliente(Abrir(b"<html>bad gateway</html>")).issues(["blocked"])
    assert str(e.value).startswith("Paperclip fora do ar: ")


def test_4xx_e_recusa_nao_fora_do_ar_e_vem_mascarada():
    erro = urllib.error.HTTPError("http://x", 404, "Not Found", {}, io.BytesIO(f'{{"error":"nao achei {GHP}"}}'.encode()))
    with pytest.raises(QuadroRecusou) as e:
        cliente(Abrir(erro=erro)).issue("DGC-999")
    assert e.value.codigo == 404
    assert str(e.value) == 'Paperclip recusou o pedido (HTTP 404): {"error":"nao achei [segredo]"}'
    assert not isinstance(e.value, QuadroForaDoAr)


def test_4xx_mascara_antes_de_cortar_nao_sobra_pedaco_de_segredo():
    corpo = "x" * 290 + GHP  # o segredo atravessa o limite de 300
    erro = urllib.error.HTTPError("http://x", 400, "Bad", {}, io.BytesIO(corpo.encode()))
    with pytest.raises(QuadroRecusou) as e:
        cliente(Abrir(erro=erro)).issue("DGC-1")
    assert str(e.value) == "Paperclip recusou o pedido (HTTP 400): " + "x" * 290 + "[segredo]"
    assert "ghp_" not in str(e.value)


def test_get_com_corpo_vazio_devolve_none():
    assert cliente(Abrir(b"")).issue("DGC-1") is None


def test_token_literal_na_resposta_e_mascarado():
    ab = Abrir([{"id": "c1", "body": f"o token e {TOKEN} ok"}])
    assert cliente(ab).comentarios("DGC-1")[0]["body"] == "o token e [segredo] ok"


@pytest.mark.parametrize("erro", [
    urllib.error.URLError(f"falha com {TOKEN}"),
    urllib.error.HTTPError("http://x", 500, f"erro {TOKEN}", {}, io.BytesIO(TOKEN.encode())),
    urllib.error.HTTPError("http://x", 401, f"erro {TOKEN}", {}, io.BytesIO(f"Bearer {TOKEN}".encode())),
])
def test_token_nunca_aparece_na_excecao(erro):
    with pytest.raises((QuadroForaDoAr, QuadroRecusou)) as e:
        cliente(Abrir(erro=erro)).issues(["blocked"])
    assert TOKEN not in str(e.value)
    assert TOKEN not in repr(e.value)


def test_url_sem_esquema_vira_recusa_e_nao_stack_trace():
    pc = Paperclip("paperclip.local", TOKEN, EMPRESA, abrir=Abrir([]))
    with pytest.raises(QuadroRecusou) as e:
        pc.issues(["blocked"])
    assert "url inválida" in str(e.value)
    assert TOKEN not in str(e.value)
