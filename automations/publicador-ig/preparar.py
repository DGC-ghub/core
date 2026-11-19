#!/usr/bin/env python3
"""Prepara uma peça para o publicador, aqui na Pi: converte os PNG em JPEG (o Instagram só aceita JPEG), copia para
saida/pecas/<id>/ e põe a peça na saida/agenda.json. Depois é só enviar a pasta saida/ para o servidor.

Uso: python3 preparar.py <id> "<AAAA-MM-DD HH:MM>" <Carrossel|Post> <pasta_dos_png> <legenda.txt> [tema]
Envio: rsync -a saida/ daniloservi@100.117.24.11:dgc-ig/
"""
import json
import sys
from pathlib import Path

from PIL import Image

import publicar_ig as p

SAIDA = Path(__file__).resolve().parent / "saida"


def main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit(__doc__)
    pid, quando, tipo, pasta, legenda = sys.argv[1:6]
    tema = sys.argv[6] if len(sys.argv) > 6 else ""
    destino = SAIDA / "pecas" / pid
    destino.mkdir(parents=True, exist_ok=True)
    for velho in destino.glob("*"):
        velho.unlink()
    for i, png in enumerate(sorted(Path(pasta).glob("*.png"), key=lambda f: int(f.stem.rsplit("-", 1)[-1])), 1):
        Image.open(png).convert("RGB").save(destino / f"{pid}-{i:02d}.jpg", "JPEG", quality=95, subsampling=0)
    peca = {"id": pid, "quando": quando, "tipo": tipo, "pasta": pid, "tema": tema,
            "legenda": Path(legenda).read_text().strip()}
    p.validar(peca, sorted(destino.glob("*.jpg")))
    arq = SAIDA / "agenda.json"
    agenda = [x for x in (json.loads(arq.read_text()) if arq.exists() else []) if x["id"] != pid]
    arq.write_text(json.dumps(sorted([*agenda, peca], key=lambda x: x["quando"]), ensure_ascii=False, indent=1))
    print(f"{pid}: {len(list(destino.glob('*.jpg')))} imagem(ns), {len(peca['legenda'])} caracteres → {arq}")


if __name__ == "__main__":
    main()
