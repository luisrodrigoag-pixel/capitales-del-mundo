#!/usr/bin/env python3
"""Rehace datos/historia.json desde las fuentes.

El área de historia no son países de hoy: son Estados que desaparecieron y
nombres que se confunden. Los datos duros —fechas, capitales, repúblicas,
provincias— salen de Wikidata. Lo único escrito a mano son los textos que
explican cada bloque y la decisión editorial de qué entra, y las dos cosas
están aquí arriba, en constantes con nombre, no escondidas en el código.

Fuentes:
  Wikidata (SPARQL)   fecha de creación y de disolución de cada Estado, su
                      capital, las repúblicas y provincias que lo componían, y
                      la capital de cada país de hoy.
  es.wikipedia        nada automático: los artículos que se consultaron para
                      redactar y cotejar cada texto quedan anotados en el campo
                      "fuente" de cada bloque.

Uso:  python3 herramientas/traer_historia.py [ruta de salida]
Después hay que correr armar.py. Tarda ~1 minuto: son nueve consultas.

Guarda positiva: si una capital de hoy que este archivo da por sabida no
coincide con Wikidata, el script lo dice y termina con error en vez de escribir
un dato malo.
"""
import json, pathlib, sys, time, urllib.parse, urllib.request

RAIZ = pathlib.Path(__file__).parent.parent
SALIDA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "datos" / "historia.json"
AGENTE = "LuluBot/1.0 (proyecto personal de estudio; contacto luisrodrigoag@gmail.com)"

# ---------------------------------------------------------------- decisiones
# Los Estados que encabezan un bloque. El QID es el del Estado, no el del país
# que quedó después.
ESTADOS = {
    "urss":          "Q15180",   # Unión Soviética
    "yugoslavia":    "Q36704",   # Yugoslavia (el Estado, 1918-1992)
    "checoslovaquia": "Q33946",
    "rda":           "Q16957",   # Alemania Oriental
    "rfa":           "Q713750",  # Alemania Occidental
}

# Las 15 repúblicas de la URSS al momento de la disolución, por el código ISO
# del país que son hoy. Es una decisión editorial: la URSS tuvo otras repúblicas
# antes (Transcaucasia, Carelo-Finesa) que no llegaron a 1991.
URSS_HOY = ["RU", "UA", "BY", "MD", "EE", "LV", "LT", "GE", "AM", "AZ",
            "KZ", "UZ", "TM", "TJ", "KG"]
# Los seis Estados que salieron de Yugoslavia, más Kosovo, que es caso aparte y
# se explica en el texto del bloque.
YUGO_HOY = ["SI", "HR", "BA", "RS", "ME", "MK"]
# Cuando Wikidata ofrece varias capitales para el mismo Estado histórico, la que
# valía al final. Uzbekistán tuvo Samarcanda y Bujará antes de Taskent.
CAPITAL_HISTORICA = {"UZ": "Taskent", "KZ": "Alma Ata"}
# Wikidata no encadena por «reemplaza a» estas repúblicas con el país de hoy,
# así que su nombre se pide por etiqueta y aquí queda escrito cuál es.
NOMBRE_HISTORICO = {
    "TM": "República Socialista Soviética Turcomana",
    "BA": "República Socialista de Bosnia y Herzegovina",
    "RS": "República Socialista de Serbia",
    "ME": "República Socialista de Montenegro",
}
# De los 15 que cuelgan de los Países Bajos por «división administrativa», tres
# no son provincias sino municipios especiales en el Caribe.
NO_PROVINCIA = {"Bonaire", "Saba", "San Eustaquio"}

