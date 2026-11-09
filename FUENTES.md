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
