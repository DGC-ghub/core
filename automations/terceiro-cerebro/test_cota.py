import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from cota import Cota

BRT = ZoneInfo("America/Sao_Paulo")
UTC = timezone.utc


def test_teto_3_por_dia(tmp_path):
    c = Cota(tmp_path / "c.json")
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    for _ in range(3):
        assert c.pode_enviar("gabriel", t)
        c.registrar("gabriel", t)
    assert not c.pode_enviar("gabriel", t)


def test_teto_e_por_socio(tmp_path):
    c = Cota(tmp_path / "c.json")
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    for _ in range(3):
        c.registrar("gabriel", t)
    assert c.pode_enviar("danilo", t)


def test_janela_em_brasilia_com_relogio_utc(tmp_path):
    c = Cota(tmp_path / "c.json")
    assert not c.pode_enviar("gabriel", datetime(2026, 11, 28, 0, 30, tzinfo=UTC))  # 21:30 BRT
    assert c.pode_enviar("gabriel", datetime(2026, 11, 27, 11, 0, tzinfo=UTC))  # 08:00 BRT


def test_janela_fecha_as_21_com_21_fora(tmp_path):
    c = Cota(tmp_path / "c.json")
    assert c.pode_enviar("gabriel", datetime(2026, 11, 27, 20, 59, tzinfo=BRT))
    assert not c.pode_enviar("gabriel", datetime(2026, 11, 27, 21, 0, tzinfo=BRT))


def test_janela_abre_as_08(tmp_path):
    c = Cota(tmp_path / "c.json")
    assert not c.pode_enviar("gabriel", datetime(2026, 11, 27, 7, 59, tzinfo=BRT))
    assert c.pode_enviar("gabriel", datetime(2026, 11, 27, 8, 0, tzinfo=BRT))


def test_dia_vira_em_brasilia(tmp_path):
    c = Cota(tmp_path / "c.json")
    for _ in range(3):
        c.registrar("gabriel", datetime(2026, 11, 27, 20, tzinfo=BRT))
    assert not c.pode_enviar("gabriel", datetime(2026, 11, 27, 20, 30, tzinfo=BRT))
    assert c.pode_enviar("gabriel", datetime(2026, 11, 28, 8, tzinfo=BRT))


def test_estado_persiste_e_cria_pastas(tmp_path):
    caminho = tmp_path / "a" / "b" / "c.json"
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    for _ in range(3):
        Cota(caminho).registrar("gabriel", t)
    assert not Cota(caminho).pode_enviar("gabriel", t)


def test_arquivo_corrompido_vira_estado_vazio(tmp_path):
    caminho = tmp_path / "c.json"
    caminho.write_text("{isso nao e json")
    c = Cota(caminho)
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    assert c.pode_enviar("gabriel", t)
    c.registrar("gabriel", t)
    assert Cota(caminho).pode_enviar("gabriel", t)


def test_json_de_formato_estranho_vira_estado_vazio(tmp_path):
    caminho = tmp_path / "c.json"
    caminho.write_text('["lista"]')
    assert Cota(caminho).pode_enviar("gabriel", datetime(2026, 11, 27, 9, tzinfo=BRT))
    caminho.write_text('{"gabriel": {"dia": "2026-11-27", "n": "abc"}}')
    assert Cota(caminho).pode_enviar("gabriel", datetime(2026, 11, 27, 9, tzinfo=BRT))


def test_arquivo_ausente_e_estado_vazio(tmp_path):
    assert Cota(tmp_path / "nao-existe.json").pode_enviar(
        "gabriel", datetime(2026, 11, 27, 9, tzinfo=BRT))


def test_reservar_respeita_teto_e_janela(tmp_path):
    c = Cota(tmp_path / "c.json")
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    assert [c.reservar("gabriel", t) for _ in range(4)] == [True, True, True, False]
    assert not c.reservar("danilo", datetime(2026, 11, 27, 21, 0, tzinfo=BRT))
    assert c.reservar("danilo", t)


def test_reservar_concorrente_deixa_passar_exatamente_3(tmp_path):
    caminho = tmp_path / "c.json"
    t = datetime(2026, 11, 27, 9, tzinfo=BRT)
    n = 12
    barreira = threading.Barrier(n)
    resultados = []

    def tentar():
        c = Cota(caminho)  # uma instância por thread, como processos separados
        barreira.wait()
        resultados.append(c.reservar("gabriel", t))

    fios = [threading.Thread(target=tentar) for _ in range(n)]
    for f in fios:
        f.start()
    for f in fios:
        f.join()
    assert sum(resultados) == 3
    assert not Cota(caminho).pode_enviar("gabriel", t)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["c.json", "c.json.lock"]