# Países que hoy se llaman distinto. El nombre viejo sigue apareciendo en libros
# y en conversación, y por eso vale estudiarlo. El año es el del cambio de
# nombre del país, no el de la independencia.
# (código ISO, nombre viejo, nombre de hoy, año del cambio, por qué). El nombre
# de hoy va escrito aquí porque es justo lo que se estudia, y porque el atlas
# guarda algunos con el nombre que más se usa en español: «Birmania» por
# Myanmar, por ejemplo. Türkiye y Cabo Verde no entran en la tabla: no
# cambiaron de nombre, pidieron que no se traduzca el que ya tenían, y eso se
# cuenta en las claves del bloque.
RENOMBRADOS = [
    ("MM", "Birmania",   "Myanmar",                          1989, "El gobierno militar cambió el nombre a Myanmar. Buena parte del mundo hispanohablante siguió diciendo Birmania."),
    ("IR", "Persia",     "Irán",                             1935, "Reza Sah pidió a los demás países llamarlo Irán, el nombre que el país usaba para sí mismo."),
    ("TH", "Siam",       "Tailandia",                        1939, "Pasó a Tailandia, «tierra de los libres». Volvió a ser Siam entre 1945 y 1949."),
    ("LK", "Ceilán",     "Sri Lanka",                        1972, "Al volverse república dejó el nombre colonial y tomó Sri Lanka."),
    ("BF", "Alto Volta", "Burkina Faso",                     1984, "Thomas Sankara lo renombró Burkina Faso, «patria de los hombres íntegros»."),
    ("CD", "Zaire",      "República Democrática del Congo",  1997, "Fue Congo Belga, luego Zaire con Mobutu, y hoy República Democrática del Congo."),
    ("ZW", "Rodesia",    "Zimbabue",                         1980, "Con la independencia pasó a Zimbabue, y su capital, Salisbury, a Harare."),
    ("BJ", "Dahomey",    "Benín",                            1975, "Tomó el nombre de Benín, por el antiguo reino."),
    ("SZ", "Suazilandia", "Esuatini",                        2018, "El rey lo cambió a Esuatini, que es como el país se llama en suazi."),
    ("MK", "Macedonia",  "Macedonia del Norte",              2019, "Pasó a Macedonia del Norte por el acuerdo de Prespa con Grecia."),
]

# Capitales que se mudaron de ciudad. No es un cambio de nombre: es otra ciudad.
CAPITALES_MUDADAS = [
    ("BR", "Río de Janeiro", 1960, "Brasilia se construyó de cero en el interior para poblar el centro del país."),
    ("NG", "Lagos",          1991, "Abuya se eligió por estar en el medio y ser neutral entre norte y sur."),
    ("KZ", "Almatý",         1997, "Astaná quedó más al norte y más al centro; Almatý sigue siendo la ciudad mayor."),
    ("MM", "Rangún",         2006, "Naipyidó se levantó tierra adentro y el gobierno se mudó casi sin avisar."),
    ("TZ", "Dar es Salaam",  1974, "Dodoma se designó capital, aunque muchas oficinas tardaron décadas en mudarse."),
    ("CI", "Abiyán",         1983, "Yamusukro, el pueblo natal del presidente Houphouët-Boigny, pasó a ser la capital oficial."),
    ("BZ", "Ciudad de Belice", 1970, "Tras el huracán Hattie la capital se movió tierra adentro, a Belmopán."),
    ("PK", "Karachi",        1960, "Islamabad se planeó y construyó para sustituir a Karachi."),
]

