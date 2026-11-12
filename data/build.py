#!/usr/bin/env python3
"""Rebuild observatorio-acai.html from template.html + the domain data files
in this same directory (meta.json, modelo.json, blocos.json, normas.json,
notas.json, siglas.json).

Usage:
    python3 build.py [output_path]

Default output_path is ../observatorio-acai.html (i.e. next to src/).
"""
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAINS = ("meta", "modelo", "blocos", "normas", "notas", "siglas")

# O vocabulário do documento (quais grupos/raias, sistemas de contexto e
# etiquetas de elo existem) mora em modelo.json — é dado, não código. Só duas
# coisas continuam fixas aqui porque espelham o template:
#   COR_SLOTS  os "slots" de paleta que o CSS sabe pintar (--cat-<slot> e
#              --cat-<slot>-soft, com variantes de modo escuro). Um grupo
#              escolhe um slot; não existe cor livre. Novo slot = mudança de CSS.
#   TIPOS_ELO  "bloco": a etiqueta é o id de um bloco (ex.: e1…e10);
#              "agregado": etiqueta que reúne vários (ex.: auxiliar, apoio).
COR_SLOTS = {"principal", "sup", "aux", "apoio", "neutro"}
TIPOS_ELO = {"bloco", "agregado"}
# Atalhos que o campo "elos" da tabela de normas já entende por conta própria.
ATALHOS_ELOS = {"todos", "t"}
# Vistas (modelo.vistas): o TIPO é código (um renderizador no template); o
# resto — nome no menu, título, introdução, colunas, rótulos — é dado.
#   diagrama  o diagrama da cadeia (raias e/ou anéis do ecossistema); no máx. 1
#   normas    a tabela de normas com busca e filtros; no máx. 1
#   cartoes   cartões com os blocos de um grupo (campo "grupo"); quantas quiser
#   lista     lista editável de itens (campo "fonte"); quantas quiser
TIPOS_VISTA = {"diagrama", "normas", "cartoes", "lista"}
VISTAS_UNICAS = {"diagrama", "normas"}  # ids de DOM únicos no template
COMPONENTES_DIAGRAMA = {"ecossistema", "raias"}
FONTES_LISTA = {"notas"}
COLUNAS_NORMAS = ("esfera", "norma", "resumo", "elos")
ROTULOS_NORMAS = ("busca", "buscaAria", "contagem", "adicionar", "filtroElo", "aConferir", "verElo", "verAplicavel")
RE_ID_VISTA = re.compile(r"^[a-z][a-z0-9-]*$")
RE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _txt(v):
    return isinstance(v, str) and v.strip() != ""


def _ids(lista):
    return [x.get("id") for x in lista if isinstance(x, dict)]


def _em(v, conjunto):
    """`v in conjunto` que não levanta TypeError com valor não hashable (uma
    lista ou objeto no lugar de um texto, vindo de dados malformados): só
    textos pertencem a estes conjuntos de ids/valores."""
    return isinstance(v, str) and v in conjunto


