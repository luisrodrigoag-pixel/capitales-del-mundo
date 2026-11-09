#!/usr/bin/env python3
"""Rehace datos/paises.json desde cero, desde las fuentes.

Fuentes, y por qué cada una:
  Wikidata (SPARQL)   nombre del país y de la capital en español, coordenadas de
                      la capital, población con su año, moneda, y quién gobierna.
  es.wikipedia        la «forma de gobierno» de la ficha del artículo, que está
                      mucho mejor redactada que la propiedad P122 de Wikidata, y
                      la primera frase del artículo de cada gobernante.
  mledoze/countries   código ISO 3166-1, continente, subregión, superficie y el
                      símbolo de la moneda.

Uso:  python3 herramientas/traer_datos.py [ruta de salida]
Después hay que correr herramientas/traducir_cargos.py, bajar_fotos.py y armar.py.
Tarda varios minutos: son unas cuantas consultas y ~500 artículos.
"""
import json, pathlib, re, sys, time, urllib.parse, urllib.request

RAIZ = pathlib.Path(__file__).parent.parent
SALIDA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "datos" / "paises.json"
AGENTE = "LuluBot/1.0 (proyecto personal de estudio; contacto luisrodrigoag@gmail.com)"

# Dos no son miembros de la ONU pero cuentan como países en cualquier examen.
EXTRA = {"VA", "PS"}
# Lo que ninguna base trae bien y se revisó a mano.
NOMBRE_MEJOR = {"NL": "Países Bajos", "CN": "China", "SZ": "Esuatini", "ML": "Malí",
                "CG": "República del Congo", "FM": "Micronesia", "DK": "Dinamarca",
                "VA": "Ciudad del Vaticano", "PS": "Palestina"}
CAPITAL_PRINCIPAL = {"BO": "Sucre", "LK": "Sri Jayawardenapura Kotte", "SZ": "Mbabane",
                     "ZA": "Pretoria", "YE": "Saná", "GQ": "Malabo",
                     "AG": "Saint John's", "GD": "Saint George's",
                     "DK": "Copenhague", "VA": "Ciudad del Vaticano", "PS": "Ramala"}
ALIAS_CAPITAL = {
    "BO": ["La Paz"], "LK": ["Colombo", "Kotte"], "SZ": ["Lobamba"],
    "ZA": ["Ciudad del Cabo", "Bloemfontein", "Cape Town"], "YE": ["Adén"],
    "GQ": ["Ciudad de la Paz", "Djibloho", "Oyala"], "CL": ["Santiago"], "UA": ["Kyiv"],
    "KZ": ["Nursultán", "Nur-Sultán", "Akmola"], "MM": ["Naypyidaw", "Nay Pyi Taw"],
    "US": ["Washington"], "SM": ["Ciudad de San Marino"], "IN": ["Delhi"], "CN": ["Beijing"],
    "DJ": ["Yibuti", "Djibouti"], "AG": ["Saint John"], "GD": ["Saint George"],
    "MD": ["Chisinau", "Kishinev"], "VN": ["Hanoi"], "TT": ["Port of Spain"],
    "MV": ["Male"], "TO": ["Nuku'alofa"], "KI": ["Tarawa"], "CI": ["Abiyán"],
    "BJ": ["Cotonú"], "TZ": ["Dar es Salaam"], "IL": ["Tel Aviv"], "NL": ["La Haya"],
}
ALIAS_PAIS = {
    "SZ": ["Suazilandia"], "CZ": ["Chequia"], "MM": ["Myanmar"], "NL": ["Holanda"],
    "CN": ["República Popular China"], "RO": ["Rumanía"], "GB": ["Gran Bretaña", "Inglaterra"],
    "US": ["EUA", "EEUU", "Estados Unidos de América"], "AE": ["EAU"], "TR": ["Türkiye"],
    "TL": ["Timor-Leste"], "CD": ["Congo (RDC)", "Zaire"], "MK": ["Macedonia"],
    "VA": ["Vaticano", "Santa Sede"], "FM": ["Estados Federados de Micronesia"],
    "DO": ["Dominicana"],
}
NOTAS = {
    "BO": "Sucre es la capital constitucional; La Paz es la sede del gobierno.",
    "ZA": "Tres capitales: Pretoria (ejecutiva), Ciudad del Cabo (legislativa) y Bloemfontein (judicial).",
    "LK": "Sri Jayawardenapura Kotte es la capital oficial; Colombo es la capital comercial.",
    "SZ": "Mbabane es la capital administrativa; Lobamba es la real y legislativa. El país se llama Esuatini desde 2018.",
    "YE": "Saná es la capital oficial; Adén es sede del gobierno reconocido desde 2015.",
    "GQ": "Malabo sigue siendo la capital de hecho; desde 2017 el gobierno designó Ciudad de la Paz (Djibloho) como nueva capital.",
    "NL": "Ámsterdam es la capital; el gobierno y la Corte están en La Haya.",
    "CI": "Yamusukro es la capital oficial; Abiyán es la sede del gobierno.",
    "BJ": "Porto Novo es la capital oficial; Cotonú es la sede del gobierno.",
    "TZ": "Dodoma es la capital desde 1996; Dar es Salaam fue la anterior.",
    "IL": "Jerusalén es la capital declarada; su estatuto está disputado y la mayoría de embajadas están en Tel Aviv.",
    "PS": "Ramala es la sede administrativa; Palestina reclama Jerusalén Este como capital.",
    "KZ": "Astaná; se llamó Nursultán entre 2019 y 2022.",
    "UA": "Kiev (Kyiv en transliteración del ucraniano).",
    "MM": "Naipyidó es la capital desde 2005; Rangún fue la anterior.",
    "CZ": "República Checa o Chequia; ambas son oficiales en español.",
}
NOTAS_JEFES = {
    "BA": "La jefatura del Estado es una presidencia colegiada de tres miembros —bosniaco, croata y serbio— que se turnan la presidencia cada ocho meses. Aquí aparece uno de los tres.",
    "SM": "San Marino tiene dos Capitanes Regentes que gobiernan juntos seis meses y se renuevan cada 1 de abril y cada 1 de octubre, así que este dato envejece rápido.",
    "CH": "Suiza no tiene jefe de Estado: gobierna en cuerpo el Consejo Federal, de siete miembros, y la presidencia rota cada año.",
    "AD": "Andorra tiene dos coprincipes, el obispo de Urgel y el presidente de Francia. Aquí aparece el episcopal.",
}
CONTINENTE = {"Africa": "África", "Americas": "América", "Asia": "Asia",
              "Europe": "Europa", "Oceania": "Oceanía"}
