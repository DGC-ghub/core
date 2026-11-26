from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

import quadro
from paperclip import QuadroForaDoAr, QuadroRecusou

FUSO = ZoneInfo("America/Sao_Paulo")
AGORA = datetime(2026, 11, 26, 10, 30, tzinfo=FUSO)
TELEFONE = "5562000000000"


class PaperclipFalso:
    def __init__(self, issues=None, comentarios=None, interacoes=None, erro=None):
        self._issues = issues or {}
        self._comentarios = comentarios or {}
        self._interacoes = interacoes or {}
        self._erro = erro
        self.chamadas = []

    def _registra(self, *chamada):
        self.chamadas.append(chamada)
        if self._erro:
            raise self._erro

    def issues(self, status):
        self._registra("issues", tuple(status))
        achadas = []
        for s in status:
            achadas.extend(self._issues.get(s, []))
        return achadas

    def issue(self, ident):
        self._registra("issue", ident)
        for lista in self._issues.values():
            for i in lista:
                if i["identifier"] == ident:
                    return i
        raise QuadroRecusou(404, "nao achei")

    def comentarios(self, issue_id, limite=5):
        self._registra("comentarios", issue_id, limite)
        return self._comentarios.get(issue_id, [])[:limite]

    def interacoes(self, issue_id):
        self._registra("interacoes", issue_id)
        return self._interacoes.get(issue_id, [])

    def comentar(self, issue_id, texto):
        self._registra("comentar", issue_id, texto)

    def mudar_status(self, issue_id, status):
        self._registra("mudar_status", issue_id, status)

    def aceitar_interacao(self, issue_id, interacao_id):
        self._registra("aceitar_interacao", issue_id, interacao_id)

    def aprovar(self, approval_id):
        self._registra("aprovar", approval_id)


def issue(ident="DGC-370", titulo="Contrato do piloto", status="blocked"):
    return {"id": f"uuid-{ident}", "identifier": ident, "title": titulo,
            "status": status, "updatedAt": "2026-11-20T10:00:00Z"}


@pytest.fixture
def cfg(tmp_path):
    return {"SOCIOS": f"gabriel:{TELEFONE},danilo:{TELEFONE}",
            "PAINEL_PATH": str(tmp_path / "PAINEL.md"),
            "COTA_PATH": str(tmp_path / "cota.json")}


def rodar(argv, pc, cfg, capsys):
    codigo = quadro.main(argv, pc=pc, config=cfg, agora=AGORA)
    return codigo, capsys.readouterr().out


# --- e_comando ---------------------------------------------------------------
def test_e_comando():
    assert quadro.e_comando("/status") is True
    assert quadro.e_comando("  /status") is True
    assert quadro.e_comando("/status ") is True
    assert quadro.e_comando("fiz a B2") is False
    assert quadro.e_comando("e aí /mano") is False


def test_subcomando_e_comando(cfg, capsys):
    assert rodar(["e-comando", " /x"], PaperclipFalso(), cfg, capsys) == (0, "sim\n")
    assert rodar(["e-comando", "oi"], PaperclipFalso(), cfg, capsys) == (0, "nao\n")


# --- erros de rede e recusa ----------------------------------------------------
def test_fora_do_ar_sai_com_2(cfg, capsys):
    pc = PaperclipFalso(erro=QuadroForaDoAr("caiu"))
    codigo, saida = rodar(["pendencias", "gabriel"], pc, cfg, capsys)
    assert codigo == 2
    assert saida == "quadro fora do ar\n"


def test_recusa_sai_com_3(cfg, capsys):
    pc = PaperclipFalso(erro=QuadroRecusou(404, "Issue not found"))
    codigo, saida = rodar(["tarefa", "DGC-1"], pc, cfg, capsys)
    assert codigo == 3
    assert saida == "quadro recusou: Issue not found\n"


# --- aprovar e aceitar -----------------------------------------------------------
def test_aprovar_comenta_quem_aprovou(cfg, capsys):
    pc = PaperclipFalso()
    codigo, saida = rodar(["aprovar", "apr-1", "DGC-370", "--socio", "gabriel"], pc, cfg, capsys)
    assert codigo == 0
    assert pc.chamadas == [
        ("aprovar", "apr-1"),
        ("comentar", "DGC-370", "aprovado pelo Gabriel via WhatsApp, em 26/11/2026 10:30"),
    ]


def test_aceitar_comenta_quem_aprovou(cfg, capsys):
    pc = PaperclipFalso()
    codigo, _ = rodar(["aceitar", "DGC-370", "int-9", "--socio", "danilo"], pc, cfg, capsys)
    assert codigo == 0
    assert pc.chamadas == [
        ("aceitar_interacao", "DGC-370", "int-9"),
        ("comentar", "DGC-370", "aprovado pelo Danilo via WhatsApp, em 26/11/2026 10:30"),
    ]


