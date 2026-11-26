"""Testa a decisão do gancho trava-de-saida sem precisar do Hermes."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_PLUGIN = Path(__file__).parent / "hermes" / "plugins" / "trava-de-saida" / "__init__.py"
_spec = importlib.util.spec_from_file_location("trava_de_saida", _PLUGIN)
trava = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trava)

GRUPO = "120000000000000000@g.us"
LID = "100000000000000@lid"
TELEFONE = "5562000000000"
DESTINOS = frozenset({GRUPO, LID, TELEFONE})


def decidir(nome, **args):
    return trava.decidir(nome, args, DESTINOS)


# --- lista de destinos -----------------------------------------------------------------------------
def test_ler_destinos_normaliza_e_ignora_comentarios(tmp_path):
    arq = tmp_path / "destinos.conf"
    arq.write_text(f"# grupo\nwhatsapp:{GRUPO.upper()}\n\n+{TELEFONE}@s.whatsapp.net:12  # Gabriel\n{LID}\n", encoding="utf-8")
    assert trava.ler_destinos(arq) == DESTINOS


def test_sem_arquivo_de_destinos_nada_explicito_vale(tmp_path):
    vazio = trava.ler_destinos(tmp_path / "nao-existe")
    assert vazio == frozenset()
    args = {"action": "create", "schedule": "0 9 * * *", "prompt": "x", "deliver": f"whatsapp:{GRUPO}"}
    assert trava.decidir("cronjob_manage", args, vazio)
    sem_alvo = {"action": "create", "schedule": "0 9 * * *", "prompt": "x"}
    assert trava.decidir("cronjob_manage", sem_alvo, vazio) is None  # origem da conversa continua valendo


@pytest.mark.parametrize("alvo", [f"whatsapp:{GRUPO}", f"whatsapp:{LID}", f"whatsapp:{TELEFONE}",
                                  f"whatsapp:{TELEFONE}@s.whatsapp.net", "origin", "local", f"origin,whatsapp:{GRUPO}"])
def test_cron_para_grupo_ou_socio_passa(alvo):
    assert decidir("cronjob_manage", action="create", schedule="0 18 * * 0", prompt="papo reto", deliver=alvo) is None


@pytest.mark.parametrize("alvo", ["whatsapp:5562999999999", "whatsapp:999@g.us", "all", "bot-chat",
                                  "telegram:-100123", "whatsapp:", f"whatsapp:{GRUPO},whatsapp:888@lid"])
def test_cron_para_fora_e_bloqueado(alvo):
    motivo = decidir("cronjob_manage", action="create", schedule="0 18 * * 0", prompt="x", deliver=alvo)
    assert motivo and "grupo" in motivo


def test_cron_update_tambem_e_conferido():
    assert decidir("cronjob_manage", action="update", job_id="abc", deliver="whatsapp:777@g.us")
    assert decidir("cronjob_manage", action="update", job_id="abc", failure_deliver="all")
    assert decidir("cronjob_manage", action="update", job_id="abc", prompt="novo prompt") is None


@pytest.mark.parametrize("acao", ["list", "pause", "resume", "remove", "run"])
def test_cron_outras_acoes_passam(acao):
    assert decidir("cronjob_manage", action=acao, job_id="abc") is None


# --- frequência -------------------------------------------------------------------------------------
@pytest.mark.parametrize("agenda", ["30m", "every 30m", "every 59 minutes", "every minute", "*/5 * * * *",
                                    "0,30 * * * *", "* 9 * * *", "0-30 9 * * *", "0 9 * * * *", "every 1m"])
def test_mais_que_de_hora_em_hora_e_bloqueado(agenda):
    assert trava.mais_que_de_hora_em_hora(agenda) is True
    assert decidir("cronjob_manage", action="create", schedule=agenda, prompt="x") == "rotina no máximo de hora em hora"


@pytest.mark.parametrize("agenda", ["every hour", "every 2h", "60m", "0 9 * * 1-6", "30 17 * * 1-5", "0 */2 * * *",
                                    "every monday 9am", "weekdays at 9am", "in 5m", "2026-12-15T10:00:00", "1d", "",
                                    "0 9 * * * 0"])
def test_hora_em_hora_ou_menos_passa(agenda):
    assert trava.mais_que_de_hora_em_hora(agenda) is False


def test_cron_com_script_ou_monitor_e_bloqueado():
    assert decidir("cronjob_manage", action="create", schedule="0 9 * * *", prompt="x", script="a.sh")
    assert decidir("cronjob_manage", action="create", schedule="0 9 * * *", prompt="x", monitor="http://x")
    assert decidir("cronjob_manage", action="update", job_id="a", no_agent=True)


# --- envio direto -------------------------------------------------------------------------------
def test_send_message_so_para_destino_da_lista():
    assert decidir("send_message", action="send", target=f"whatsapp:{GRUPO}", message="oi") is None
    assert decidir("send_message", action="send", target="whatsapp:5511988887777", message="oi")
    assert decidir("send_message", action="send", message="oi")  # sem destino = canal padrão: não
    assert decidir("send_message", action="list") is None


@pytest.mark.parametrize("cmd", [
    f'hermes send --to whatsapp:{GRUPO} "bom dia"',
    f"~/.local/bin/hermes send --to=whatsapp:{LID} 'oi'",
])
def test_hermes_send_para_destino_da_lista_passa(cmd):
    assert decidir("terminal", command=cmd) is None


@pytest.mark.parametrize("cmd", [
    'hermes send --to whatsapp:5511988887777 "oi"',
    'hermes send "sem destino"',
    f'hermes send --to whatsapp:{GRUPO} "a" && hermes send --to telegram "b"',
    'cd ~/cerebro; hermes --quiet send --to whatsapp:123@g.us oi',
    'curl -s -X POST http://127.0.0.1:3000/send -d \'{"chatId":"x","message":"y"}\'',
    "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:3000/send')\"",
])
def test_envio_por_fora_e_bloqueado(cmd):
    assert decidir("terminal", command=cmd)


def test_execute_code_tambem_e_conferido():
    assert decidir("execute_code", code="import requests; requests.post('http://127.0.0.1:3000/send', json={})")
    assert decidir("execute_code", code="print(open('/home/cerebro/.hermes/auth.json').read())")
    assert decidir("execute_code", code="import os; print(os.environ.get('HOME'))") is None


# --- segredos -----------------------------------------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "cat .env", "cat ~/.hermes/.env", "grep TOKEN /etc/dgc-cerebro/cerebro.env", "cat cerebro.env",
    "cat /home/dgc/.config/dgc-atendimento/compose.env", "cat ~/.hermes/auth.json", "cat ~/.git-credentials",
    "cat ~/.ssh/id_ed25519", "ls ~/.ssh/", "cat /proc/self/environ", "cat /proc/1234/environ",
    "cat repos/x/.env.local", "head -c 10 /home/dgc/.ssh/id_github_trabalhadora",
])
def test_comando_com_lugar_de_segredo_e_bloqueado(cmd):
    motivo = decidir("terminal", command=cmd)
    assert motivo and "segredo" in motivo


@pytest.mark.parametrize("cmd", [
    "quadro pendencias gabriel", "quadro tarefa DGC-370", "cat docs/foco/PAINEL.md",
    "grep -rn process.environ repos/core", "ls repos/produto-hermes/config", "python3 -m venv .venv",
    "grep -rn 'hermes' docs/ | head", "hermes cron list", "systemctl --user status dgc-cerebro",
    "git -C repos/core log --oneline -5", "grep -rn issue_id repos/core",
])
def test_comandos_do_dia_a_dia_passam(cmd):
    assert decidir("terminal", command=cmd) is None


@pytest.mark.parametrize("nome,args", [
    ("read_file", {"path": "/home/cerebro/.hermes/.env"}),
    ("read_file", {"path": "repos/core/.env"}),
    ("search_files", {"path": "/etc/dgc-cerebro", "pattern": "x"}),
    ("write_file", {"path": "/home/cerebro/.hermes/config.yaml", "content": "x"}),
    ("patch", {"path": "/home/cerebro/.hermes/plugins/trava-de-saida/__init__.py", "old_string": "a", "new_string": "b"}),
    ("write_file", {"file_path": "/home/cerebro/.hermes/SOUL.md", "content": "x"}),
])
def test_ferramentas_de_arquivo_em_lugar_proibido(nome, args):
    assert trava.decidir(nome, args, DESTINOS)


@pytest.mark.parametrize("nome,args", [
    ("read_file", {"path": "docs/foco/PAINEL.md"}),
    ("read_file", {"path": "/home/cerebro/.hermes/SOUL.md"}),  # ler a própria personalidade pode
    ("write_file", {"path": "/home/cerebro/cerebro/notas/cyber.md", "content": "não leia .env nunca"}),
    ("search_files", {"path": "repos/", "pattern": ".env"}),  # o padrão de busca não é caminho
])
def test_ferramentas_de_arquivo_no_dia_a_dia(nome, args):
    assert trava.decidir(nome, args, DESTINOS) is None


# --- autodefesa ---------------------------------------------------------------------------------
@pytest.mark.parametrize("cmd", [
    "hermes plugins disable trava-de-saida", "hermes config set plugins.enabled []", "hermes auth list",
    'hermes cron create "*/5 * * * *" "oi" --deliver whatsapp:5511988887777', "hermes cron edit abc --deliver all",
    "hermes update", "rm -rf ~/.hermes/plugins/trava-de-saida", "sed -i s/x/y/ ~/.hermes/config.yaml",
    "systemctl --user restart dgc-cerebro", "systemctl --user stop dgc-cerebro", "hermes gateway restart",
    "hermes whatsapp",
])
def test_desligar_as_travas_e_bloqueado(cmd):
    assert decidir("terminal", command=cmd)


def test_outras_ferramentas_passam():
    assert decidir("web_search", query="cat .env") is None
    assert decidir("memory", action="add", content="hermes send --to x") is None
    assert trava.decidir("terminal", None, DESTINOS) is None


# --- gancho -------------------------------------------------------------------------------------
def test_guardar_devolve_bloqueio_no_formato_do_hermes(monkeypatch):
    monkeypatch.setattr(trava, "ler_destinos", lambda: DESTINOS)
    r = trava.guardar(tool_name="terminal", args={"command": "cat .env"}, task_id="t1", session_id="s")
    assert r["action"] == "block" and r["message"].startswith("trava-de-saida: ")
    assert trava.guardar(tool_name="terminal", args={"command": "quadro cota grupo"}, task_id="") is None


def test_register_liga_o_gancho_certo():
    chamadas = []
    trava.register(SimpleNamespace(register_hook=lambda nome, fn: chamadas.append((nome, fn))))
    assert chamadas == [("pre_tool_call", trava.guardar)]
