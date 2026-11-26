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
    uuid = "00000000-0000-4000-8000-000000000000"
    assert mascarar(f"empresa {uuid}") == f"empresa {uuid}"


def test_varios_segredos_no_mesmo_texto():
    texto = "ghp_0123456789abcdefABCDEF0123456789abcd e sk-ant-api03-AbCdEf0123456789xyz"
    assert mascarar(texto) == "[segredo] e [segredo]"


@pytest.mark.parametrize("texto", [
    "o Bearer token expirou",
    "Bearer expirou.",
    "usa Bearer no header",
])
def test_bearer_em_prosa_passa(texto):
    assert mascarar(texto) == texto


@pytest.mark.parametrize("seg", [
    "bearer abc.def.ghi", "BEARER abc.def.ghi", "bearer AbCdEf0123456789xyzQ",
])
def test_bearer_com_valor_de_token_e_mascarado_sem_diferenciar_caixa(seg):
    assert mascarar(f"header {seg} ok") == "header [segredo] ok"


def test_hex_no_limite_de_32():
    assert mascarar("a" * 31) == "a" * 31
    assert mascarar("a" * 32) == "[segredo]"


def test_hex_maiusculo_e_mascarado():
    assert mascarar("chave " + "A3F9C2E1" * 4) == "chave [segredo]"


def test_hex_colado_em_prefixo_com_sublinhado_e_mascarado():
    assert mascarar("key_" + "a3f9c2e1" * 4) == "key_[segredo]"
    assert mascarar("key=" + "a3f9c2e1" * 4) == "key=[segredo]"


def test_hex_dentro_de_palavra_maior_nao_e_mascarado():
    assert mascarar("x" + "a" * 32) == "x" + "a" * 32


# --- segredos de outros serviços --------------------------------------------------------------
_FALSO_35 = "Ab0_Cd1-Ef2Gh3Ij4Kl5Mn6Op7Qr8St9Uv0"
assert len(_FALSO_35) == 35


@pytest.mark.parametrize("seg", [
    "sk-proj-AbCdEf0123456789xyzAbCdEf0123456789",             # OpenAI (projeto)
    "sk-AbCdEf0123456789xyzAbCdEf0123456789",                  # OpenAI (antiga)
    "sk-svcacct-AbCdEf0123456789xyz_AbCdEf",                   # OpenAI (conta de serviço)
    f"123456789:{_FALSO_35}",                                  # bot do Telegram
    "AKIAABCDEFGHIJKLMNOP",                                    # AWS
    f"AIza{_FALSO_35}",                                        # Google
    "xoxb-0000000000-0000000000000-AbCdEfGhIjKl",              # Slack
    "EAAGm0PX4ZCpsBAAbCdEf0123456789",                         # Meta
    "pcp_board_" + "0a1b2c3d" * 6,                             # Paperclip (formato da chave do quadro)
    "pcp_board_SEGREDINHO_123",
])
def test_mascara_segredos_de_outros_servicos(seg):
    assert mascarar(f"a chave é {seg} ok") == "a chave é [segredo] ok"


def test_bloco_de_chave_privada_some_inteiro():
    pem = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXk\nAAAA\n-----END OPENSSH PRIVATE KEY-----"
    assert mascarar(f"antes\n{pem}\ndepois") == "antes\n[segredo]\ndepois"
    rsa = "-----BEGIN RSA PRIVATE KEY-----\nMIIE\n-----END RSA PRIVATE KEY-----"
    assert mascarar(rsa) == "[segredo]"


def test_bloco_de_chave_privada_cortado_some_ate_o_fim():
    assert mascarar("veja: -----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg…") == "veja: [segredo]"


@pytest.mark.parametrize("texto", [
    "o sk-ant é a chave da Anthropic",
    "task-1234 e sk-learn",                     # sk- curto
    "risk-assessment-of-the-whole-project",     # "sk-" dentro de palavra
    "às 10:30:00 do dia 26/11",                 # hora não é token do Telegram
    "pedido 123456789:ok",
    "AKIA é o prefixo da AWS",
    "a pcp_board e a pcp_x",                    # prefixo sem valor
    "EAA é o começo do token da Meta",
    "-----BEGIN PUBLIC KEY----- é pública",
    "DGC-370 xoxo e abraço",
])
def test_texto_normal_com_prefixos_passa(texto):
    assert mascarar(texto) == texto
