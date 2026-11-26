"""Testa o gancho barra-do-robo sem precisar do Hermes (usa objetos de mentira)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_PLUGIN = Path(__file__).parent / "hermes" / "plugins" / "barra-do-robo" / "__init__.py"
_spec = importlib.util.spec_from_file_location("barra_do_robo", _PLUGIN)
barra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(barra)


def evento(texto, plataforma="whatsapp", metadata=None, grupo=False, bruto=None, resposta_ao_bot=False):
    source = SimpleNamespace(platform=SimpleNamespace(value=plataforma), chat_type="group" if grupo else "dm")
    return SimpleNamespace(text=texto, source=source, metadata=metadata or {}, raw_message=bruto,
                           reply_to_is_own_message=resposta_ao_bot, reply_expected=None)


BOT = "5562000000000@s.whatsapp.net"


def grupo(texto, **kw):
    bruto = {"isGroup": True, "botIds": [BOT, "111222333@lid"], "body": texto, "mentionedIds": kw.pop("marcados", [])}
    return evento(texto, grupo=True, bruto=bruto, **kw)


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


# --- grupo: quando o [SILENT] do modelo pode valer (reply_expected = False) -------------------------------
@pytest.mark.parametrize("texto", ["mano cadê o contrato", "o hermes piloto caiu", "cê viu isso?", "bora fechar", "oi hermes"])
def test_conversa_entre_socios_pode_calar(texto):
    e = grupo(texto)
    assert barra.pode_calar(e) is True
    assert barra.ignorar_barra(e) is None
    assert e.reply_expected is False


@pytest.mark.parametrize("texto", ["hermes, o que falta?", "  Hermes: e aí", "@hermes oi", "@Hermes"])
def test_chamar_pelo_nome_no_comeco_nao_pode_calar(texto):
    e = grupo(texto)
    assert barra.pode_calar(e) is False
    barra.ignorar_barra(e)
    assert e.reply_expected is None


def test_nome_no_comeco_so_vale_como_palavra():
    e = grupo("hermesinho caiu de novo")
    assert barra.pode_calar(e) is True


def test_marcar_o_bot_nao_pode_calar():
    e = grupo("@5562000000000 o que tá travando?", marcados=["5562000000000:7@s.whatsapp.net"])
    assert barra.pode_calar(e) is False
    barra.ignorar_barra(e)
    assert e.reply_expected is None


def test_marcar_o_bot_pelo_lid():
    e = grupo("olha isso aí", marcados=["111222333@lid"])
    assert barra.pode_calar(e) is False


def test_marcar_outra_pessoa_nao_conta():
    e = grupo("@5562111111111 e aí", marcados=["5562111111111@s.whatsapp.net"])
    assert barra.pode_calar(e) is True


def test_resposta_a_mensagem_do_bot_nao_pode_calar():
    e = grupo("pior que sim", resposta_ao_bot=True)
    assert barra.pode_calar(e) is False
    barra.ignorar_barra(e)
    assert e.reply_expected is None


def test_dm_nunca_pode_calar():
    e = evento("oi", grupo=False, bruto={"isGroup": False})
    assert barra.pode_calar(e) is False
    barra.ignorar_barra(e)
    assert e.reply_expected is None


def test_grupo_de_outra_plataforma_nao_e_tocado():
    e = grupo("papo de grupo")
    e.source.platform = SimpleNamespace(value="telegram")
    barra.ignorar_barra(e)
    assert e.reply_expected is None


def test_barra_no_grupo_continua_sendo_descartada():
    e = grupo("/status")
    assert barra.ignorar_barra(e)["action"] == "skip"
    assert e.reply_expected is None


def test_grupo_detectado_so_pelo_bruto():
    e = SimpleNamespace(text="oi gente", source=SimpleNamespace(platform="whatsapp", chat_type="dm"),
                        metadata={}, raw_message={"isGroup": True, "botIds": [BOT], "body": "oi gente"},
                        reply_to_is_own_message=False, reply_expected=None)
    assert barra.pode_calar(e) is True


def test_evento_imutavel_nao_quebra():
    class Congelado(SimpleNamespace):
        def __setattr__(self, k, v):
            if k == "reply_expected":
                raise AttributeError("congelado")
            super().__setattr__(k, v)
    e = Congelado(text="papo", source=SimpleNamespace(platform="whatsapp", chat_type="group"), metadata={},
                  raw_message={"isGroup": True, "botIds": [BOT]}, reply_to_is_own_message=False)
    assert barra.ignorar_barra(e) is None
