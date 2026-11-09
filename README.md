# Capitales del Mundo

Examen y atlas de los 195 países del mundo: los 193 miembros de la ONU más la
Ciudad del Vaticano y Palestina.

Para jugar: **https://luisrodrigoag-pixel.github.io/capitales-del-mundo/**

También abre `index.html` directo en el navegador. No necesita servidor, ni
instalar nada, ni conexión: los datos, el mapa y las fotos van dentro del
repositorio. Lo único que se baja de fuera son las tipografías.

## Qué trae

**Examen.** Seis modos — bandera → país, país → capital, capital → país,
bandera → capital, escribir la capital, y mixto. Se puede acotar a un
continente y elegir de 10 a 195 reactivos. Califica sobre 10, mide el tiempo y
al final lista lo que fallaste con la respuesta correcta al lado. También hay
práctica libre, sin calificación, y un repaso que arma una ronda solo con los
países que traes mal.

**Explorar.** Los 195 divididos por continente, cada uno con su mapa. Al entrar
a un país se abre su ficha:

- bandera y capital;
- mapa de su región con el país marcado y un punto en la capital;
- régimen de gobierno, población con el año del dato, superficie y moneda;
- quién gobierna — jefatura del Estado y jefatura del gobierno, con foto, cargo,
  desde cuándo y dos renglones de biografía.

El buscador encuentra por país, capital, moneda, forma de gobierno o nombre del
gobernante. En la ficha, las flechas ‹ › del teclado pasan al país siguiente.

**Historia.** Ocho láminas de estudio con lo que el mapa de hoy no explica:
Estados que desaparecieron y nombres que se usan mal.

- la Unión Soviética y los quince países que salieron de ella, con la capital de
  cada república soviética al lado de la de hoy;
- Yugoslavia y los seis países de la ONU que quedaron, más Kosovo, que se
  explica aparte;
- Reino Unido, Gran Bretaña, Inglaterra e Islas Británicas: qué es cada cosa y
  las capitales de las cuatro naciones;
- Países Bajos y Holanda: las doce provincias, las dos que se llaman Holanda, y
  por qué la capital es Ámsterdam pero el gobierno está en La Haya;
- Checoslovaquia, las dos Alemanias, los países que cambiaron de nombre
  (Birmania, Persia, Siam, Zaire, Rodesia…) y las capitales que se mudaron de
  ciudad (Brasilia, Abuya, Astaná, Naipyidó…).

Cada lámina trae su tabla, cuatro o cinco claves de lo que se confunde, y un
repaso de opción múltiple con las preguntas de ese bloque: las de concepto están
escritas, y las de capitales se arman solas con los datos de la tabla.

**Mi progreso.** Porcentaje dominado por continente y tus diez peores. Un país
cuenta como dominado con dos aciertos seguidos. Se guarda en el navegador donde
juegas (`localStorage`): no sale de ahí ni se sincroniza entre dispositivos.

Al escribir la capital se aceptan las variantes razonables —sin acentos, un
error de dedo, y los nombres alternos: *Kyiv* por Kiev, *La Paz* por Sucre,
*Holanda* por Países Bajos—. Las capitales dobles o disputadas traen una nota
que explica el caso.

## Los datos

Ver [FUENTES.md](FUENTES.md) para el detalle de de dónde sale cada campo.

- `datos/paises.json` — 195 registros: código ISO 3166-1 alfa-2, país y capital
  en español, continente, región, población, moneda, forma de gobierno,
  coordenadas de la capital, gobernantes y notas.
- `datos/mapa.json` — los contornos de 174 países, simplificados, en grados.
- `datos/historia.json` — los ocho bloques del área de historia: texto, tabla y
  preguntas de cada uno.
- `fotos/` — un retrato por gobernante, reducido a 200 px. El autor y la
  licencia de cada uno están en `datos/paises.json` y la ficha los muestra.

## Cómo se arma

```
python3 armar.py
```

Lee `_plantilla.html` y la carpeta `datos/`, e incrusta los datos para escribir:

- `index.html` — el archivo completo y autónomo, el que se publica;
- `pagina.html` — lo mismo sin el esqueleto HTML, para publicarlo como artifact
  de Claude.

**No se edita `index.html` a mano: se regenera.** Para cambiar un dato suelto se
edita `datos/paises.json` y se corre `armar.py`.

Para rehacer los datos desde las fuentes, en este orden:

```
python3 herramientas/traer_datos.py        # Wikidata + es.wikipedia + mledoze
python3 herramientas/traducir_cargos.py    # los cargos que solo venían en inglés
python3 herramientas/bajar_fotos.py        # los retratos que falten
python3 herramientas/traer_historia.py     # el área de historia, desde Wikidata
python3 armar.py
```

Los gobernantes y la población cambian; eso se vuelve a correr cada tanto.
Última corrida: **9 de noviembre de 2026**.

## Dos advertencias

**Las banderas son emoji.** En macOS, iOS y Android se ven como banderas; en
Windows, Chrome y Edge las muestran como las dos letras del código del país
(MX, FR), porque esa fuente del sistema no las trae.

**Lo que gobierna cambia solo.** Los nombres de los gobernantes salieron de
Wikidata el 9 de noviembre de 2026. Si hubo elección desde entonces, hay que
volver a correr `traer_datos.py`.
