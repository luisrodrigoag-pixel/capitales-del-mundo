#!/usr/bin/env python3
"""Pone en español los cargos que Wikidata solo tiene etiquetados en inglés.

Son pocos (30 de 335) y siguen un patrón fijo: «<cargo> of <país en inglés>».
Se traduce el cargo y se pega el nombre del país que ya traemos en español.
Corre sobre datos/paises.json y lo deja escrito.
"""
import json, pathlib, re

RAIZ = pathlib.Path(__file__).parent.parent
ARCHIVO = RAIZ / "datos" / "paises.json"

CARGOS = [
    (r'^monarch\b',                  'monarca'),
    (r'^President\b',                'presidente'),
    (r'^Prime Minister\b',           'primer ministro'),
    (r'^Premier\b',                  'primer ministro'),
    (r'^King\b',                     'rey'),
    (r'^Queen\b',                    'reina'),
    (r'^Chief Minister\b',           'ministro principal'),
    (r'^Governor[- ]General\b',      'gobernador general'),
    (r'^Sultan\b',                   'sultán'),
    (r'^Emir\b',                     'emir'),
    (r'^Chancellor\b',               'canciller'),
]
ENTEROS = {
    'Chairman of the Presidential Council': 'presidente del Consejo Presidencial',
    'Chairman of the Transitional Military Council': 'presidente del Consejo Militar de Transición',
}
SOBRA = re.compile(r'\s+(of|de)\s+.*$', re.I)

def traduce(cargo, pais):
    if cargo in ENTEROS:
        return ENTEROS[cargo]
    for patron, es in CARGOS:
        if re.match(patron, cargo, re.I):
            return es + ' de ' + pais
    return cargo

def ingles(cargo):
    return bool(re.search(r'\b(of|the|President|Prime|Minister|Monarch|King|Queen|Premier|Chairman|Chief|Sultan|Chancellor)\b', cargo))

def main():
    datos = json.loads(ARCHIVO.read_text(encoding='utf-8'))
    tocados = []
    for p in datos:
        for rol, j in p.get('jefes', {}).items():
            c = j.get('cargo')
            if not c or not ingles(c):
                continue
            nuevo = traduce(c, p['pais'])
            if nuevo != c:
                j['cargo'] = nuevo
                tocados.append((p['pais'], c, nuevo))
    ARCHIVO.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')
    print('cargos traducidos:', len(tocados))
    for t in tocados:
        print('  ', t[0], '|', t[1], '->', t[2])

if __name__ == '__main__':
    main()