def validate_modelo(modelo, bloco_ids):
    """Valida o próprio modelo.json: formas, tipos e ids únicos. Devolve a
    lista de erros (vazia = ok). Não levanta exceção com dados malformados:
    cada checagem tolera o que a anterior reprovou."""
    errors = []
    if not isinstance(modelo, dict):
        return ["modelo: deve ser um objeto"]

    def lista(nome):
        v = modelo.get(nome)
        if not isinstance(v, list) or not v:
            errors.append(f"modelo.{nome}: deve ser uma lista não vazia")
            return []
        out = []
        for i, x in enumerate(v):
            if isinstance(x, dict):
                out.append(x)
            else:
                errors.append(f"modelo.{nome}[{i}]: deve ser um objeto")
        return out

    def ids_unicos(nome, itens):
        vistos = set()
        for x in itens:
            i = x.get("id")
            if not _txt(i):
                errors.append(f"modelo.{nome}: item sem 'id' (texto não vazio): {x!r}")
            elif i in vistos:
                errors.append(f"modelo.{nome}: id duplicado {i!r}")
            if isinstance(i, str):
                vistos.add(i)

    grupos, sistemas, elos = lista("grupos"), lista("sistemas"), lista("elos")
    ids_unicos("grupos", grupos)
    ids_unicos("sistemas", sistemas)
    ids_unicos("elos", elos)
    elo_ids = {x.get("id") for x in elos if isinstance(x.get("id"), str)}

    for g in grupos:
        gid = g.get("id")
        if not _txt(g.get("etiqueta")):
            errors.append(f"modelo.grupos {gid!r}: falta 'etiqueta'")
        if not _em(g.get("cor"), COR_SLOTS):
            errors.append(f"modelo.grupos {gid!r}: cor {g.get('cor')!r} não é um slot de paleta ({sorted(COR_SLOTS)})")
        for campo in ("sequencial", "raia"):
            if not isinstance(g.get(campo), bool):
                errors.append(f"modelo.grupos {gid!r}: '{campo}' deve ser true ou false")
        if g.get("raia") is True:
            for campo in ("nome", "icone", "subtitulo"):
                if not _txt(g.get(campo)):
                    errors.append(f"modelo.grupos {gid!r}: grupo com raia precisa de '{campo}'")
        fe = g.get("filtroElo")
        if fe is not None and not _em(fe, elo_ids):
            errors.append(f"modelo.grupos {gid!r}: filtroElo {fe!r} não existe em modelo.elos")

    for s in sistemas:
        for campo in ("nome", "desc"):
            if not _txt(s.get(campo)):
                errors.append(f"modelo.sistemas {s.get('id')!r}: falta '{campo}'")

    tokens = {}  # texto digitável -> id do elo, pra detectar ambiguidade
    for e in elos:
        eid = e.get("id")
        if not _em(e.get("tipo"), TIPOS_ELO):
            errors.append(f"modelo.elos {eid!r}: tipo {e.get('tipo')!r} inválido ({sorted(TIPOS_ELO)})")
        if not _txt(e.get("abrev")):
            errors.append(f"modelo.elos {eid!r}: falta 'abrev'")
        if e.get("tipo") == "bloco" and not _em(eid, bloco_ids):
            errors.append(f"modelo.elos {eid!r}: elo do tipo 'bloco' sem bloco correspondente em blocos.json")
        if e.get("tipo") == "agregado" and not _txt(e.get("rotulo")):
            errors.append(f"modelo.elos {eid!r}: elo 'agregado' precisa de 'rotulo'")
        apelidos = e.get("apelidos", [])
        if not isinstance(apelidos, list) or not all(_txt(a) for a in apelidos):
            errors.append(f"modelo.elos {eid!r}: 'apelidos' deve ser uma lista de textos não vazios")
            apelidos = []
        for t in [eid, e.get("abrev")] + apelidos:
            if not _txt(t):
                continue
            t = t.strip().lower()
            if t in ATALHOS_ELOS:
                errors.append(f"modelo.elos {eid!r}: {t!r} é um atalho reservado do campo de elos")
            elif t in tokens and tokens[t] != eid:
                errors.append(f"modelo.elos: o texto {t!r} identificaria dois elos ({tokens[t]!r} e {eid!r})")
            tokens[t] = eid

    eco = modelo.get("ecossistema")
    if not isinstance(eco, dict):
        errors.append("modelo.ecossistema: deve ser um objeto")
    else:
        for campo in ("nucleo", "nota", "semItem", "dicaChip"):
            if not _txt(eco.get(campo)):
                errors.append(f"modelo.ecossistema: falta '{campo}'")

    errors += validate_vistas(modelo.get("vistas"), {g.get("id") for g in grupos if isinstance(g.get("id"), str)})
    return errors


