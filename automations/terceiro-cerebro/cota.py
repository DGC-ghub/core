"""Teto de mensagens espontâneas por sócio: no máximo 3 por dia, entre 08:00 e 21:00 (Brasília).

Estado em JSON: {"<socio>": {"dia": "aaaa-mm-dd", "n": int}}. Arquivo ausente ou
corrompido vale como estado vazio (o teto recomeça, em vez de travar o robô).
"""
import json
import os
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
TETO_POR_DIA = 3
ABRE = time(8, 0)
FECHA = time(21, 0)  # 21:00 já está fora


class Cota:
    def __init__(self, caminho: Path):
        self._caminho = Path(caminho)

    def _ler(self) -> dict:
        try:
            estado = json.loads(self._caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return estado if isinstance(estado, dict) else {}

    def _enviadas_no_dia(self, estado: dict, socio: str, dia: str) -> int:
        registro = estado.get(socio)
        if not isinstance(registro, dict) or registro.get("dia") != dia:
            return 0
        n = registro.get("n")
        return n if isinstance(n, int) and n > 0 else 0

    def pode_enviar(self, socio: str, agora: datetime) -> bool:
        local = agora.astimezone(FUSO)
        if not (ABRE <= local.time() < FECHA):
            return False
        dia = local.date().isoformat()
        return self._enviadas_no_dia(self._ler(), socio, dia) < TETO_POR_DIA

    def registrar(self, socio: str, agora: datetime) -> None:
        dia = agora.astimezone(FUSO).date().isoformat()
        estado = self._ler()
        estado[socio] = {"dia": dia, "n": self._enviadas_no_dia(estado, socio, dia) + 1}
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self._caminho.with_name(self._caminho.name + ".tmp")
        temporario.write_text(json.dumps(estado), encoding="utf-8")
        os.replace(temporario, self._caminho)
