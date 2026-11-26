import pytest

from mascarar import mascarar


@pytest.mark.parametrize("seg", [
    "sk-ant-api03-AbCdEf0123456789xyz",
    "ghp_0123456789abcdefABCDEF0123456789abcd",
    "github_pat_11ABCDEFG0123456789_abcdefghijklmnop",
    "Bearer abc.def.ghi",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",
    "a3f9c2e1b4d5a6f7e8c9b0a1d2e3f4a5",
])
def test_mascara_segredo(seg):
    assert mascarar(f"a chave é {seg} ok") == "a chave é [segredo] ok"


def test_texto_normal_passa():
    assert mascarar("DGC-370 esperando o Danilo desde 23/11") == "DGC-370 esperando o Danilo desde 23/11"


def test_uuid_nao_e_segredo():
    uuid = "1e670459-aaaa-4bbb-8ccc-123456789abc"
    assert mascarar(f"empresa {uuid}") == f"empresa {uuid}"


def test_varios_segredos_no_mesmo_texto():
    texto = "ghp_0123456789abcdefABCDEF0123456789abcd e sk-ant-api03-AbCdEf0123456789xyz"
    assert mascarar(texto) == "[segredo] e [segredo]"
