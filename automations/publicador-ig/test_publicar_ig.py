import datetime as dt
import json

import pytest

import publicar_ig as p

AGORA = dt.datetime(2026, 11, 26, 11, 35)


def peca(**kw):
    base = {"id": "p2", "quando": "2026-11-26 11:30", "tipo": "Carrossel", "pasta": "p2", "legenda": "Oi.\nManda DIAGNÓSTICO na DM."}
    base.update(kw)
    return base


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "AQUI", tmp_path)
    (tmp_path / "pecas" / "p2").mkdir(parents=True)
    for i in (1, 2, 3):
        (tmp_path / "pecas" / "p2" / f"p2-{i}.jpg").write_bytes(b"x")
    return tmp_path


def test_publica_quando_chegou_a_hora_e_ainda_nao_saiu(pasta):
    assert p.situacao(peca(), {}, AGORA) == (True, "na hora")


def test_nao_publica_antes_da_hora(pasta):
    pode, motivo = p.situacao(peca(), {}, dt.datetime(2026, 11, 26, 11, 0))
    assert not pode and motivo.startswith("agendada")


def test_nao_publica_de_novo(pasta):
    pode, motivo = p.situacao(peca(), {"p2": {"id": "123"}}, AGORA)
    assert not pode and motivo.startswith("publicada")


def test_nao_publica_atrasada_alem_da_janela(pasta):
    pode, motivo = p.situacao(peca(), {}, AGORA + dt.timedelta(hours=p.JANELA_HORAS + 1))
    assert not pode and motivo.startswith("ATRASADA")


def test_suspensa_nao_sai(pasta):
    pode, motivo = p.situacao(peca(suspensa=True), {}, AGORA)
    assert not pode and motivo == "suspensa"


def test_imagens_em_ordem_e_validacao_do_carrossel(pasta):
    assert [f.name for f in p.imagens(peca())] == ["p2-1.jpg", "p2-2.jpg", "p2-3.jpg"]
    with pytest.raises(ValueError, match="carrossel"):
        p.validar(peca(), [pasta / "pecas/p2/p2-1.jpg"])
    with pytest.raises(ValueError, match="post"):
        p.validar(peca(tipo="Post"), p.imagens(peca()))


def test_legenda_longa_ou_hashtag_demais_barra(pasta):
    with pytest.raises(ValueError, match="legenda"):
        p.validar(peca(legenda="a" * 2201), p.imagens(peca()))
    with pytest.raises(ValueError, match="hashtags"):
        p.validar(peca(legenda=" ".join(f"#t{i}" for i in range(31))), p.imagens(peca()))


def test_so_aceita_jpeg(pasta):
    (pasta / "pecas/p2/p2-4.png").write_bytes(b"x")
    with pytest.raises(ValueError, match="JPEG"):
        p.validar(peca(), [*p.imagens(peca()), pasta / "pecas/p2/p2-4.png"])


def test_url_do_tunel_sai_do_log():
    log = "INF |  https://great-technologies-seeks-driver.trycloudflare.com  |\nINF Registered tunnel connection"
    assert p.url_tunel(log) == "https://great-technologies-seeks-driver.trycloudflare.com"
    assert p.url_tunel("INF Requesting new quick Tunnel") is None


def test_token_renova_depois_de_7_dias():
    assert p.precisa_renovar({"renovado_em": "2026-11-18"}, dt.date(2026, 11, 26))
    assert not p.precisa_renovar({"renovado_em": "2026-11-20"}, dt.date(2026, 11, 26))
    assert p.precisa_renovar({}, dt.date(2026, 11, 26))


def test_agenda_de_exemplo_e_valida(pasta):
    (pasta / "agenda.json").write_text(json.dumps([peca()]))
    assert p.agenda()[0]["quando_dt"] == dt.datetime(2026, 11, 26, 11, 30)