# Los textos. Esto es redacción, no dato: se cotejó con los artículos de
# es.wikipedia que quedan anotados en la clave "fuente" de cada bloque.
TEXTOS = {
    "urss": {
        "unidad": "países de hoy",
        "titulo": "La Unión Soviética",
        "subtitulo": "Un solo Estado donde hoy hay quince países",
        "entrada": "Entre 1922 y 1991 todo lo que hoy va de Estonia a Tayikistán era un mismo país, con una sola capital: Moscú. Las quince repúblicas que lo formaban ya tenían sus propias capitales, y casi todas las conservaron al independizarse. Por eso el mapa de hoy se aprende más rápido de lo que parece: las capitales no se inventaron en 1991, ya estaban ahí.",
        "claves": [
            "Quince repúblicas, no catorce ni dieciséis: ese es el número al disolverse, en diciembre de 1991.",
            "Las tres bálticas —Estonia, Letonia y Lituania— nunca reconocieron la anexión de 1940 y salieron antes que las demás.",
            "Kazajistán es el único que mudó la capital después: la soviética era Alma-Atá, y desde 1997 es Astaná.",
            "Rusia no «heredó» Moscú: Moscú ya era la capital de la república rusa dentro de la Unión.",
        ],
        "fuente": "Wikidata Q15180 · es.wikipedia «Unión Soviética», «Disolución de la Unión Soviética»",
    },
    "yugoslavia": {
        "unidad": "países de hoy",
        "titulo": "Yugoslavia",
        "subtitulo": "De un país a siete",
        "entrada": "Yugoslavia existió de 1918 a 1992 con Belgrado como capital. Se deshizo en guerra, y de su territorio salieron seis países reconocidos por la ONU, más Kosovo, cuya independencia reconoce una parte del mundo y otra no. Las repúblicas que la formaban ya tenían capital propia, y las seis la conservaron.",
        "claves": [
            "Seis repúblicas en la federación: Eslovenia, Croacia, Bosnia y Herzegovina, Serbia, Montenegro y Macedonia.",
            "Serbia y Montenegro siguieron juntos hasta 2006: Montenegro es el país más joven del grupo, sin contar Kosovo.",
            "Macedonia se llama Macedonia del Norte desde 2019, por el acuerdo con Grecia.",
            "Kosovo declaró su independencia en 2008 y no es miembro de la ONU; en el examen de los 195 no entra.",
        ],
        "fuente": "Wikidata Q36704 · es.wikipedia «Yugoslavia», «Guerras yugoslavas», «Acuerdo de Prespa»",
    },
    "reino-unido": {
        "unidad": "naciones",
        "titulo": "Reino Unido, Gran Bretaña, Inglaterra",
        "subtitulo": "Tres cosas distintas que se usan como si fueran una",
        "entrada": "No son sinónimos y el error es tan común que conviene fijarlo de una vez. Inglaterra es una de las cuatro naciones. Gran Bretaña es la isla grande, donde están tres de ellas. El Reino Unido es el país, el que tiene asiento en la ONU, y son las cuatro. Y las Islas Británicas son la geografía: ahí entra también Irlanda, que es otro país.",
        "claves": [
            "Reino Unido = Inglaterra + Escocia + Gales + Irlanda del Norte. Es el Estado, y su capital es Londres.",
            "Gran Bretaña = la isla: Inglaterra, Escocia y Gales. Irlanda del Norte no está en ella.",
            "Inglaterra = una sola de las cuatro. Decirle «Inglaterra» al Reino Unido deja fuera a Escocia, Gales e Irlanda del Norte.",
            "Islas Británicas = el archipiélago, Irlanda incluida. Es un término geográfico, no político, y en Irlanda no gusta.",
            "Cada nación tiene capital propia, y las cuatro existen a la vez: Londres, Edimburgo, Cardiff y Belfast.",
        ],
        "fuente": "Wikidata Q145 · es.wikipedia «Reino Unido», «Gran Bretaña», «Islas Británicas»",
    },
    "paises-bajos": {
        "unidad": "provincias",
        "titulo": "Países Bajos y Holanda",
        "subtitulo": "Holanda son dos provincias de doce",
        "entrada": "El país se llama Países Bajos. Holanda es la región de dos de sus doce provincias —Holanda Septentrional y Holanda Meridional—, que son las más ricas y las más visitadas, y por eso su nombre se le quedó a todo el país. Desde 2020 el gobierno pidió dejar de usarlo así en lo oficial. Y hay un segundo enredo: la capital es Ámsterdam, pero el gobierno, el parlamento y el rey despachan en La Haya.",
        "claves": [
            "Doce provincias. Holanda Septentrional (capital Haarlem) y Holanda Meridional (capital La Haya) son dos de ellas.",
            "Ámsterdam es la capital por constitución, y está en Holanda Septentrional.",
            "La Haya no es capital del país, pero es sede del gobierno, de la corte y de la Corte Internacional de Justicia.",
            "El Reino de los Países Bajos incluye además Aruba, Curazao y San Martín, que son países del reino, no provincias.",
        ],
        "fuente": "Wikidata Q55 · es.wikipedia «Países Bajos», «Holanda», «Ámsterdam», «La Haya»",
    },
    "checoslovaquia": {
        "unidad": "países de hoy",
        "titulo": "Checoslovaquia",
        "subtitulo": "El divorcio de terciopelo",
        "entrada": "Checoslovaquia nació en 1918 de la caída del Imperio austrohúngaro y se partió en dos el 1 de enero de 1993, sin un disparo: por eso se le llamó el divorcio de terciopelo. Praga, que era la capital de todo, se quedó del lado checo. Eslovaquia estrenó capital propia: Bratislava.",
        "claves": [
            "Dos países: Chequia (o República Checa) con Praga, y Eslovaquia con Bratislava.",
            "La separación fue pacífica y negociada, al contrario de la yugoslava.",
            "Chequia pidió en 2016 que se use ese nombre corto; República Checa sigue siendo correcto.",
            "Ojo con la confusión: Eslovaquia no es Eslovenia. Eslovenia era parte de Yugoslavia y su capital es Liubliana.",
        ],
        "fuente": "Wikidata Q33946 · es.wikipedia «Checoslovaquia», «Disolución de Checoslovaquia»",
    },
    "alemanias": {
        "unidad": "estados",
        "titulo": "Las dos Alemanias",
        "subtitulo": "Bonn y Berlín Este, 1949-1990",
        "entrada": "Entre 1949 y 1990 hubo dos Alemanias. La Occidental (RFA) tenía su capital en Bonn, una ciudad pequeña elegida a propósito como provisional. La Oriental (RDA) la tenía en Berlín Este. Berlín, dentro del territorio oriental, estaba partida por un muro. Con la reunificación de 1990 el país quedó uno, y Berlín volvió a ser la capital.",
        "claves": [
            "RFA, capital Bonn. RDA, capital Berlín Este. No es que Alemania tuviera dos capitales: eran dos países.",
            "Bonn se eligió provisional para no dar por perdida Berlín, y lo fue cuarenta y un años.",
            "El muro cayó el 9 de noviembre de 1989; la reunificación llegó el 3 de octubre de 1990.",
            "El gobierno tardó en mudarse: el traslado de Bonn a Berlín se decidió en 1991 y se hizo en 1999.",
        ],
        "fuente": "Wikidata Q713750 y Q16957 · es.wikipedia «República Federal de Alemania», «República Democrática Alemana», «Reunificación alemana»",
    },
    "renombrados": {
        "unidad": "países",
        "titulo": "Países que cambiaron de nombre",
        "subtitulo": "El mapa viejo sigue hablando",
        "entrada": "Un país puede cambiar de nombre sin cambiar de territorio. Pasa al independizarse, al cambiar de régimen o al pedir que se use el nombre propio en vez del que le pusieron de fuera. El nombre viejo sigue vivo en los libros, en las conversaciones y en los exámenes mal hechos, así que vale tenerlos juntos.",
        "claves": [
            "Cambiar de nombre no es cambiar de capital: casi todos estos conservaron la suya.",
            "Dos pidieron además que no se traduzca: Türkiye y Cabo Verde.",
            "Esuatini y Macedonia del Norte son los cambios más recientes, de 2018 y 2019.",
            "Myanmar y Birmania conviven: la ONU usa Myanmar, y mucha prensa en español siguió con Birmania.",
        ],
        "fuente": "Wikidata (nombre y capital de hoy, por código ISO) · es.wikipedia, el artículo de cada país",
    },
    "capitales-mudadas": {
        "unidad": "países",
        "titulo": "Capitales que se mudaron",
        "subtitulo": "Cuando el gobierno se cambia de ciudad",
        "entrada": "Varias capitales de hoy no son la de siempre: son ciudades nuevas o pequeñas a las que se llevó el gobierno, casi siempre para descentralizar, para poblar el interior o para quedar en un punto neutral. Es la trampa más frecuente en un examen de capitales, porque la ciudad famosa del país suele ser la vieja capital.",
        "claves": [
            "La ciudad más grande no es la capital en ninguno de estos casos.",
            "Brasilia, Abuya, Islamabad y Naipyidó se construyeron para ser capital.",
            "Dodoma y Yamusukro son capitales oficiales, pero buena parte del gobierno se quedó en la ciudad vieja.",
            "Astaná cambió además de nombre: fue Akmola, Astaná, Nursultán y otra vez Astaná.",
        ],
        "fuente": "Wikidata (capital de hoy, por código ISO) · es.wikipedia, el artículo de cada país y de cada capital",
    },
}