def test_aprovar_usa_horario_de_brasilia(cfg, capsys):
    utc = datetime(2026, 11, 26, 13, 5, tzinfo=ZoneInfo("UTC"))
    pc = PaperclipFalso()
    quadro.main(["aprovar", "a", "DGC-1", "--socio", "gabriel"], pc=pc, config=cfg, agora=utc)
    assert pc.chamadas[1][2].endswith("em 26/11/2026 10:05")


def test_aprovar_recusado_nao_comenta(cfg, capsys):
    class Recusa(PaperclipFalso):
        def aprovar(self, approval_id):
            super()._registra("aprovar", approval_id)
            raise QuadroRecusou(409, "ja decidido")

    pc = Recusa()
    codigo, saida = rodar(["aprovar", "a", "DGC-1", "--socio", "gabriel"], pc, cfg, capsys)
    assert codigo == 3 and "ja decidido" in saida
    assert [c[0] for c in pc.chamadas] == ["aprovar"]


def test_aprovar_exige_socio_valido(cfg, capsys):
    pc = PaperclipFalso()
    codigo, saida = rodar(["aprovar", "a", "DGC-1", "--socio", "fulano"], pc, cfg, capsys)
    assert codigo == 1
    assert pc.chamadas == []
    assert TELEFONE not in saida


# --- comentar e status ---------------------------------------------------------------
def test_comentar_e_status(cfg, capsys):
    pc = PaperclipFalso()
    assert rodar(["comentar", "DGC-5", "feito a B2"], pc, cfg, capsys) == (0, "ok\n")
    assert rodar(["status", "DGC-5", "done"], pc, cfg, capsys) == (0, "ok\n")
    assert pc.chamadas == [("comentar", "DGC-5", "feito a B2"), ("mudar_status", "DGC-5", "done")]


# --- cota ---------------------------------------------------------------------------
def test_cota_e_enviei(cfg, capsys):
    pc = PaperclipFalso()
    assert rodar(["cota", "gabriel"], pc, cfg, capsys) == (0, "pode\n")
    for _ in range(3):
        assert rodar(["enviei", "gabriel"], pc, cfg, capsys) == (0, "pode\n")
    assert rodar(["enviei", "gabriel"], pc, cfg, capsys) == (0, "esgotada\n")
    assert rodar(["cota", "gabriel"], pc, cfg, capsys) == (0, "esgotada\n")
    assert rodar(["cota", "danilo"], pc, cfg, capsys) == (0, "pode\n")
    assert pc.chamadas == []  # a cota não fala com o quadro


def test_cota_fora_da_janela(cfg, capsys):
    noite = datetime(2026, 11, 26, 22, 0, tzinfo=FUSO)
    assert quadro.main(["cota", "gabriel"], pc=PaperclipFalso(), config=cfg, agora=noite) == 0
    assert capsys.readouterr().out == "esgotada\n"
    assert quadro.main(["enviei", "gabriel"], pc=PaperclipFalso(), config=cfg, agora=noite) == 0
    assert capsys.readouterr().out == "esgotada\n"


def test_cota_socio_desconhecido(cfg, capsys):
    codigo, saida = rodar(["cota", "fulano"], PaperclipFalso(), cfg, capsys)
    assert codigo == 1
    assert "gabriel" in saida and TELEFONE not in saida


# --- pendencias ----------------------------------------------------------------------
def test_pendencias_vazio(cfg, capsys):
    assert rodar(["pendencias", "gabriel"], PaperclipFalso(), cfg, capsys) == (0, "nada pendente pro gabriel\n")


def test_pendencias_junta_fontes(cfg, tmp_path, capsys):
    (tmp_path / "PAINEL.md").write_text("## Precisa do Gabriel\n1. Revisar o contrato (DGC-92)\n", encoding="utf-8")
    pc = PaperclipFalso(
        issues={"blocked": [issue()], "in_review": [issue("DGC-400", "Texto do robô", "in_review")]},
        comentarios={"uuid-DGC-370": [{"body": "Segue esperando o Gabriel", "createdAt": "2026-11-23T15:00:00Z"}],
                     "DGC-370": [{"body": "Segue esperando o Gabriel", "createdAt": "2026-11-23T15:00:00Z"}]},
        interacoes={"DGC-400": [{"id": "i1", "status": "pending", "title": "Posso publicar?",
                                 "summary": "o post de sexta", "createdAt": "2026-11-24T10:00:00Z"},
                                {"id": "i2", "status": "accepted", "title": "velha", "createdAt": "2026-11-01T10:00:00Z"}]},
    )
    codigo, saida = rodar(["pendencias", "gabriel"], pc, cfg, capsys)
    assert codigo == 0
    linhas = saida.splitlines()
    assert len(linhas) == 3
    assert linhas[0].startswith("DGC-370 · bloqueada · desde 23/11 · Contrato do piloto — ")
    assert "esperando o Gabriel" in linhas[0]
    assert linhas[1].startswith("DGC-400 · cartão · desde 24/11 · Posso publicar? — o post de sexta")
    assert "painel" in linhas[2] and "Revisar o contrato" in linhas[2]
    assert "velha" not in saida


