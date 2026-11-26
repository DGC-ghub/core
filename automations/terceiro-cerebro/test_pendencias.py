from pendencias import Pendencia, pendencias_do_socio


def issue(ident="DGC-370", titulo="Algo"):
    return {"id": f"uuid-{ident}", "identifier": ident, "title": titulo,
            "status": "blocked", "updatedAt": "2026-11-20T10:00:00Z"}


def com(corpo, quando="2026-11-25T12:00:00Z"):
    return {"body": corpo, "createdAt": quando}


PAINEL = """# Painel

## Precisa do Gabriel (em ordem)
1. ✅ **Push:** a nota 74 chegou.
4. **Backup LGPD (DGC-92):** dar o aval e rodar uma vez.
   continuação indentada do item 4.
7b. Revisar o contrato

## Precisa do Danilo
1. ✅ Topou ser a "clínica" no teste (23/11).
4. Login do Uptime Kuma (o SSH no servidor já temos), pendente.

## Rodando sozinho (sem precisar de vocês)
1. Coisa que roda sozinha
"""


def test_bloqueada_esperando_gabriel_conta():
    r = pendencias_do_socio(
        "gabriel", [(issue(), [com("Continuam esperando o Gabriel")])], [], "")
    assert len(r) == 1
    p = r[0]
    assert (p.socio, p.origem, p.ref, p.titulo) == ("gabriel", "bloqueada", "DGC-370", "Algo")
    assert p.desde == "2026-11-25T12:00:00Z"
    assert "esperando o Gabriel" in p.detalhe


def test_bloqueada_esperando_gabriel_nao_conta_para_danilo():
    assert pendencias_do_socio(
        "danilo", [(issue(), [com("Continuam esperando o Gabriel")])], [], "") == []


def test_waiting_for_danilo_em_ingles_conta():
    r = pendencias_do_socio(
        "danilo", [(issue(), [com("Waiting for Danilo: reply sim")])], [], "")
    assert len(r) == 1 and r[0].socio == "danilo"


def test_bloqueada_esperando_agente_nao_conta():
    assert pendencias_do_socio(
        "gabriel", [(issue(), [com("bloqueada pela DGC-422")])], [], "") == []


def test_usa_so_o_ultimo_comentario_que_vem_primeiro():
    comentarios = [com("Resolvido, segue o baile", "2026-11-25T12:00:00Z"),
                   com("esperando o Gabriel", "2026-11-20T12:00:00Z")]
    assert pendencias_do_socio("gabriel", [(issue(), comentarios)], [], "") == []


def test_bloqueada_sem_comentarios_nao_conta():
    assert pendencias_do_socio("gabriel", [(issue(), [])], [], "") == []


def test_cartao_aberto_conta_para_gabriel():
    cartao = {"id": "i1", "kind": "request_confirmation", "status": "pending",
              "title": "Aprovar o plano", "summary": "Resumo", "createdAt": "2026-11-24T08:00:00Z"}
    r = pendencias_do_socio("gabriel", [], [(issue("DGC-9", "Tarefa"), cartao)], "")
    assert len(r) == 1
    p = r[0]
    assert (p.origem, p.ref, p.desde) == ("cartao", "DGC-9", "2026-11-24T08:00:00Z")
    assert "Aprovar o plano" in p.titulo


def test_cartao_aberto_nao_conta_para_danilo():
    cartao = {"id": "i1", "kind": "x", "status": "pending", "title": "T",
              "summary": "", "createdAt": "2026-11-24T08:00:00Z"}
    assert pendencias_do_socio("danilo", [], [(issue(), cartao)], "") == []


def test_cartao_resolvido_nao_conta():
    cartao = {"id": "i1", "kind": "x", "status": "accepted", "title": "T",
              "summary": "", "createdAt": "2026-11-24T08:00:00Z"}
    assert pendencias_do_socio("gabriel", [], [(issue(), cartao)], "") == []


def test_painel_secao_do_danilo():
    r = pendencias_do_socio("danilo", [], [], PAINEL)
    assert len(r) == 1
    assert r[0].origem == "painel" and r[0].desde == "" and r[0].ref == ""
    assert r[0].titulo.startswith("Login do Uptime Kuma")


def test_painel_secao_do_gabriel_ignora_feitos_e_pega_ref():
    r = pendencias_do_socio("gabriel", [], [], PAINEL)
    assert [p.ref for p in r] == ["DGC-92", ""]
    assert r[0].titulo.startswith("**Backup LGPD") or r[0].titulo.startswith("Backup LGPD")
    assert all("✅" not in p.titulo for p in r)
    assert not any("Coisa que roda sozinha" in p.titulo for p in r)


def test_painel_titulo_limitado_a_120():
    md = "## Precisa do Danilo\n1. " + "x" * 300 + "\n"
    r = pendencias_do_socio("danilo", [], [], md)
    assert len(r[0].titulo) <= 120


def test_item_feito_com_continuacao_nao_conta():
    md = "## Precisa do Danilo\n1. ✅ feito\n   continuação sem marca\n2. aberto\n"
    r = pendencias_do_socio("danilo", [], [], md)
    assert [p.titulo for p in r] == ["aberto"]


def test_ordenada_da_mais_antiga_para_a_mais_nova_painel_por_ultimo():
    bloq = [(issue("DGC-1"), [com("esperando o Gabriel", "2026-11-25T00:00:00Z")]),
            (issue("DGC-2"), [com("esperando o Gabriel", "2026-11-10T00:00:00Z")])]
    cartao = {"id": "i", "kind": "k", "status": "pending", "title": "C",
              "summary": "", "createdAt": "2026-11-18T00:00:00Z"}
    r = pendencias_do_socio("gabriel", bloq, [(issue("DGC-3"), cartao)], PAINEL)
    assert [p.ref for p in r[:3]] == ["DGC-2", "DGC-3", "DGC-1"]
    assert all(p.origem == "painel" for p in r[3:])


def test_pendencia_e_dataclass_com_campos():
    p = Pendencia("gabriel", "painel", "", "t", "", "d")
    assert p.detalhe == "d"
