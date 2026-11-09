# Capitales del Mundo

Examen de banderas, países y capitales. 195 países: los 193 miembros de la ONU
más la Ciudad del Vaticano y Palestina.

Abre `index.html` en cualquier navegador. No necesita servidor, ni conexión
(salvo para las tipografías), ni instalar nada.

## Qué trae

- **Seis modos**: bandera → país, país → capital, capital → país,
  bandera → capital, escribir la capital, y mixto.
- **Alcance** por continente o el mundo entero.
- **Examen calificado sobre 10**, con tiempo, ritmo por reactivo y la lista de
  lo que fallaste con la respuesta correcta al lado.
- **Práctica libre** sin calificación.
- **Repaso de fallos**: arma una ronda solo con los países que traes mal.
- **Estudiar**: los 195 de corrido, buscables por país, capital o región.
- **Mi progreso**: porcentaje dominado por continente y tus diez peores.
  Un país cuenta como dominado con dos aciertos seguidos.

Al escribir la capital se aceptan las variantes razonables (sin acentos, un
error de dedo, y los nombres alternos: *Kyiv* por Kiev, *La Paz* por Sucre,
*Holanda* por Países Bajos) y las capitales dobles o disputadas traen una nota
que explica el caso.

El progreso se guarda en el navegador donde juegas (`localStorage`); no sale de
ahí ni se sincroniza entre dispositivos.

## Los datos

`datos/paises.json` — 195 registros con código ISO 3166-1 alfa-2, país y
capital en español, continente, región, nombres alternos aceptados y nota.

Fuentes: los nombres en español y las capitales vienen de **Wikidata**
(consulta SPARQL de estados miembros de la ONU con su capital, etiquetas en
español); los códigos ISO, el continente y la subregión, del dataset
**mledoze/countries**. Las capitales múltiples, los nombres recién cambiados
(Esuatini, Astaná, Naipyidó) y los casos disputados se revisaron uno por uno y
quedaron anotados en el campo `nota`.

## Cómo se arma

```
python3 armar.py
```

Lee `_plantilla.html` y `datos/paises.json`, y escribe:

- `index.html` — el archivo completo y autónomo (este es el que se publica).
- `pagina.html` — el mismo contenido sin el esqueleto HTML, para publicarlo
  como artifact de Claude.

Para cambiar una capital o agregar un nombre alterno se edita
`datos/paises.json` y se corre `armar.py`. **No** se edita `index.html` a mano:
se regenera.

## Pendiente

Los siguientes bloques de estudio: la Unión Soviética, Yugoslavia, la
diferencia entre Reino Unido, Gran Bretaña e Inglaterra, y Países Bajos contra
Holanda.

## Una advertencia sobre las banderas

Las banderas son emoji. En macOS, iOS y Android se ven como banderas; en
Windows, Chrome y Edge las muestran como las dos letras del código del país
(MX, FR), porque esa fuente del sistema no trae las banderas.