def validate_vistas(vistas, grupo_ids):
    """Regras de modelo.vistas (menu + corpo de cada vista)."""
    if not isinstance(vistas, list) or not vistas:
        return ["modelo.vistas: deve ser uma lista não vazia"]
    errors = []
    vistos, por_tipo = set(), {}
    for i, v in enumerate(vistas):
        if not isinstance(v, dict):
            errors.append(f"modelo.vistas[{i}]: deve ser um objeto")
            continue
        vid, tipo = v.get("id"), v.get("tipo")
        nome = f"modelo.vistas {vid!r}"
        if not (isinstance(vid, str) and RE_ID_VISTA.fullmatch(vid)):
            errors.append(f"modelo.vistas[{i}]: id {vid!r} inválido (minúsculas, dígitos e hífen; começa por letra)")
        elif vid in vistos:
            errors.append(f"{nome}: id duplicado")
        if isinstance(vid, str):
            vistos.add(vid)
        if not _em(tipo, TIPOS_VISTA):
            errors.append(f"{nome}: tipo {tipo!r} inválido ({sorted(TIPOS_VISTA)})")
            continue
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        for campo in ("rotulo", "icone", "titulo"):
            if not _txt(v.get(campo)):
                errors.append(f"{nome}: falta '{campo}'")
        if not isinstance(v.get("intro"), str):
            errors.append(f"{nome}: 'intro' deve ser um texto (pode ser vazio)")
        if tipo == "diagrama":
            comp = v.get("componentes")
            if not (isinstance(comp, list) and comp and all(_em(c, COMPONENTES_DIAGRAMA) for c in comp) and len(set(comp)) == len(comp)):
                errors.append(f"{nome}: 'componentes' deve ser uma lista sem repetição de {sorted(COMPONENTES_DIAGRAMA)}")
        elif tipo == "normas":
            col = v.get("colunas")
            if not (isinstance(col, dict) and all(_txt(col.get(k)) for k in COLUNAS_NORMAS)):
                errors.append(f"{nome}: 'colunas' deve ter textos para {list(COLUNAS_NORMAS)}")
            esf = v.get("ordemEsferas")
            if not (isinstance(esf, list) and all(_txt(e) for e in esf)):
                errors.append(f"{nome}: 'ordemEsferas' deve ser uma lista de textos")
            rot = v.get("rotulos")
            if not (isinstance(rot, dict) and all(_txt(rot.get(k)) for k in ROTULOS_NORMAS)):
                errors.append(f"{nome}: 'rotulos' deve ter textos para {list(ROTULOS_NORMAS)}")
            elif "{total}" not in rot["contagem"] or "{visiveis}" not in rot["contagem"]:
                errors.append(f"{nome}: rotulos.contagem deve conter {{total}} e {{visiveis}}")
        elif tipo == "cartoes":
            if not _em(v.get("grupo"), grupo_ids):
                errors.append(f"{nome}: grupo {v.get('grupo')!r} não existe em modelo.grupos")
        elif tipo == "lista":
            if not _em(v.get("fonte"), FONTES_LISTA):
                errors.append(f"{nome}: fonte {v.get('fonte')!r} inválida ({sorted(FONTES_LISTA)})")
    for t in VISTAS_UNICAS:
        if por_tipo.get(t, 0) > 1:
            errors.append(f"modelo.vistas: no máximo uma vista do tipo {t!r} (há {por_tipo[t]})")
    return errors


def validate_meta(meta):
    """Identidade do documento (meta.json)."""
    if not isinstance(meta, dict):
        return ["meta: deve ser um objeto"]
    errors = []
    if not (isinstance(meta.get("slug"), str) and RE_SLUG.fullmatch(meta["slug"])):
        errors.append(f"meta.slug {meta.get('slug')!r} inválido (minúsculas, dígitos e hífen; vira prefixo do armazenamento e nome do arquivo exportado)")
    for campo in ("titulo", "icone", "subtitulo"):
        if not _txt(meta.get(campo)):
            errors.append(f"meta: falta '{campo}'")
    return errors