# Preguntas de concepto, las que no salen solas de una tabla.
PREGUNTAS_CONCEPTO = {
    "reino-unido": [
        {"p": "¿Qué cuatro naciones forman el Reino Unido?",
         "op": ["Inglaterra, Escocia, Gales e Irlanda del Norte",
                "Inglaterra, Escocia, Gales e Irlanda",
                "Inglaterra, Escocia, Gales y Cornualles",
                "Inglaterra, Escocia, Irlanda del Norte y la Isla de Man"],
         "nota": "Irlanda es un país aparte, con capital en Dublín. La Isla de Man y Cornualles no son naciones del Reino Unido."},
        {"p": "¿Qué naciones están en la isla de Gran Bretaña?",
         "op": ["Inglaterra, Escocia y Gales", "Las cuatro del Reino Unido",
                "Inglaterra y Escocia", "Inglaterra, Gales e Irlanda del Norte"],
         "nota": "Irlanda del Norte está en la isla de Irlanda, no en Gran Bretaña."},
        {"p": "Si digo «Islas Británicas», ¿qué incluyo que no está en el Reino Unido?",
         "op": ["Irlanda", "Islandia", "Las Islas Feroe", "Normandía"],
         "nota": "Es un término geográfico: el archipiélago entero, Irlanda incluida. En Irlanda se prefiere evitarlo."},
    ],
    "paises-bajos": [
        {"p": "¿Cuántas provincias tienen los Países Bajos?",
         "op": ["12", "2", "7", "16"],
         "nota": "Y solo dos de ellas se llaman Holanda: la Septentrional y la Meridional."},
        {"p": "¿Cuál es la capital de los Países Bajos?",
         "op": ["Ámsterdam", "La Haya", "Róterdam", "Utrecht"],
         "nota": "Ámsterdam es la capital por constitución; el gobierno y el rey despachan en La Haya."},
        {"p": "¿Qué hay en La Haya?",
         "op": ["La sede del gobierno y la Corte Internacional de Justicia",
                "La capital del país", "El palacio real y nada más",
                "La capital de Holanda Septentrional"],
         "nota": "La Haya es capital de la provincia de Holanda Meridional y sede del gobierno, pero no capital del país."},
    ],
    "urss": [
        {"p": "¿Cuántas repúblicas tenía la URSS al disolverse?",
         "op": ["15", "12", "16", "20"],
         "nota": "Quince en diciembre de 1991. Antes hubo otras que se fusionaron o desaparecieron."},
        {"p": "¿Cuál de estos países NO fue república soviética?",
         "op": ["Polonia", "Letonia", "Moldavia", "Kirguistán"],
         "nota": "Polonia fue del bloque del Este, pero país aparte: nunca fue república de la Unión."},
    ],
    "yugoslavia": [
        {"p": "¿Cuál de estos países NO salió de Yugoslavia?",
         "op": ["Albania", "Eslovenia", "Macedonia del Norte", "Montenegro"],
         "nota": "Albania fue país comunista independiente, nunca parte de Yugoslavia."},
        {"p": "¿Cuál es el país más joven de los que salieron de Yugoslavia y es miembro de la ONU?",
         "op": ["Montenegro", "Croacia", "Eslovenia", "Serbia"],
         "nota": "Montenegro se separó de Serbia en 2006. Kosovo es posterior, pero no es miembro de la ONU."},
    ],
    "checoslovaquia": [
        {"p": "¿En qué dos países se partió Checoslovaquia?",
         "op": ["Chequia y Eslovaquia", "Chequia y Eslovenia",
                "Bohemia y Moravia", "Chequia y Austria"],
         "nota": "El 1 de enero de 1993, sin violencia: el divorcio de terciopelo."},
        {"p": "¿Cuál es la capital de Eslovaquia?",
         "op": ["Bratislava", "Liubliana", "Praga", "Brno"],
         "nota": "Liubliana es la de Eslovenia, que era yugoslava. Son dos países distintos que se confunden mucho."},
    ],
    "alemanias": [
        {"p": "¿Cuál era la capital de Alemania Occidental?",
         "op": ["Bonn", "Berlín Occidental", "Fráncfort", "Hamburgo"],
         "nota": "Bonn, elegida como provisional para no renunciar a Berlín. Lo fue de 1949 a 1990."},
        {"p": "¿Qué día cayó el muro de Berlín?",
         "op": ["9 de noviembre de 1989", "3 de octubre de 1990",
                "1 de enero de 1993", "25 de diciembre de 1991"],
         "nota": "La reunificación llegó casi un año después, el 3 de octubre de 1990."},
    ],
}


