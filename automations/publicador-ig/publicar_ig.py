#!/usr/bin/env python3
"""Publica sozinho, no Instagram @dgc_hub, os carrosséis e posts da agenda. Reels ficam com o Gabriel, no app
(a API publica reel em 720p e não põe música do Instagram). Decisão do Gabriel em 19/11/2026.

Roda no servidor da DGC (o do Paperclip), na pasta ~/dgc-ig, chamado pelo cron a cada 10 min. Só biblioteca padrão.

Uso: python3 publicar_ig.py <comando>
  conta                  confere o token: mostra o @ e o id da conta (nada é publicado)
  listar                 mostra a agenda e o que o robô faria com cada peça agora
  rodar [--aplicar]      publica o que estiver na hora (é o que o cron chama); sem --aplicar só simula
  testar <id>            sobe as imagens e monta os contêineres SEM publicar (confere imagem, legenda e formato)
  publicar <id> --aplicar   publica a peça já, fora do horário (para repor uma que falhou)
  renovar                renova o token se já passou 7 dias (o cron chama junto com o rodar)

Regras: cada peça sai uma vez só (registro.json); passou JANELA_HORAS do horário e não saiu, o robô não publica
atrasado: registra e espera alguém decidir; o arquivo PAUSAR nesta pasta para tudo; só publica se o token for do
@dgc_hub. Para o Instagram buscar as imagens, abre um link público temporário (túnel rápido da Cloudflare) só
durante a publicação e fecha logo depois. Nunca imprime o token.
"""
import contextlib
import datetime as dt
import fcntl
import functools
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
API = "https://graph.instagram.com/v24.0"
CONTA_ESPERADA = "dgc_hub"
JANELA_HORAS = 3
TUNEL_IMAGEM = "cloudflare/cloudflared:2026.10.7"
TIPOS = ("Carrossel", "Post")


# ── arquivos ────────────────────────────────────────────────────────────────────────────────────────────────────────
def agora() -> dt.datetime:
    return dt.datetime.now()


def diz(msg: str) -> None:
    linha = f"{agora():%d/%m %H:%M} {msg}"
    print(linha)
    with open(AQUI / "publicar.log", "a") as f:
        f.write(linha + "\n")


def ler_json(nome: str, padrao):
    arq = AQUI / nome
    return json.loads(arq.read_text()) if arq.exists() else padrao


def gravar_json(nome: str, dado) -> None:
    tmp = AQUI / (nome + ".tmp")
    tmp.write_text(json.dumps(dado, ensure_ascii=False, indent=1))
    tmp.replace(AQUI / nome)


def agenda() -> list[dict]:
    pecas = ler_json("agenda.json", [])
    for p in pecas:
        p["quando_dt"] = dt.datetime.strptime(p["quando"], "%Y-%m-%d %H:%M")
    return sorted(pecas, key=lambda p: p["quando_dt"])


def imagens(p: dict) -> list[Path]:
    return sorted((AQUI / "pecas" / p["pasta"]).glob("*.*"))


def validar(p: dict, imgs: list[Path]) -> None:
    if p["tipo"] not in TIPOS:
        raise ValueError(f"{p['id']}: tipo {p['tipo']} (use {TIPOS})")
    if p["tipo"] == "Carrossel" and not 2 <= len(imgs) <= 10:
        raise ValueError(f"{p['id']}: carrossel com {len(imgs)} imagens (2 a 10)")
    if p["tipo"] == "Post" and len(imgs) != 1:
        raise ValueError(f"{p['id']}: post com {len(imgs)} imagens (1)")
    if any(f.suffix.lower() not in (".jpg", ".jpeg") for f in imgs):
        raise ValueError(f"{p['id']}: o Instagram só aceita JPEG")
    if len(p["legenda"]) > 2200:
        raise ValueError(f"{p['id']}: legenda com {len(p['legenda'])} caracteres (máximo 2200)")
    if len(re.findall(r"#\w+", p["legenda"])) > 30:
        raise ValueError(f"{p['id']}: hashtags demais (máximo 30)")


