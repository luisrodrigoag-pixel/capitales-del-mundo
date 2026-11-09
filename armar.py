#!/usr/bin/env python3
"""Arma las dos salidas a partir de _plantilla.html y la carpeta datos/.

  pagina.html  contenido suelto, para publicar como artifact de Claude
  index.html   archivo completo y autónomo, es el que vive en GitHub Pages

Los datos van incrustados a propósito: así la app abre desde file:// y sin red.
"""
import json, pathlib

aqui = pathlib.Path(__file__).parent
paises = json.loads((aqui / "datos" / "paises.json").read_text(encoding="utf-8"))
mapa = json.loads((aqui / "datos" / "mapa.json").read_text(encoding="utf-8"))
historia = json.loads((aqui / "datos" / "historia.json").read_text(encoding="utf-8"))

bloque = (
    "const PAISES_CRUDO = " + json.dumps(paises, ensure_ascii=False, separators=(",", ":")) + ";\n"
    "const MAPA = " + json.dumps(mapa, ensure_ascii=False, separators=(",", ":")) + ";\n"
    "const HISTORIA_CRUDO = " + json.dumps(historia, ensure_ascii=False, separators=(",", ":")) + ";"
)

plantilla = (aqui / "_plantilla.html").read_text(encoding="utf-8")
assert "/*__DATOS__*/" in plantilla, "falta el marcador de datos en la plantilla"
pagina = plantilla.replace("/*__DATOS__*/", bloque)
(aqui / "pagina.html").write_text(pagina, encoding="utf-8")

# El artifact de Claude inyecta su propio esqueleto; el archivo de GitHub lo
# necesita escrito, con el mismo reset para que se vea igual en los dos lados.
envoltura = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
  :root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px);
          padding-bottom: env(safe-area-inset-bottom, 0px); }
  body { margin: 0; font: 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
__CONTENIDO__
</head>
<body>
__CUERPO__
</body>
</html>
"""
corte = pagina.index("<div class=\"marco\">")
cabeza, cuerpo = pagina[:corte], pagina[corte:]
completo = envoltura.replace("__CONTENIDO__", cabeza.strip()).replace("__CUERPO__", cuerpo.strip())
(aqui / "index.html").write_text(completo, encoding="utf-8")

fotos = len(list((aqui / "fotos").glob("*.jpg"))) if (aqui / "fotos").exists() else 0
print("países    ", len(paises))
print("contornos ", len(mapa["paises"]))
print("fotos     ", fotos)
print("historia  ", len(historia["bloques"]), "bloques,",
      sum(len(b["preguntas"]) for b in historia["bloques"]), "preguntas")
print("pagina.html", f"{len(pagina.encode()):,}", "bytes")
print("index.html ", f"{len(completo.encode()):,}", "bytes")