# ---------------------------------------------------------------- utilidades
def sparql(consulta):
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(consulta)
    pet = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/sparql-results+json"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(pet, timeout=90) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            if intento == 3:
                raise
            print("   reintento de la consulta:", e)
            time.sleep(4 * (intento + 1))


def val(fila, clave, omision=""):
    return fila.get(clave, {}).get("value", omision)


def valores(lista):
    return " ".join('"%s"' % x for x in lista)


def fecha(texto):
    """De '1922-12-30T00:00:00Z' saca 1922."""
    return texto[:4] if texto else ""


# ---------------------------------------------------------------- consultas
def estados():
    """Cabecera de cada Estado desaparecido: capital, año de inicio y de fin."""
    qids = " ".join("wd:" + q for q in ESTADOS.values())
    filas = sparql("""SELECT ?x ?capLabel ?ini ?fin WHERE {
      VALUES ?x { %s }
      OPTIONAL { ?x wdt:P36 ?cap }
      OPTIONAL { ?x wdt:P571 ?ini }
      OPTIONAL { ?x wdt:P576 ?fin }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
    }""" % qids)
    salida = {}
    for f in filas:
        qid = val(f, "x").rsplit("/", 1)[-1]
        d = salida.setdefault(qid, {"capital": "", "inicio": "", "fin": ""})
        if val(f, "capLabel"):
            d["capital"] = val(f, "capLabel")
        ini, fin = fecha(val(f, "ini")), fecha(val(f, "fin"))
        # Wikidata a veces trae varias fechas de disolución; vale la última.
        if ini and (not d["inicio"] or ini < d["inicio"]):
            d["inicio"] = ini
        if fin and fin > d["fin"]:
            d["fin"] = fin
    return salida