REGION = {
    "Northern Africa": "Norte de África", "Western Africa": "África occidental",
    "Eastern Africa": "África oriental", "Middle Africa": "África central",
    "Southern Africa": "África austral", "North America": "Norteamérica",
    "Central America": "Centroamérica", "Caribbean": "Caribe", "South America": "Sudamérica",
    "Western Asia": "Asia occidental", "Central Asia": "Asia central",
    "Southern Asia": "Asia del sur", "Eastern Asia": "Asia oriental",
    "South-Eastern Asia": "Sudeste asiático", "Northern Europe": "Europa del norte",
    "Western Europe": "Europa occidental", "Eastern Europe": "Europa del este",
    "Southern Europe": "Europa del sur", "Central Europe": "Europa central",
    "Southeast Europe": "Europa del sureste", "Northern America": "Norteamérica",
    "Australia and New Zealand": "Australia y Nueva Zelanda", "Melanesia": "Melanesia",
    "Micronesia": "Micronesia", "Polynesia": "Polinesia",
}
# El código CY cuelga del artículo de la isla, no del país.
ARTICULO_MEJOR = {"CY": "Chipre"}


def baja(url, json_=True):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r) if json_ else r.read()


def sparql(consulta):
    u = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": consulta, "format": "json"})
    return baja(u)["results"]["bindings"]


def val(fila, clave):
    return fila[clave]["value"] if clave in fila else None


def api(sitio, parametros):
    return baja("https://" + sitio + "/w/api.php?" + urllib.parse.urlencode(parametros))


def por_lotes(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def bandera(cc):
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in cc)


# ---------- limpieza de wikitexto ----------
CITAS = r"(?:sfn|harvnp|harvsp|harv|cita|cite|efn|nota|refn|listaref|r)\b"