def test_pendencias_leitura_bloqueadas_com_limite_1(cfg, capsys):
    pc = PaperclipFalso(issues={"blocked": [issue()]})
    rodar(["pendencias", "danilo"], pc, cfg, capsys)
    assert ("issues", ("blocked",)) in pc.chamadas
    assert ("issues", ("blocked", "in_review", "in_progress", "todo")) in pc.chamadas
    assert any(c[0] == "comentarios" and c[2] == 1 for c in pc.chamadas)


def test_pendencias_painel_ausente_nao_quebra(cfg, capsys):
    assert rodar(["pendencias", "danilo"], PaperclipFalso(), cfg, capsys)[0] == 0


def test_pendencias_socio_desconhecido(cfg, capsys):
    codigo, saida = rodar(["pendencias", "fulano"], PaperclipFalso(), cfg, capsys)
    assert codigo == 1 and TELEFONE not in saida


# --- tarefa ---------------------------------------------------------------------------
def test_tarefa(cfg, capsys):
    longo = "x" * 500
    pc = PaperclipFalso(
        issues={"blocked": [issue()]},
        comentarios={"DGC-370": [{"body": "c1", "createdAt": "2026-11-25T15:00:00Z"},
                                 {"body": longo, "createdAt": "2026-11-24T15:00:00Z"}]},
        interacoes={"DGC-370": [{"id": "int-7", "status": "pending", "kind": "request_confirmation",
                                 "title": "Aprova?"},
                                {"id": "int-1", "status": "accepted", "title": "velha"}]},
    )
    codigo, saida = rodar(["tarefa", "DGC-370"], pc, cfg, capsys)
    assert codigo == 0
    assert "DGC-370" in saida and "blocked" in saida and "Contrato do piloto" in saida
    assert "25/11" in saida and "c1" in saida
    assert "x" * 299 + "…" in saida and "x" * 300 not in saida
    assert "int-7" in saida and "Aprova?" in saida
    assert "int-1" not in saida
    assert ("comentarios", "DGC-370", 3) in pc.chamadas


# --- uso e configuração -----------------------------------------------------------------
def test_uso_errado_nao_levanta(cfg, capsys):
    codigo, saida = rodar([], PaperclipFalso(), cfg, capsys)
    assert codigo == 2
    assert "uso" in saida.lower()


def test_ler_env(tmp_path):
    arq = tmp_path / "c.env"
    arq.write_text("# comentário\n\nPAPERCLIP_URL=http://x\nSOCIOS=a:1,b:2\nTOKEN = com=igual \n", encoding="utf-8")
    assert quadro.ler_env(arq) == {"PAPERCLIP_URL": "http://x", "SOCIOS": "a:1,b:2", "TOKEN": "com=igual"}


def test_main_sem_pc_le_arquivo_do_env(tmp_path, monkeypatch, capsys):
    arq = tmp_path / "cerebro.env"
    arq.write_text(f"SOCIOS=gabriel:{TELEFONE}\nCOTA_PATH={tmp_path / 'cota.json'}\n"
                   "PAPERCLIP_URL=http://127.0.0.1:1\nPAPERCLIP_TOKEN=t\nPAPERCLIP_COMPANY=c\n", encoding="utf-8")
    monkeypatch.setenv("CEREBRO_ENV", str(arq))
    assert quadro.main(["cota", "gabriel"], agora=AGORA) == 0
    assert capsys.readouterr().out == "pode\n"


