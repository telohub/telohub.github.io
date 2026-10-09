#!/usr/bin/env python3
"""Rebuild observatorio-acai.html from template.html + the domain data files
in this same directory (meta.json, blocos.json, normas.json, notas.json).

Usage:
    python3 build.py [output_path]

Default output_path is ../observatorio-acai.html (i.e. next to src/).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAINS = ("meta", "blocos", "normas", "notas")

# The closed sets each relation is allowed to range over. Not a type system —
# just the cheapest possible stand-in for one: every id a bloco or norma can
# point at, listed once, so a typo or a stale reference fails the build
# instead of silently rendering as an empty ring or a missing tag.
GRUPO_IDS = {"principal", "suprimentos", "auxiliar", "circular", "institucional"}
SISTEMA_IDS = {"normas", "urbana", "ambiental", "sanitario", "trabalhista", "tributario", "educacional"}
ELO_IDS = {f"e{i}" for i in range(1, 11)} | {"auxiliar", "apoio"}


def validate(seed):
    """Referential-integrity checks across the bloco/norma relations.

    bloco.sistemas and norma.elos are many-to-many relations stored as id
    lists on each record (see the concentric-circles refactor). A list is
    just strings to Python, so nothing stops a typo'd id from compiling —
    this function is what catches it instead, at build time rather than as
    a silently-empty drawer the user finds by clicking around.
    """
    errors = []

    ids = [b["id"] for b in seed["blocos"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"blocos com id duplicado: {sorted(dupes)}")

    for b in seed["blocos"]:
        if b["grupo"] not in GRUPO_IDS:
            errors.append(f"bloco {b['id']!r}: grupo desconhecido {b['grupo']!r}")
        for sid in b.get("sistemas", []):
            if sid not in SISTEMA_IDS:
                errors.append(f"bloco {b['id']!r}: sistema desconhecido {sid!r}")

    for i, n in enumerate(seed["normas"]):
        for eid in n.get("elos", []):
            if eid not in ELO_IDS:
                errors.append(f"norma #{i} ({n.get('titulo')!r}): elo desconhecido {eid!r}")

    if errors:
        raise SystemExit("Falhas de integridade referencial:\n  - " + "\n  - ".join(errors))


def build():
    with open(os.path.join(HERE, "template.html"), encoding="utf-8") as f:
        template = f.read()

    seed = {}
    for key in DOMAINS:
        with open(os.path.join(HERE, f"{key}.json"), encoding="utf-8") as f:
            seed[key] = json.load(f)

    validate(seed)

    seed_json = json.dumps(seed, ensure_ascii=False)

    placeholder = "__SEED_JSON__"
    count = template.count(placeholder)
    if count != 1:
        raise SystemExit(f"expected exactly 1 occurrence of {placeholder!r}, found {count}")

    return template.replace(placeholder, seed_json, 1)


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "observatorio-acai.html")
    html = build()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out_path} ({len(html)} chars)")