def limpia_wiki(s):
    if not s:
        return None
    s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", s, flags=re.S)
    previo = None
    while previo != s:
        previo = s
        s = re.sub(r"\{\{\s*" + CITAS + r"[^{}]*\}\}", "", s, flags=re.I)
        s = re.sub(r"\{\{\s*[^{}|]*\|([^{}]*)\}\}", r"\1", s)
        s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[[^\]\|]+\|([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s).strip(" ,;·|") or None


def sin_parentesis(t):
    previo = None
    while previo != t:
        previo = t
        t = re.sub(r"\([^()]*\)", "", t)
    t = re.sub(r"\([^)]*$", "", t)
    return re.sub(r"^[^(]*\)", "", t)


def resume(texto, minimo=130, tope=270):
    t = (texto or "").replace("​", "").replace("­", "")
    t = sin_parentesis(t)
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"\s*,\s*,", ",", t).strip().lstrip(",;: ")
    salida = ""
    for f in re.split(r"(?<=\.)\s+", t):
        f = f.strip()
        if not f:
            continue
        if not salida:
            salida = f
        elif len(salida) < minimo and len(salida) + 1 + len(f) <= tope:
            salida += " " + f
        else:
            break
    if len(salida) > tope + 70:
        salida = salida[:tope].rsplit(" ", 1)[0].rstrip(",;") + "…"
    return salida.strip()