def test_sem_arquivo_de_config(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CEREBRO_ENV", str(tmp_path / "nao-existe.env"))
    assert quadro.main(["pendencias", "gabriel"]) == 1
    assert "configura" in capsys.readouterr().out


# --- rodada de correções: sem stack trace, falha fechada --------------------------------
def test_erro_inesperado_vira_linha_curta_com_exit_1(cfg, capsys):
    pc = PaperclipFalso(erro=RuntimeError("segredo ghp_0123456789abcdefABCDEF0123456789abcd"))
    codigo, saida = rodar(["tarefa", "DGC-1"], pc, cfg, capsys)
    assert (codigo, saida) == (1, "erro inesperado: RuntimeError\n")


def test_cota_nao_gravavel_nao_gera_stack_trace(cfg, tmp_path, capsys):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("x")
    cfg["COTA_PATH"] = str(arquivo / "cota.json")  # o "diretório" é um arquivo comum
    codigo, saida = rodar(["enviei", "gabriel"], PaperclipFalso(), cfg, capsys)
    assert codigo == 1
    assert saida.startswith("erro inesperado: ")
    assert "Traceback" not in saida


def test_painel_com_bytes_invalidos_conta_como_vazio(cfg, tmp_path, capsys):
    (tmp_path / "PAINEL.md").write_bytes(b"\xff\xfe## Precisa do Gabriel\n\x80")
    assert rodar(["pendencias", "gabriel"], PaperclipFalso(), cfg, capsys) == (0, "nada pendente pro gabriel\n")


def test_env_com_bytes_invalidos_vira_erro_de_configuracao(tmp_path, monkeypatch, capsys):
    arq = tmp_path / "cerebro.env"
    arq.write_bytes(b"\xff\xfe=\x80")
    monkeypatch.setenv("CEREBRO_ENV", str(arq))
    assert quadro.main(["pendencias", "gabriel"]) == 1
    assert "configura" in capsys.readouterr().out


def test_issues_none_conta_como_lista_vazia(cfg, capsys):
    class SemLista(PaperclipFalso):
        def issues(self, status):
            return None

    assert rodar(["pendencias", "gabriel"], SemLista(), cfg, capsys) == (0, "nada pendente pro gabriel\n")


@pytest.mark.parametrize("erro", [QuadroForaDoAr("x"), QuadroRecusou(400, "x"), RuntimeError("x")])
def test_aprovar_com_comentario_falho_sai_com_4(cfg, capsys, erro):
    class ComentarioFalha(PaperclipFalso):
        def comentar(self, issue_id, texto):
            raise erro

    pc = ComentarioFalha()
    codigo, saida = rodar(["aprovar", "a", "DGC-1", "--socio", "gabriel"], pc, cfg, capsys)
    assert (codigo, saida) == (4, "aprovado, mas o comentário falhou\n")
    assert ("aprovar", "a") in pc.chamadas


def test_aceitar_com_comentario_falho_sai_com_4(cfg, capsys):
    class ComentarioFalha(PaperclipFalso):
        def comentar(self, issue_id, texto):
            raise QuadroForaDoAr("caiu")

    pc = ComentarioFalha()
    codigo, saida = rodar(["aceitar", "DGC-1", "i1", "--socio", "danilo"], pc, cfg, capsys)
    assert (codigo, saida) == (4, "aceito, mas o comentário falhou\n")


@pytest.mark.parametrize("socios", [None, "", " , "])
def test_sem_socios_configurados_falha_fechada(cfg, capsys, socios):
    if socios is None:
        del cfg["SOCIOS"]
    else:
        cfg["SOCIOS"] = socios
    for argv in (["cota", "gabriel"], ["enviei", "gabriel"], ["pendencias", "gabriel"],
                 ["aprovar", "a", "DGC-1", "--socio", "gabriel"]):
        pc = PaperclipFalso()
        codigo, saida = rodar(argv, pc, cfg, capsys)
        assert (codigo, saida) == (1, "falta SOCIOS no cerebro.env\n")
        assert pc.chamadas == []


def test_pendencias_pula_tarefa_recusada_e_conta(cfg, capsys):
    class UmaRecusa(PaperclipFalso):
        def comentarios(self, issue_id, limite=5):
            if issue_id == "DGC-1":
                raise QuadroRecusou(404, "sumiu")
            return super().comentarios(issue_id, limite)

        def interacoes(self, issue_id):
            if issue_id == "DGC-2":
                raise QuadroRecusou(403, "proibido")
            return super().interacoes(issue_id)

    pc = UmaRecusa(
        issues={"blocked": [issue("DGC-1"), issue("DGC-3", "Boa")], "todo": [issue("DGC-2", "x", "todo")]},
        comentarios={"DGC-3": [{"body": "esperando o Gabriel", "createdAt": "2026-11-23T15:00:00Z"}]},
    )
    codigo, saida = rodar(["pendencias", "gabriel"], pc, cfg, capsys)
    assert codigo == 0
    linhas = saida.splitlines()
    assert linhas[0].startswith("DGC-3 · bloqueada")
    assert linhas[-1] == "(2 tarefas não lidas)"


def test_pendencias_5xx_numa_tarefa_ainda_aborta(cfg, capsys):
    class Cai(PaperclipFalso):
        def comentarios(self, issue_id, limite=5):
            raise QuadroForaDoAr("caiu")

    codigo, saida = rodar(["pendencias", "gabriel"], Cai(issues={"blocked": [issue()]}), cfg, capsys)
    assert (codigo, saida) == (2, "quadro fora do ar\n")