def situacao(p: dict, reg: dict, quando: dt.datetime) -> tuple[bool, str]:
    if reg.get(p["id"], {}).get("id"):
        return False, f"publicada {reg[p['id']].get('quando', '')} {reg[p['id']].get('link', '')}".strip()
    if p.get("suspensa"):
        return False, "suspensa"
    hora = dt.datetime.strptime(p["quando"], "%Y-%m-%d %H:%M")
    if quando < hora:
        return False, f"agendada {hora:%d/%m %H:%M}"
    if quando > hora + dt.timedelta(hours=JANELA_HORAS):
        return False, f"ATRASADA: era {hora:%d/%m %H:%M} e não saiu; publique com 'publicar {p['id']} --aplicar' ou suspenda"
    return True, "na hora"


# ── token ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def token() -> str:
    for linha in (AQUI / ".env").read_text().splitlines():
        if linha.startswith("IG_TOKEN="):
            return linha.split("=", 1)[1].strip()
    raise SystemExit("falta IG_TOKEN no .env")


def precisa_renovar(estado: dict, hoje: dt.date) -> bool:
    feito = estado.get("renovado_em")
    return not feito or (hoje - dt.date.fromisoformat(feito)).days >= 7


def renovar() -> None:
    estado = ler_json("token.json", {})
    if not precisa_renovar(estado, dt.date.today()):
        return
    r = chamar("GET", "https://graph.instagram.com/refresh_access_token", grant_type="ig_refresh_token")
    if "access_token" not in r:
        diz(f"renovação do token FALHOU: {json.dumps(r)[:300]}")
        return
    env = AQUI / ".env"
    linhas = [ln for ln in env.read_text().splitlines() if not ln.startswith("IG_TOKEN=")]
    env.write_text("\n".join([f"IG_TOKEN={r['access_token']}", *linhas]) + "\n")
    env.chmod(0o600)
    gravar_json("token.json", {"renovado_em": dt.date.today().isoformat(), "vale_dias": r.get("expires_in", 0) // 86400})
    diz("token renovado")


# ── API do Instagram ────────────────────────────────────────────────────────────────────────────────────────────────
def chamar(metodo: str, url: str, **campos) -> dict:
    campos["access_token"] = token()
    dados = urllib.parse.urlencode(campos)
    if metodo == "GET":
        req = urllib.request.Request(f"{url}?{dados}")
    else:
        req = urllib.request.Request(url, data=dados.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"erro_http": e.code, **json.loads(e.read() or b"{}")}


def conta() -> dict:
    r = chamar("GET", f"{API}/me", fields="user_id,username")
    if r.get("username") != CONTA_ESPERADA:
        raise SystemExit(f"o token não é do @{CONTA_ESPERADA}: {json.dumps(r)[:300]}")
    return r


def falha(rotulo: str, r: dict):
    raise RuntimeError(f"{rotulo} FALHOU: {json.dumps(r, ensure_ascii=False)[:600]}")


def espera(cid: str, rotulo: str) -> None:
    for _ in range(60):
        st = chamar("GET", f"{API}/{cid}", fields="status_code")
        if st.get("status_code") in ("FINISHED", None):
            return
        if st.get("status_code") == "ERROR":
            falha(f"{rotulo} (processamento)", st)
        time.sleep(5)
    falha(f"{rotulo} (processamento demorou)", {})


# ── link público temporário ─────────────────────────────────────────────────────────────────────────────────────────
def url_tunel(log: str) -> str | None:
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", log)
    return m.group(0) if m else None


@contextlib.contextmanager
def link_publico(pasta: Path):
    """Serve só a pasta da peça em 127.0.0.1 e abre um túnel rápido da Cloudflare até ela; fecha tudo na saída."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(pasta))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    nome = f"dgc-ig-tunel-{os.getpid()}"
    subprocess.run(["docker", "run", "-d", "--rm", "--name", nome, "--network", "host", TUNEL_IMAGEM, "tunnel",
                    "--no-autoupdate", "--url", f"http://127.0.0.1:{srv.server_port}"],
                   check=True, capture_output=True)
    try:
        url = None
        for _ in range(60):
            log = subprocess.run(["docker", "logs", nome], capture_output=True, text=True).stderr
            url = url_tunel(log)
            if url and "Registered tunnel connection" in log:
                break
            time.sleep(1)
        else:
            raise RuntimeError("o túnel não abriu em 60 s")
        time.sleep(10)  # o nome novo leva alguns segundos para valer no DNS
        yield url
    finally:
        subprocess.run(["docker", "stop", nome], capture_output=True)
        srv.shutdown()


# ── publicação ──────────────────────────────────────────────────────────────────────────────────────────────────────
def montar(p: dict, ig: str) -> tuple[str, int]:
    """Cria os contêineres no Instagram e devolve o id do contêiner final (nada é publicado aqui)."""
    imgs = imagens(p)
    validar(p, imgs)
    with link_publico(AQUI / "pecas" / p["pasta"]) as base:
        urls = [f"{base}/{urllib.parse.quote(f.name)}" for f in imgs]
        if p["tipo"] == "Post":
            c = chamar("POST", f"{API}/{ig}/media", image_url=urls[0], caption=p["legenda"])
            if "id" not in c:
                falha("contêiner", c)
        else:
            filhos = []
            for i, u in enumerate(urls, 1):
                f = chamar("POST", f"{API}/{ig}/media", image_url=u, is_carousel_item="true")
                if "id" not in f:
                    falha(f"cartão {i}", f)
                espera(f["id"], f"cartão {i}")
                filhos.append(f["id"])
            c = chamar("POST", f"{API}/{ig}/media", media_type="CAROUSEL", children=",".join(filhos),
                       caption=p["legenda"])
            if "id" not in c:
                falha("contêiner do carrossel", c)
        espera(c["id"], "contêiner")
    return c["id"], len(imgs)


def publicar(p: dict) -> None:
    ig = conta()["user_id"]
    cid, n = montar(p, ig)
    r = chamar("POST", f"{API}/{ig}/media_publish", creation_id=cid)
    if "id" not in r:
        falha("publicação", r)
    info = chamar("GET", f"{API}/{r['id']}", fields="permalink,media_type,caption")
    ok = (info.get("caption") or "").strip() == p["legenda"].strip()
    reg = ler_json("registro.json", {})
    reg[p["id"]] = {"id": r["id"], "link": info.get("permalink"), "quando": f"{agora():%d/%m/%Y %H:%M}",
                    "imagens": n, "legenda_conferida": ok}
    gravar_json("registro.json", reg)
    diz(f"{p['id']} PUBLICADA {info.get('permalink')} · {n} imagem(ns) · legenda {'OK' if ok else 'DIFERENTE: olhar'}")


def main() -> None:
    a = sys.argv[1:]
    cmd = a[0] if a else "listar"
    aplicar = "--aplicar" in a
    trava = open(AQUI / ".trava", "w")
    fcntl.flock(trava, fcntl.LOCK_EX)  # o cron nunca roda duas vezes ao mesmo tempo
    reg = ler_json("registro.json", {})
    if cmd == "conta":
        print(conta())
    elif cmd == "listar":
        for p in agenda():
            pode, motivo = situacao(p, reg, agora())
            print(f"{p['id']:4} {p['quando_dt']:%a %d/%m %H:%M} {p['tipo']:9} {p.get('tema', '')[:36]:36} "
                  f"→ {'PUBLICARIA AGORA' if pode else motivo}")
    elif cmd == "rodar":
        if (AQUI / "PAUSAR").exists():
            print("pausado (arquivo PAUSAR)")
            return
        renovar()
        for p in agenda():
            pode, motivo = situacao(p, reg, agora())
            if motivo.startswith("ATRASADA") and not reg.get(p["id"], {}).get("avisada"):
                diz(f"{p['id']} {motivo}")
                reg.setdefault(p["id"], {})["avisada"] = True
                gravar_json("registro.json", reg)
            if not pode:
                continue
            if not aplicar:
                print(f"{p['id']} seria publicada agora (simulação)")
                continue
            try:
                publicar(p)
            except Exception as e:  # uma peça com problema não segura as outras
                diz(f"{p['id']} ERRO: {e}")
    elif cmd == "testar":
        p = next(x for x in agenda() if x["id"] == a[1])
        ig = conta()["user_id"]
        cid, n = montar(p, ig)
        print(f"{p['id']}: contêiner {cid} pronto com {n} imagem(ns); NÃO publicado")
    elif cmd == "publicar" and aplicar:
        publicar(next(x for x in agenda() if x["id"] == a[1]))
    elif cmd == "renovar":
        renovar()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
