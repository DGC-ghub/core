"""Testa o gancho barra-do-robo sem precisar do Hermes (usa objetos de mentira)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_PLUGIN = Path(__file__).parent / "hermes" / "plugins" / "barra-do-robo" / "__init__.py"
_spec = importlib.util.spec_from_file_location("barra_do_robo", _PLUGIN)
barra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(barra)


def evento(texto, plataforma="whatsapp", metadata=None):
    source = SimpleNamespace(platform=SimpleNamespace(value=plataforma))
    return SimpleNamespace(text=texto, source=source, metadata=metadata or {})


@pytest.mark.parametrize("texto", ["/ajuda", "/status", "  /status", "\n\t/x arg", "/"])
def test_comando_com_barra_no_whatsapp_e_ignorado(texto):
    r = barra.ignorar_barra(evento(texto))
    assert r["action"] == "skip"


@pytest.mark.parametrize("texto", ["oi mano", "cadê a DGC-322?", "ver /status", "", "http://x/y", "5/3"])
def test_outros_textos_passam(texto):
    assert barra.ignorar_barra(evento(texto)) is None


def test_outras_plataformas_nao_sao_tocadas():
    assert barra.ignorar_barra(evento("/status", plataforma="telegram")) is None


def test_mensagem_do_dono_do_aparelho_e_ignorada():
    r = barra.ignorar_barra(evento("oi", metadata={"whatsapp_from_owner": True}))
    assert r["action"] == "skip"


def test_texto_ausente_nao_quebra():
    e = evento(None)
    assert barra.ignorar_barra(e) is None


def test_plataforma_como_string():
    e = SimpleNamespace(text="/x", source=SimpleNamespace(platform="whatsapp"), metadata={})
    assert barra.ignorar_barra(e)["action"] == "skip"


def test_register_liga_o_gancho_certo():
    chamadas = []
    ctx = SimpleNamespace(register_hook=lambda nome, fn: chamadas.append((nome, fn)))
    barra.register(ctx)
    assert chamadas == [("pre_gateway_dispatch", barra.ignorar_barra)]