def validate(seed):
    """Referential-integrity checks across the bloco/norma relations.

    bloco.grupo, bloco.sistemas and norma.elos are relations stored as ids on
    each record; the sets of valid ids come from modelo.json. A list is just
    strings to Python, so nothing stops a typo'd id from compiling — this
    function is what catches it instead, at build time rather than as a
    silently-empty drawer the user finds by clicking around.

    siglas is a dict keyed by the exact acronym text the page matches against
    (template.html builds one case-sensitive regex straight from these keys),
    so a blank key or a missing expansion would silently show an empty or
    broken tooltip instead of failing the build.
    """
    errors = []

    ids = [b["id"] for b in seed["blocos"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"blocos com id duplicado: {sorted(dupes)}")

    errors += validate_meta(seed["meta"])
    modelo = seed["modelo"]
    errors += validate_modelo(modelo, set(ids))

    def ids_de(nome):  # só ids que são texto (um id malformado já foi reportado por validate_modelo)
        if isinstance(modelo, dict) and isinstance(modelo.get(nome), list):
            return {i for i in _ids(modelo[nome]) if isinstance(i, str)}
        return set()

    grupo_ids, sistema_ids, elo_ids = ids_de("grupos"), ids_de("sistemas"), ids_de("elos")

    for b in seed["blocos"]:
        if not _em(b["grupo"], grupo_ids):
            errors.append(f"bloco {b['id']!r}: grupo desconhecido {b['grupo']!r}")
        for sid in b.get("sistemas", []):
            if not _em(sid, sistema_ids):
                errors.append(f"bloco {b['id']!r}: sistema desconhecido {sid!r}")

    for i, n in enumerate(seed["normas"]):
        for eid in n.get("elos", []):
            if not _em(eid, elo_ids):
                errors.append(f"norma #{i} ({n.get('titulo')!r}): elo desconhecido {eid!r}")

    for sigla, info in seed.get("siglas", {}).items():
        if not sigla.strip():
            errors.append("siglas: chave vazia ou só espaços")
        if not isinstance(info, dict) or not info.get("expansao", "").strip():
            errors.append(f"sigla {sigla!r}: falta 'expansao' (não vazia)")
        url = info.get("url") if isinstance(info, dict) else None
        if url and not (url.startswith("http://") or url.startswith("https://")):
            errors.append(f"sigla {sigla!r}: url {url!r} não parece um link http(s)")

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
    # Hash do CONTEÚDO (não um timestamp): dois builds com os mesmos dados
    # geram a mesma versão, então reconstruir o site sem mudar nada em
    # meta/modelo/blocos/normas/notas/siglas não invalida à toa o que já estiver
    # salvo no navegador de quem visitou antes. template.html (init()) usa
    # isto pra saber se uma cópia salva no localStorage/db já está
    # desatualizada em relação ao conteúdo que este build publica.
    seed_version = hashlib.sha256(seed_json.encode("utf-8")).hexdigest()[:12]

    def inject(tpl, placeholder, value):
        count = tpl.count(placeholder)
        if count != 1:
            raise SystemExit(f"expected exactly 1 occurrence of {placeholder!r}, found {count}")
        return tpl.replace(placeholder, value, 1)

    template = inject(template, "__SEED_JSON__", seed_json)
    template = inject(template, "__SEED_VERSION__", seed_version)

    # Identidade no <head> (título da aba, descrição e favicon). Vem do meta.json
    # e é escapada aqui; em runtime o template também atualiza document.title
    # a partir de state.meta.titulo.
    meta = seed["meta"]
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           f"<text y='.9em' font-size='90'>{html.escape(meta['icone'], quote=False)}</text></svg>")
    favicon = "data:image/svg+xml," + urllib.parse.quote(svg, safe="/:='")
    template = inject(template, "__TITULO__", html.escape(meta["titulo"], quote=False))
    template = inject(template, "__DESCRICAO__", html.escape(meta["subtitulo"], quote=True))
    template = inject(template, "__FAVICON__", html.escape(favicon, quote=True))
    return template


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "observatorio-acai.html")
    html = build()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out_path} ({len(html)} chars)")
