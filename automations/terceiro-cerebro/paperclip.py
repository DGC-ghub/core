"""Cliente mínimo da API REST do Paperclip (o quadro de tarefas).

Rotas e campos confirmados lendo o código do servidor (build 2026.1106.0,
server/dist/routes/issues.js e approvals.js; sem chamar a API). Todas ficam
sob /api e pedem `Authorization: Bearer <board API key>`:

  GET   /companies/:companyId/issues?status=a,b
        Devolve uma lista JSON de issues (até 500 por padrão). `status` aceita
        vários valores separados por vírgula. Campos usados: id, identifier
        ("DGC-370"), title, status, updatedAt.
  GET   /issues/:id
        `:id` aceita o identificador ("DGC-370") ou o UUID: o servidor resolve
        o identificador em todas as rotas /issues/:id/... (router.param).
        Por isso este cliente NÃO precisa resolver por lista.
  GET   /issues/:id/comments?order=desc&limit=N
        Lista JSON de comentários. Campos: id, body, createdAt, authorAgentId,
        authorUserId. `order` é asc|desc (padrão desc = mais novo primeiro);
        `limit` vai até 500.
  POST  /issues/:id/comments            corpo {"body": "<texto>"}
  PATCH /issues/:id                     corpo {"status": "<status>"}
  GET   /issues/:id/interactions
        Lista JSON. Campos: id, kind (suggest_tasks, ask_user_questions,
        request_confirmation, request_checkbox_confirmation,
        request_item_verdicts, connection_intent), status (pending, accepted,
        rejected, answered, cancelled, expired, failed), title, summary,
        payload, createdAt, resolvedAt.
  POST  /issues/:id/interactions/:interactionId/accept    corpo {} (campos
        opcionais: selectedClientKeys, selectedOptionIds, rememberAction)
  POST  /approvals/:id/approve          corpo {} (opcional: decisionNote)

Erros do servidor: 4xx traz {"error": "..."}.
"""
import http.client
import json
import urllib.error
import urllib.parse
import urllib.request

from mascarar import SEGREDO, mascarar

TEMPO_LIMITE = 20  # segundos


class QuadroForaDoAr(Exception):
    """Erro de rede, resposta ilegível ou HTTP 5xx: o quadro não respondeu direito."""


class QuadroRecusou(Exception):
    """O quadro respondeu com 4xx (pedido recusado). `codigo` guarda o HTTP."""

    def __init__(self, codigo: int, detalhe: str):
        super().__init__(f"Paperclip recusou o pedido (HTTP {codigo}): {detalhe}")
        self.codigo = codigo


class Paperclip:
    def __init__(self, base: str, token: str, company_id: str, abrir=urllib.request.urlopen):
        self._base = base.rstrip("/")
        self._token = token
        self._company = company_id
        self._abrir = abrir

    # --- leitura -----------------------------------------------------------
    def issues(self, status: list[str]) -> list[dict]:
        filtro = urllib.parse.quote(",".join(status), safe=",_")
        return self._pedir("GET", f"/companies/{self._company}/issues?status={filtro}")

    def issue(self, ident: str) -> dict:
        return self._pedir("GET", f"/issues/{self._id(ident)}")

    def comentarios(self, issue_id: str, limite: int = 5) -> list[dict]:
        """Os `limite` comentários mais novos, do mais novo para o mais antigo."""
        return self._pedir("GET", f"/issues/{self._id(issue_id)}/comments?order=desc&limit={int(limite)}")

    def interacoes(self, issue_id: str) -> list[dict]:
        return self._pedir("GET", f"/issues/{self._id(issue_id)}/interactions")

    # --- escrita -----------------------------------------------------------
    def comentar(self, issue_id: str, texto: str) -> None:
        self._pedir("POST", f"/issues/{self._id(issue_id)}/comments", {"body": texto})

    def mudar_status(self, issue_id: str, status: str) -> None:
        self._pedir("PATCH", f"/issues/{self._id(issue_id)}", {"status": status})

    def aceitar_interacao(self, issue_id: str, interacao_id: str) -> None:
        self._pedir("POST", f"/issues/{self._id(issue_id)}/interactions/{self._id(interacao_id)}/accept", {})

    def aprovar(self, approval_id: str) -> None:
        self._pedir("POST", f"/approvals/{self._id(approval_id)}/approve", {})

    # --- interno -----------------------------------------------------------
    @staticmethod
    def _id(valor: str) -> str:
        return urllib.parse.quote(str(valor), safe="")

    def _limpar(self, texto: str) -> str:
        """Tira o token literal (se vazou) e mascara os padrões de segredo."""
        texto = str(texto)
        if self._token:
            texto = texto.replace(self._token, SEGREDO)
        return mascarar(texto)

    def _limpar_tudo(self, dado):
        if isinstance(dado, str):
            return self._limpar(dado)
        if isinstance(dado, list):
            return [self._limpar_tudo(x) for x in dado]
        if isinstance(dado, dict):
            return {k: self._limpar_tudo(v) for k, v in dado.items()}
        return dado

    def _pedir(self, metodo: str, caminho: str, corpo: dict | None = None):
        cabecalhos = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        dados = None
        if corpo is not None:
            dados = json.dumps(corpo).encode()
            cabecalhos["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{self._base}/api{caminho}", data=dados, headers=cabecalhos, method=metodo)
        try:
            with self._abrir(req, timeout=TEMPO_LIMITE) as resp:
                bruto = resp.read()
            return self._limpar_tudo(json.loads(bruto)) if bruto.strip() else None
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                raise QuadroForaDoAr(f"Paperclip fora do ar (HTTP {e.code})") from None
            # mascara primeiro e só depois corta, para não deixar pedaço de segredo na emenda
            raise QuadroRecusou(e.code, self._limpar(self._ler_erro(e))[:300]) from None
        except (OSError, ValueError, http.client.HTTPException) as e:  # rede, timeout, JSON inválido, resposta cortada
            raise QuadroForaDoAr(f"Paperclip fora do ar: {self._limpar(e)}") from None

    @staticmethod
    def _ler_erro(e: urllib.error.HTTPError) -> str:
        try:
            return e.read().decode("utf-8", "replace")
        except Exception:
            return str(e.reason)