def paises_de_hoy(isos):
    """Nombre y capital de hoy, del atlas del propio proyecto.

    No se vuelve a preguntar a Wikidata: datos/paises.json ya trae resueltas las
    decisiones de la casa —Esuatini y no Suazilandia, Sri Jayawardenapura Kotte y
    no Colombo— y si se consultara aparte, el área de historia contradiría al
    atlas en la misma página.
    """
    atlas = json.loads((RAIZ / "datos" / "paises.json").read_text(encoding="utf-8"))
    por_codigo = {p["codigo"]: p for p in atlas}
    salida = {}
    for iso in isos:
        p = por_codigo.get(iso)
        if p:
            salida[iso] = {"pais": p["pais"], "capitales": [p["capital"]]}
    return salida


def nombres_por_etiqueta(nombres):
    """Capital de un Estado histórico buscándolo por su etiqueta en español."""
    if not nombres:
        return {}
    filas = sparql("""SELECT ?eti ?capLabel WHERE {
      VALUES ?eti { %s }
      ?x rdfs:label ?eti FILTER(LANG(?eti) = "es")
      ?x wdt:P36 ?cap .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
    }""" % " ".join('"%s"@es' % n for n in nombres))
    salida = {}
    for f in filas:
        salida[val(f, "eti")] = val(f, "capLabel")
    return salida


def predecesores(isos, patron):
    """El Estado anterior de cada país, y su capital de entonces.

    Se filtra por patrón porque «reemplaza a» de Wikidata encadena toda la
    historia del territorio: para Estonia trae hasta la gobernación zarista.
    """
    filas = sparql("""SELECT ?iso ?antLabel ?capAntLabel WHERE {
      VALUES ?iso { %s }
      ?p wdt:P297 ?iso ; wdt:P1365 ?ant .
      OPTIONAL { ?ant wdt:P36 ?capAnt }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
    }""" % valores(isos))
    salida = {}
    for f in filas:
        nombre = val(f, "antLabel")
        if patron.lower() not in nombre.lower():
            continue
        # «Soviética» casa también con «Unión Soviética», que es el Estado
        # entero y no la república de ese país.
        if nombre in ("Unión Soviética", "República Federativa Socialista de Yugoslavia",
                      "Yugoslavia", "Serbia y Montenegro"):
            continue
        iso = val(f, "iso")
        d = salida.setdefault(iso, {"nombre": nombre, "capitales": []})
        if val(f, "capAntLabel") and val(f, "capAntLabel") not in d["capitales"]:
            d["capitales"].append(val(f, "capAntLabel"))
    return salida


def subdivisiones(qid):
    """Lo que cuelga de un país por «contiene la división administrativa»."""
    filas = sparql("""SELECT ?rLabel ?capLabel WHERE {
      wd:%s wdt:P150 ?r .
      OPTIONAL { ?r wdt:P36 ?cap }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
    } ORDER BY ?rLabel""" % qid)
    salida = []
    for f in filas:
        salida.append({"nombre": val(f, "rLabel"), "capital": val(f, "capLabel", "")})
    return salida


# ---------------------------------------------------------------- armado
def elige_capital(iso, capitales, historica=False):
    """Una sola capital. CAPITAL_HISTORICA manda cuando hay varias."""
    if historica and iso in CAPITAL_HISTORICA:
        return CAPITAL_HISTORICA[iso]
    return capitales[0] if capitales else ""


def bloque_estado_sucesores(isos, hoy, antes):
    """Los bloques de la URSS y Yugoslavia: una fila por país de hoy.

    Donde «reemplaza a» no encadena la república, el nombre sale de
    NOMBRE_HISTORICO y su capital se pide a Wikidata por esa etiqueta.
    """
    por_etiqueta = nombres_por_etiqueta(
        [NOMBRE_HISTORICO[i] for i in isos if i in NOMBRE_HISTORICO and i not in antes])
    filas = []
    for iso in isos:
        h = hoy.get(iso)
        if not h:
            print("   ⚠️ sin datos de hoy para", iso)
            continue
        a = antes.get(iso, {})
        nombre_antes = a.get("nombre") or NOMBRE_HISTORICO.get(iso, "")
        cap_antes = elige_capital(iso, a.get("capitales", []), historica=True)
        if not cap_antes and nombre_antes in por_etiqueta:
            cap_antes = por_etiqueta[nombre_antes]
        filas.append({
            "codigo": iso,
            "pais": h["pais"],
            "capital": elige_capital(iso, h["capitales"]),
            "entonces": nombre_antes,
            "capital_entonces": cap_antes,
        })
    return filas


def preguntas_de(filas, pregunta, campo_p, campo_r, nota=""):
    """Reactivos de opción múltiple sacados de las propias filas."""
    salida = []
    for f in filas:
        correcta = f[campo_r]
        if not correcta:
            continue
        otras = [g[campo_r] for g in filas if g[campo_r] and g[campo_r] != correcta]
        if len(otras) < 3:
            continue
        salida.append({
            "p": pregunta.replace("{}", f[campo_p]),
            "op": [correcta] + otras[:3],
            "nota": nota.replace("{}", f[campo_p]) if nota else "",
        })
    return salida