def main():
    print("1/7  países, códigos y continentes (mledoze/countries)")
    mled = {c["cca2"]: c for c in baja(
        "https://raw.githubusercontent.com/mledoze/countries/master/countries.json")}
    codigos = sorted({c for c, v in mled.items() if v.get("unMember")} | EXTRA)
    print("     ", len(codigos), "países")

    print("2/7  nombres y capitales en español (Wikidata)")
    nombre, capitales = {}, {}
    for f in sparql('SELECT ?code ?paisLabel ?capLabel WHERE { VALUES ?org { wd:Q1065 wd:Q47423 } '
                    '?pais wdt:P463 ?org . ?pais wdt:P297 ?code . ?pais wdt:P36 ?cap . '
                    'SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". } }'):
        c = val(f, "code")
        if c not in codigos:
            continue
        nombre.setdefault(c, val(f, "paisLabel"))
        capitales.setdefault(c, []).append(val(f, "capLabel"))

    print("3/7  artículos, coordenadas de la capital, población, moneda")
    articulo, coord = {}, {}
    for f in sparql('SELECT ?code ?art ?coord WHERE { ?pais wdt:P297 ?code . '
                    'OPTIONAL { ?art schema:about ?pais ; schema:isPartOf <https://es.wikipedia.org/> } '
                    'OPTIONAL { ?pais wdt:P36 ?cap . ?cap wdt:P625 ?coord } }'):
        c = val(f, "code")
        if c not in codigos:
            continue
        if val(f, "art") and c not in articulo:
            articulo[c] = urllib.parse.unquote(val(f, "art").rsplit("/", 1)[-1]).replace("_", " ")
        m = re.match(r"Point\(([-0-9.]+) ([-0-9.]+)\)", val(f, "coord") or "")
        if m and c not in coord:
            coord[c] = [round(float(m.group(2)), 3), round(float(m.group(1)), 3)]
    articulo.update(ARTICULO_MEJOR)

    poblacion = {}
    for f in sparql('SELECT ?code ?pob ?fecha WHERE { ?pais wdt:P297 ?code . ?pais p:P1082 ?ps . '
                    '?ps ps:P1082 ?pob . OPTIONAL { ?ps pq:P585 ?fecha } '
                    'FILTER NOT EXISTS { ?ps wikibase:rank wikibase:DeprecatedRank } }'):
        c = val(f, "code")
        if c not in codigos:
            continue
        fch = val(f, "fecha") or ""
        try:
            n = int(float(val(f, "pob")))
        except (TypeError, ValueError):
            continue
        if c not in poblacion or fch > poblacion[c][1]:
            poblacion[c] = (n, fch)

    moneda = {}
    for f in sparql('SELECT ?code ?monedaLabel ?iso WHERE { ?pais wdt:P297 ?code . ?pais p:P38 ?pm . '
                    '?pm ps:P38 ?moneda . FILTER NOT EXISTS { ?pm pq:P582 ?fin } '
                    'OPTIONAL { ?moneda wdt:P498 ?iso } '
                    'SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". } }'):
        c = val(f, "code")
        if c not in codigos:
            continue
        nom, iso = val(f, "monedaLabel"), val(f, "iso")
        lista = moneda.setdefault(c, [])
        if nom and not any(x["nombre"] == nom for x in lista):
            reg = {"nombre": nom, "iso": iso}
            simbolo = ((mled[c].get("currencies") or {}).get(iso) or {}).get("symbol")
            if simbolo:
                reg["simbolo"] = simbolo
            lista.append(reg)

    print("4/7  quién gobierna (Wikidata)")
    jefes_crudo = {}
    for f in sparql('SELECT ?code ?rol ?quien ?desde WHERE { ?pais wdt:P297 ?code . '
                    '{ ?pais p:P35 ?pp . ?pp ps:P35 ?quien . BIND("estado" AS ?rol) } UNION '
                    '{ ?pais p:P6 ?pp . ?pp ps:P6 ?quien . BIND("gobierno" AS ?rol) } '
                    'FILTER NOT EXISTS { ?pp pq:P582 ?fin } OPTIONAL { ?pp pq:P580 ?desde } }'):
        c = val(f, "code")
        if c not in codigos:
            continue
        jefes_crudo.setdefault(c, {}).setdefault(val(f, "rol"), []).append(
            {"qid": val(f, "quien").rsplit("/", 1)[-1], "desde": val(f, "desde")})
    jefes = {}
    for c, roles in jefes_crudo.items():
        for rol, gente in roles.items():
            gente.sort(key=lambda g: g["desde"] or "", reverse=True)
            jefes.setdefault(c, {})[rol] = gente[0]

    cargo = {}
    for consulta, rol in (
        ('SELECT ?code ?cargoLabel WHERE { ?pais wdt:P297 ?code . ?pais wdt:P1906 ?cargo . '
         'SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". } }', "estado"),
        ('SELECT ?code ?cargoLabel WHERE { ?pais wdt:P297 ?code . ?pais wdt:P1313 ?cargo . '
         'SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". } }', "gobierno"),
    ):
        for f in sparql(consulta):
            c = val(f, "code")
            if c in codigos and val(f, "cargoLabel"):
                cargo.setdefault(c, {}).setdefault(rol, val(f, "cargoLabel"))

    print("5/7  nombre, foto y artículo de cada gobernante")
    qids = sorted({g["qid"] for c in jefes for g in jefes[c].values()})
    persona = {}
    for lote in por_lotes(qids, 50):
        d = api("www.wikidata.org", {
            "action": "wbgetentities", "format": "json", "languages": "es|en",
            "props": "labels|descriptions|sitelinks|claims", "sitefilter": "eswiki",
            "ids": "|".join(lote)})
        for q, e in d.get("entities", {}).items():
            img = None
            if e.get("claims", {}).get("P18"):
                try:
                    img = e["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"]
                except (KeyError, IndexError):
                    pass
            persona[q] = {
                "nombre": (e.get("labels", {}).get("es") or e.get("labels", {}).get("en") or {}).get("value"),
                "descripcion": (e.get("descripciones", {}) or e.get("descriptions", {}) or {}).get("es", {}).get("value"),
                "eswiki": e.get("sitelinks", {}).get("eswiki", {}).get("title"),
                "archivo": img,
            }
        time.sleep(0.3)

    print("6/7  forma de gobierno y biografías (es.wikipedia)")
    secciones = {}
    titulos = sorted(set(articulo.values()))
    for lote in por_lotes(titulos, 15):
        d = api("es.wikipedia.org", {
            "action": "query", "format": "json", "formatversion": "2", "prop": "revisions",
            "rvslots": "main", "rvprop": "content", "rvsection": "0", "redirects": "1",
            "titles": "|".join(lote)})
        mapa_t = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for n in d.get("query", {}).get("redirects", []):
            mapa_t[n["to"]] = mapa_t.get(n["from"], n["from"])
        for p in d.get("query", {}).get("pages", []):
            try:
                secciones[mapa_t.get(p["title"], p["title"])] = p["revisions"][0]["slots"]["main"]["content"]
            except (KeyError, IndexError):
                pass
        time.sleep(0.25)

    regimen = {}
    for c, t in articulo.items():
        txt = secciones.get(t, "")
        v = None
        for campo in ("forma_de_gobierno", "forma de gobierno", "gobierno"):
            m = re.search(r"\|\s*" + campo + r"\s*=([^\n]*(?:\n(?!\s*[|}])[^\n]*)*)", txt, re.I)
            if m and m.group(1).strip():
                v = limpia_wiki(m.group(1))
                break
        if not v:
            continue
        if len(v) > 92:
            v = v[:90].rsplit(" ", 1)[0] + "…"
        regimen[c] = v[0].upper() + v[1:]

    bio_titulos = sorted({p["eswiki"] for p in persona.values() if p["eswiki"]})
    extractos = {}
    for lote in por_lotes(bio_titulos, 20):
        d = api("es.wikipedia.org", {
            "action": "query", "format": "json", "formatversion": "2", "prop": "extracts",
            "exintro": "1", "explaintext": "1", "redirects": "1", "titles": "|".join(lote)})
        mapa_t = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for n in d.get("query", {}).get("redirects", []):
            mapa_t[n["to"]] = mapa_t.get(n["from"], n["from"])
        for p in d.get("query", {}).get("pages", []):
            if "extract" in p:
                extractos[mapa_t.get(p["title"], p["title"])] = p["extract"]
        time.sleep(0.25)

    print("7/7  créditos de las fotos (Commons)")
    archivos = sorted({p["archivo"] for p in persona.values() if p["archivo"]})
    credito = {}
    for lote in por_lotes(archivos, 40):
        d = api("commons.wikimedia.org", {
            "action": "query", "format": "json", "formatversion": "2", "prop": "imageinfo",
            "iiprop": "extmetadata|url", "iiextmetadatafilter": "Artist|LicenseShortName",
            "iiurlwidth": "220", "titles": "|".join("File:" + a for a in lote)})
        for p in d.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            def texto(x):
                return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x or "")).strip(" ,;")
            credito[p["title"][5:]] = {
                "autor": texto(em.get("Artist", {}).get("value"))[:90],
                "licencia": texto(em.get("LicenseShortName", {}).get("value"))[:40],
                "miniatura": ii.get("thumburl"),
            }
        time.sleep(0.3)

    print("     armando el archivo")
    salida = []
    for c in codigos:
        m = mled[c]
        caps = capitales.get(c, [])
        principal = CAPITAL_PRINCIPAL.get(c) or (caps[0] if caps else None)
        pais = NOMBRE_MEJOR.get(c) or nombre.get(c) or m["name"]["common"]
        if not principal:
            raise SystemExit("sin capital para " + c)
        reg = {
            "codigo": c, "pais": pais, "capital": principal, "bandera": bandera(c),
            "continente": CONTINENTE[m["region"]],
            "region": REGION.get(m.get("subregion") or "", CONTINENTE[m["region"]]),
        }
        ap = [a for a in ALIAS_PAIS.get(c, []) if a != pais]
        ac = [a for a in ALIAS_CAPITAL.get(c, []) if a != principal]
        if ap:
            reg["alias_pais"] = ap
        if ac:
            reg["alias_capital"] = ac
        if c in NOTAS:
            reg["nota"] = NOTAS[c]
        n, fch = poblacion.get(c, (None, ""))
        reg["poblacion"] = {"valor": n, "anio": int(fch[:4]) if fch else None} if n else None
        reg["moneda"] = moneda.get(c, [])
        reg["regimen"] = regimen.get(c)
        reg["area"] = m.get("area")
        reg["latlng"] = [round(x, 2) for x in (m.get("latlng") or [])] or None
        reg["capital_latlng"] = coord.get(c)
        reg["wiki"] = "https://es.wikipedia.org/wiki/" + articulo[c].replace(" ", "_") if c in articulo else None
        quien = {}
        for rol in ("estado", "gobierno"):
            g = (jefes.get(c) or {}).get(rol)
            if not g:
                continue
            d = persona.get(g["qid"], {})
            arch = d.get("archivo")
            cr = credito.get(arch) if arch else None
            bio = ""
            if d.get("eswiki") and d["eswiki"] in extractos:
                bio = resume(extractos[d["eswiki"]])
            elif d.get("descripcion"):
                bio = d["descripcion"][0].upper() + d["descripcion"][1:] + "."
            ficha = {
                "nombre": d.get("nombre") or d.get("eswiki") or g["qid"],
                "cargo": (cargo.get(c) or {}).get(rol),
                "desde": (g.get("desde") or "")[:10] or None,
                "bio": bio,
                "foto": g["qid"] + ".jpg" if arch else None,
                "wiki": "https://es.wikipedia.org/wiki/" + d["eswiki"].replace(" ", "_") if d.get("eswiki") else None,
            }
            if cr:
                ficha["credito"] = " / ".join(x for x in [cr.get("autor"), cr.get("licencia")] if x)
            quien[rol] = ficha
        if "estado" in quien and "gobierno" in quien and quien["estado"]["nombre"] == quien["gobierno"]["nombre"]:
            quien.pop("gobierno")
            quien["estado"]["unico"] = True
        reg["jefes"] = quien
        if c in NOTAS_JEFES:
            reg["nota_jefes"] = NOTAS_JEFES[c]
        salida.append(reg)

    salida.sort(key=lambda r: r["pais"])
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito", SALIDA, "con", len(salida), "países")


if __name__ == "__main__":
    main()
