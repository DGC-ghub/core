"""Teto de mensagens espontâneas por sócio: no máximo 3 por dia, entre 08:00 e 21:00 (Brasília).

Estado em JSON: {"<socio>": {"dia": "aaaa-mm-dd", "n": int}, "_intervencao": {"ultima": "<iso>"}}.
"_intervencao" guarda só a hora da última intervenção espontânea no grupo (no máximo 1 por hora), à parte da
contagem do dia. Arquivo ausente ou corrompido vale como estado vazio (o teto recomeça, em vez de travar o robô).
"""
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")
TETO_POR_DIA = 3
ABRE = time(8, 0)
FECHA = time(21, 0)  # 21:00 já está fora
INTERVALO_DA_INTERVENCAO = timedelta(minutes=60)
_INTERVENCAO = "_intervencao"  # chave do estado; começa com "_" para nunca colidir com nome de sócio


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

    @contextmanager
    def _trava(self):
        """Trava exclusiva entre processos (flock num arquivo irmão) para ler e gravar."""
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        lock = self._caminho.with_name(self._caminho.name + ".lock")
        with open(lock, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    @staticmethod
    def _na_janela(local: datetime) -> bool:
        return ABRE <= local.time() < FECHA

    def _pode(self, socio: str, agora: datetime) -> bool:
        local = agora.astimezone(FUSO)
        if not self._na_janela(local):
            return False
        dia = local.date().isoformat()
        return self._enviadas_no_dia(self._ler(), socio, dia) < TETO_POR_DIA

    def _gravar_contagem(self, socio: str, agora: datetime, intervencao: bool = False) -> None:
        dia = agora.astimezone(FUSO).date().isoformat()
        estado = self._ler()
        estado[socio] = {"dia": dia, "n": self._enviadas_no_dia(estado, socio, dia) + 1}
        if intervencao:
            estado[_INTERVENCAO] = {"ultima": agora.isoformat()}
        self._gravar(estado)

    def _gravar(self, estado: dict) -> None:
        fd, temporario = tempfile.mkstemp(
            dir=self._caminho.parent, prefix=self._caminho.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(estado, f)
            os.replace(temporario, self._caminho)
        except BaseException:
            try:
                os.unlink(temporario)
            except OSError:
                pass
            raise

    def pode_enviar(self, socio: str, agora: datetime) -> bool:
        with self._trava():
            return self._pode(socio, agora)

    def registrar(self, socio: str, agora: datetime) -> None:
        with self._trava():
            self._gravar_contagem(socio, agora)

    def reservar(self, socio: str, agora: datetime) -> bool:
        """Confere a janela e o teto e já registra, tudo sob a mesma trava.

        Devolve False (sem registrar) se a janela está fechada ou o teto foi atingido.
        """
        with self._trava():
            if not self._pode(socio, agora):
                return False
            self._gravar_contagem(socio, agora)
            return True

    def _ultima_intervencao(self) -> datetime | None:
        registro = self._ler().get(_INTERVENCAO)
        try:
            quando = datetime.fromisoformat(registro["ultima"])
        except (TypeError, KeyError, ValueError):
            return None
        return quando if quando.tzinfo else None

    def intervir(self, chave: str, agora: datetime) -> str:
        """Reserva uma intervenção espontânea: "pode" (registrou), "espera" (menos de 60 min da última) ou "esgotada".

        Conta no teto do dia de `chave` (o grupo) e guarda a hora, tudo sob a mesma trava. "espera" e "esgotada" não
        registram nada.
        """
        with self._trava():
            ultima = self._ultima_intervencao()
            if ultima is not None and timedelta(0) <= agora - ultima < INTERVALO_DA_INTERVENCAO:
                return "espera"
            if not self._pode(chave, agora):
                return "esgotada"
            self._gravar_contagem(chave, agora, intervencao=True)
            return "pode"
