# De dónde sale cada dato

Nada de este archivo se escribió de memoria. Cada campo tiene una fuente
consultable y el script que lo trae está en `herramientas/`.

| Campo | Fuente | Cómo |
|---|---|---|
| Qué cuenta como país | Lista de miembros de la ONU | 193 miembros del dataset mledoze/countries, más Vaticano y Palestina, que son Estados observadores |
| Nombre del país en español | Wikidata | etiqueta en español del elemento con código ISO (P297) |
| Capital | Wikidata | propiedad «capital» (P36), etiqueta en español |
| Coordenadas de la capital | Wikidata | P36 → coordenadas (P625) |
| Bandera | — | se compone con los dos caracteres de indicador regional del código ISO; no es un archivo de imagen |
| Continente, región, superficie | mledoze/countries | `region`, `subregion` y `area`, traducidos |
| Población | Wikidata | P1082, tomando la medición con fecha (P585) más reciente; el año se muestra junto al número |
| Moneda | Wikidata + mledoze | P38 vigente (sin fecha de término), con su código ISO 4217 (P498); el símbolo viene de mledoze |
| Forma de gobierno | es.wikipedia | campo «forma de gobierno» de la ficha del artículo del país. Se prefirió a la propiedad P122 de Wikidata, que da listas sueltas («presidencialismo», «república federal») en vez de una frase |
| Jefatura del Estado | Wikidata | P35 sin fecha de término; si hay varias vigentes, la de toma de posesión más reciente |
| Jefatura del gobierno | Wikidata | P6, igual |
| Cargo | Wikidata | P1906 y P1313. Los 27 que solo estaban en inglés se tradujeron con `herramientas/traducir_cargos.py` |
| Biografía | es.wikipedia | primera o primeras frases de la entrada del artículo, recortadas a ~270 caracteres |
| Foto | Wikimedia Commons | P18 del gobernante, miniatura de 220 px reducida a 200. El autor y la licencia se guardan y la ficha los muestra |
| Contornos del mapa | Natural Earth, vía world-atlas 110m | TopoJSON decodificado y simplificado con Douglas-Peucker; coordenadas a dos decimales |

## El área de historia

`datos/historia.json` lo rehace `herramientas/traer_historia.py`.

| Campo | Fuente | Cómo |
|---|---|---|
| Fecha de creación y de disolución de cada Estado | Wikidata | P571 y P576 del elemento del Estado, no del país que quedó después. Cuando hay varias fechas de disolución se toma la más tardía: para la RDA, Wikidata trae 1989 y 1990, y vale 1990 |
| Capital del Estado desaparecido | Wikidata | P36 del Estado |
| Repúblicas de la URSS y de Yugoslavia | Wikidata | se parte del país de hoy y se sigue «reemplaza a» (P1365). Lo que esa propiedad no encadena —Turkmenistán, y Bosnia, Serbia y Montenegro— se pide por la etiqueta en español de la república, que está escrita en el script |
| Capital de cada república | Wikidata | P36 de la república |
| Naciones del Reino Unido y provincias de los Países Bajos | Wikidata | P150 («contiene la división administrativa») de Q145 y Q55, con su P36 |
| País y capital de hoy | este mismo proyecto | se leen de `datos/paises.json`, no se vuelven a consultar: ahí ya están resueltas las decisiones de la casa (Esuatini y no Suazilandia, Sri Jayawardenapura Kotte y no Colombo), y si se preguntaran aparte el área de historia contradiría al atlas en la misma página |
| Preguntas de capitales del repaso | — | se arman solas con las filas de la tabla del bloque, así que no pueden desincronizarse del dato |

### Lo que es redacción, no dato

Los textos de cada bloque —la entrada, las claves y las preguntas de concepto—
están escritos, no traídos de ninguna base. Viven en la constante `TEXTOS` de
`herramientas/traer_historia.py` y se cotejaron con los artículos de es.wikipedia
que quedan anotados en el campo «fuente» de cada bloque, que la propia lámina
muestra al pie.

También es decisión editorial, y está en constantes con nombre al principio del
script:

- **Qué entra.** Los cuatro bloques que se habían pedido, más Checoslovaquia,
  las dos Alemanias, los países renombrados y las capitales que se mudaron.
- **Las quince repúblicas.** Son las que existían al disolverse la URSS en
  diciembre de 1991. La Unión tuvo otras antes —Transcaucasia,
  Carelo-Finesa— que no llegaron a ese día y no entran.
- **Kosovo.** No es miembro de la ONU y no está en el examen de los 195; en el
  bloque de Yugoslavia se explica el caso en el texto, no en la tabla.
- **Las dos capitales de Uzbekistán y Kazajistán.** Wikidata ofrece varias para
  la república soviética; se eligió la que valía al final (Taskent y Alma-Atá).
- **Türkiye y Cabo Verde** no están en la tabla de países renombrados: no
  cambiaron de nombre, pidieron que no se traduzca el que ya tenían. Eso se
  cuenta en las claves del bloque.
- **Los tres municipios del Caribe** —Bonaire, Saba y San Eustaquio— cuelgan de
  los Países Bajos por P150 pero no son provincias: van en una tabla aparte.

## Lo que se decidió a mano

Está todo arriba en `herramientas/traer_datos.py`, en constantes con nombre, no
escondido en el código.

- **Capitales dobles.** Se eligió una como respuesta principal y la otra cuenta
  igual de correcta, con una nota que explica el caso: Bolivia (Sucre / La Paz),
  Sudáfrica (Pretoria, Ciudad del Cabo, Bloemfontein), Sri Lanka, Esuatini,
  Yemen, Guinea Ecuatorial.
- **Nombres recientes.** Esuatini (no Suazilandia), Astaná (no Nursultán),
  Naipyidó, Chequia / República Checa. El nombre viejo se acepta como respuesta.
- **Casos disputados.** Israel y Palestina llevan nota sobre Jerusalén; no se
  toma partido, se describe el estatuto.
- **Somalilandia y el norte de Chipre** no son Estados reconocidos: su contorno
  se suma al de Somalia y Chipre para que el mapa no quede con huecos.
- **El código CY** cuelga en Wikidata del artículo de la isla, no del país; se
  apunta a mano al artículo «Chipre».

## Licencias

El texto de Wikipedia y los datos de Wikidata son libres (CC BY-SA y CC0
respectivamente). Las fotos son de Wikimedia Commons, cada una con su licencia;
el autor y la licencia se muestran debajo de cada retrato en la ficha.
