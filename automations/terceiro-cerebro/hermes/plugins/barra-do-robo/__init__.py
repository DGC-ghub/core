"""barra-do-robo: o Hermes nunca responde a "/comando" no WhatsApp.

Texto que começa com "/" é do robô de vendas. O gateway do Hermes trataria esse texto antes do modelo
(executaria os comandos dele ou responderia "comando desconhecido"), então o gancho `pre_gateway_dispatch`
descarta a mensagem na entrada. Também descarta o que o dono do aparelho digitou (fromOwner); a ponte do
WhatsApp já ignora o que o próprio número envia (modo bot), isto é só uma segunda trava.
Qualquer outra mensagem segue o caminho normal.
"""


def _plataforma(event) -> str:
    plataforma = getattr(getattr(event, "source", None), "platform", None)
    return str(getattr(plataforma, "value", plataforma) or "").lower()


def ignorar_barra(event, **kwargs):
    """Devolve {"action": "skip", ...} para comando com barra e mensagem do dono; senão None."""
    if _plataforma(event) != "whatsapp":
        return None
    texto = getattr(event, "text", None) or ""
    if texto.lstrip().startswith("/"):
        return {"action": "skip", "reason": "barra-do-robo: comando do robo de vendas"}
    metadata = getattr(event, "metadata", None) or {}
    if isinstance(metadata, dict) and metadata.get("whatsapp_from_owner"):
        return {"action": "skip", "reason": "barra-do-robo: mensagem do proprio aparelho"}
    return None


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", ignorar_barra)