def main():
    print("Trayendo los datos de historia de Wikidata…")

    print(" · Estados desaparecidos")
    est = estados()

    print(" · las 15 de la URSS")
    hoy_urss = paises_de_hoy(URSS_HOY)
    antes_urss = predecesores(URSS_HOY, "Soviética")
    filas_urss = bloque_estado_sucesores(URSS_HOY, hoy_urss, antes_urss)

    print(" · las de Yugoslavia")
    hoy_yugo = paises_de_hoy(YUGO_HOY)
    antes_yugo = predecesores(YUGO_HOY, "República Socialista de")
    filas_yugo = bloque_estado_sucesores(YUGO_HOY, hoy_yugo, antes_yugo)

    print(" · las cuatro naciones del Reino Unido")
    naciones = subdivisiones("Q145")

    print(" · las provincias de los Países Bajos")
    todas = subdivisiones("Q55")
    provincias = [p for p in todas if p["nombre"] not in NO_PROVINCIA]
    caribe = [p for p in todas if p["nombre"] in NO_PROVINCIA]

    print(" · Checoslovaquia y las dos Alemanias")
    hoy_checo = paises_de_hoy(["CZ", "SK"])
    hoy_de = paises_de_hoy(["DE"])

    print(" · países renombrados y capitales mudadas")
    isos_ren = [x[0] for x in RENOMBRADOS]
    isos_mud = [x[0] for x in CAPITALES_MUDADAS]
    hoy_otros = paises_de_hoy(sorted(set(isos_ren + isos_mud)))

    # ------------------------------------------------- guarda positiva
    faltan = [i for i in isos_ren + isos_mud if i not in hoy_otros]
    if faltan:
        sys.exit("Estos códigos no están en datos/paises.json: " + ", ".join(faltan))

    bloques = []

    # --- URSS
    b = dict(TEXTOS["urss"])
    b.update({
        "id": "urss", "rotulo": "Estado desaparecido",
        "periodo": "%s–%s" % (est["Q15180"]["inicio"], est["Q15180"]["fin"]),
        "capital": est["Q15180"]["capital"],
        "columnas": ["País de hoy", "Capital", "Se llamaba", "Capital entonces"],
        "filas": filas_urss,
        "preguntas": PREGUNTAS_CONCEPTO["urss"] + preguntas_de(
            filas_urss, "¿Cuál es la capital de {}?", "pais", "capital",
            "{} fue república soviética hasta 1991."),
    })
    bloques.append(b)

    # --- Yugoslavia
    b = dict(TEXTOS["yugoslavia"])
    b.update({
        "id": "yugoslavia", "rotulo": "Estado desaparecido",
        "periodo": "%s–%s" % (est["Q36704"]["inicio"], est["Q36704"]["fin"]),
        "capital": est["Q36704"]["capital"],
        "columnas": ["País de hoy", "Capital", "Se llamaba", "Capital entonces"],
        "filas": filas_yugo,
        "preguntas": PREGUNTAS_CONCEPTO["yugoslavia"] + preguntas_de(
            filas_yugo, "¿Cuál es la capital de {}?", "pais", "capital",
            "{} fue una de las repúblicas de Yugoslavia."),
    })
    bloques.append(b)

    # --- Reino Unido
    filas_ru = [{"pais": n["nombre"], "capital": n["capital"]} for n in naciones]
    b = dict(TEXTOS["reino-unido"])
    b.update({
        "id": "reino-unido", "rotulo": "Lío de nombres",
        "periodo": "", "capital": "Londres",
        "columnas": ["Nación", "Capital"],
        "filas": filas_ru,
        "preguntas": PREGUNTAS_CONCEPTO["reino-unido"] + preguntas_de(
            filas_ru, "¿Cuál es la capital de {}?", "pais", "capital",
            "{} es una de las cuatro naciones del Reino Unido."),
    })
    bloques.append(b)

    # --- Países Bajos
    filas_nl = [{"pais": p["nombre"], "capital": p["capital"]} for p in provincias]
    b = dict(TEXTOS["paises-bajos"])
    b.update({
        "id": "paises-bajos", "rotulo": "Lío de nombres",
        "periodo": "", "capital": "Ámsterdam",
        "columnas": ["Provincia", "Capital"],
        "filas": filas_nl,
        "aparte": {"titulo": "En el Caribe, y no son provincias",
                   "filas": [{"pais": p["nombre"], "capital": p["capital"]} for p in caribe]},
        "preguntas": PREGUNTAS_CONCEPTO["paises-bajos"] + preguntas_de(
            filas_nl, "¿Cuál es la capital de la provincia de {}?", "pais", "capital",
            "{} es una de las doce provincias de los Países Bajos."),
    })
    bloques.append(b)

    # --- Checoslovaquia
    filas_cs = [{
        "pais": hoy_checo[i]["pais"],
        "capital": hoy_checo[i]["capitales"][0] if hoy_checo[i]["capitales"] else "",
    } for i in ("CZ", "SK") if i in hoy_checo]
    b = dict(TEXTOS["checoslovaquia"])
    b.update({
        "id": "checoslovaquia", "rotulo": "Estado desaparecido",
        "periodo": "%s–%s" % (est["Q33946"]["inicio"], est["Q33946"]["fin"]),
        "capital": est["Q33946"]["capital"],
        "columnas": ["País de hoy", "Capital"],
        "filas": filas_cs,
        "preguntas": PREGUNTAS_CONCEPTO["checoslovaquia"],
    })
    bloques.append(b)

    # --- las dos Alemanias
    cap_de = hoy_de["DE"]["capitales"][0] if hoy_de.get("DE", {}).get("capitales") else "Berlín"
    filas_de = [
        {"pais": "Alemania Occidental (RFA)", "capital": est["Q713750"]["capital"],
         "periodo": "%s–%s" % (est["Q713750"]["inicio"], est["Q713750"]["fin"])},
        {"pais": "Alemania Oriental (RDA)", "capital": est["Q16957"]["capital"],
         "periodo": "%s–%s" % (est["Q16957"]["inicio"], est["Q16957"]["fin"])},
        {"pais": "Alemania, desde 1990", "capital": cap_de, "periodo": "1990–"},
    ]
    b = dict(TEXTOS["alemanias"])
    b.update({
        "id": "alemanias", "rotulo": "Estado desaparecido",
        "periodo": "1949–1990", "capital": "",
        "columnas": ["Estado", "Capital", "Periodo"],
        "filas": filas_de,
        "preguntas": PREGUNTAS_CONCEPTO["alemanias"],
    })
    bloques.append(b)

    # --- renombrados
    filas_ren = []
    for iso, viejo, hoy_nombre, anio, por_que in RENOMBRADOS:
        h = hoy_otros[iso]
        filas_ren.append({
            "codigo": iso, "antes": viejo, "pais": hoy_nombre,
            "capital": h["capitales"][0] if h["capitales"] else "",
            "anio": str(anio), "nota": por_que,
        })
    b = dict(TEXTOS["renombrados"])
    b.update({
        "id": "renombrados", "rotulo": "Lío de nombres", "periodo": "", "capital": "",
        "columnas": ["Se llamaba", "Hoy", "Capital", "Desde"],
        "filas": filas_ren,
        "preguntas": preguntas_de(
            filas_ren, "¿Cómo se llama hoy el país que era {}?", "antes", "pais",
            "Cambió de nombre, no de territorio."),
    })
    bloques.append(b)

    # --- capitales mudadas
    filas_mud = []
    for iso, vieja, anio, por_que in CAPITALES_MUDADAS:
        h = hoy_otros[iso]
        nueva = h["capitales"][0] if h["capitales"] else ""
        filas_mud.append({
            "codigo": iso, "pais": h["pais"], "antes": vieja,
            "capital": nueva, "anio": str(anio), "nota": por_que,
        })
    b = dict(TEXTOS["capitales-mudadas"])
    b.update({
        "id": "capitales-mudadas", "rotulo": "Trampa de examen", "periodo": "", "capital": "",
        "columnas": ["País", "Era", "Es", "Desde"],
        "filas": filas_mud,
        "preguntas": preguntas_de(
            filas_mud, "¿Cuál es hoy la capital de {}?", "pais", "capital",
            "La capital de {} se mudó: la ciudad más conocida ya no lo es."),
    })
    bloques.append(b)

    # ------------------------------------------------- guardas de salida
    for b in bloques:
        if not b.get("filas"):
            sys.exit("El bloque %s salió sin filas." % b["id"])
        if not b.get("preguntas"):
            sys.exit("El bloque %s salió sin preguntas." % b["id"])
        sin_capital = [f for f in b["filas"] if not f.get("capital")]
        if sin_capital:
            print("   ⚠️ %s: %d fila(s) sin capital" % (b["id"], len(sin_capital)))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({
        "generado": time.strftime("%Y-%m-%d"),
        "bloques": bloques,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print("bloques  ", len(bloques))
    for b in bloques:
        print("  %-18s %2d filas  %2d preguntas" % (b["id"], len(b["filas"]), len(b["preguntas"])))
    print("escrito  ", SALIDA)


if __name__ == "__main__":
    main()
