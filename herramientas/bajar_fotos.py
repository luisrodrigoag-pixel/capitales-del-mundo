#!/usr/bin/env python3
"""Baja a fotos/ el retrato de cada gobernante que aparece en datos/paises.json.

Las imágenes vienen de Wikimedia Commons y se guardan reducidas (200 px de lado
mayor, JPEG) para que el repositorio no engorde. Se quedan dentro del proyecto a
propósito: así la app funciona sin red y sin depender de que un enlace siga vivo.
El crédito y la licencia de cada foto ya vienen en datos/paises.json y la ficha
los muestra.

Uso:  python3 herramientas/bajar_fotos.py
Las que ya están no se vuelven a bajar.
"""
import json, os, pathlib, subprocess, tempfile, time, urllib.parse, urllib.request

RAIZ = pathlib.Path(__file__).parent.parent
DESTINO = RAIZ / "fotos"
AGENTE = "LuluBot/1.0 (proyecto personal de estudio; contacto luisrodrigoag@gmail.com)"


def pide(url, json_=True):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r) if json_ else r.read()


def main():
    DESTINO.mkdir(exist_ok=True)
    datos = json.loads((RAIZ / "datos" / "paises.json").read_text(encoding="utf-8"))
    qids = sorted({j["foto"][:-4] for p in datos for j in p.get("jefes", {}).values() if j.get("foto")})
    print(len(qids), "retratos en la ficha")

    # de cada persona hace falta el nombre del archivo en Commons
    archivo = {}
    for i in range(0, len(qids), 50):
        d = pide("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "format": "json", "props": "claims",
            "ids": "|".join(qids[i:i + 50])}))
        for q, e in d.get("entities", {}).items():
            try:
                archivo[q] = e["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"]
            except (KeyError, IndexError):
                pass
        time.sleep(0.3)

    tmp = tempfile.mkdtemp()
    listas = saltadas = fallos = 0
    for q in qids:
        final = DESTINO / (q + ".jpg")
        if final.exists() and final.stat().st_size > 1500:
            saltadas += 1
            continue
        if q not in archivo:
            fallos += 1
            print("sin imagen en Wikidata:", q)
            continue
        url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
               + urllib.parse.quote(archivo[q].replace(" ", "_")) + "?width=220")
        crudo = os.path.join(tmp, q + ".bin")
        try:
            with open(crudo, "wb") as f:
                f.write(pide(url, json_=False))
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                            "-Z", "200", crudo, "--out", str(final)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            listas += 1
        except Exception as e:                      # red, formato raro, lo que sea
            fallos += 1
            print("falló", q, type(e).__name__, e)
        time.sleep(0.12)
    print("bajadas", listas, "| ya estaban", saltadas, "| fallos", fallos)


if __name__ == "__main__":
    main()
