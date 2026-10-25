<div align="center">

[English](README.en.md) · **Español**

# Carcasa magnética para ESP32-2424S012 (pantalla redonda 1,28") con base de carga

<img src="img/renders.png" width="720"><br><sub>Vistas del modelo</sub>

</div>

Carcasa redonda para la placa **ESP32-2424S012** (ESP32-C3 con pantalla táctil redonda de 1,28") y una base de carga de estilo industrial en la que la pantalla parece flotar.

La carcasa se sujeta a la base con un **imán oculto** y queda recostada 25°. El USB-C apunta hacia abajo, así que puedes poner y quitar la pantalla sin desenchufar el cable.

## Características

- **Dos tapas traseras roscadas** e intercambiables:
  - **Tapa USB**: perfil bajo, 18,7 mm de grosor total, para usarla siempre enchufada.
  - **Tapa batería**: con cámara para una LiPo 802530 (~500–600 mAh), 24,7 mm de grosor total.
- **Imanes invisibles**: quedan tras 0,6 mm de plástico, sin pegamento a la vista.
  - En la tapa, el imán entra a presión entre 3 costillas radiales. Está centrado, así que funciona gire como gire la tapa.
  - En la base, el imán entra de canto por una ranura lateral. Lo fija un pisador flexible que aprieta su cara plana, nunca el canto. Un agujero expulsor permite sacarlo con un alfiler.
- **Base de estilo industrial**:
  - Zócalo hexagonal con panal grabado y respaldo hexagonal que queda oculto detrás de la pantalla.
  - Mordazas en V, como un bloque en V de taller, que centran la carcasa.
  - Celdas de panal pasantes.
- **Lastre con 4 tuercas M8** (DIN 934, 22 g) que se meten por debajo.
- **Salida del cable** por un túnel trasero. Sirve un cable USB-C recto normal.
- Acceso al interruptor deslizante con un palillo por un orificio lateral.
- **Todo sin soportes**: los STL ya están orientados para imprimir.

## Piezas

| Archivo | Descripción |
|---|---|
| [`cuerpo.stl`](stl/cuerpo.stl) | Aro frontal con labio para el cristal, túnel USB-C y rosca |
| [`vaso_interior.stl`](stl/vaso_interior.stl) | Sujeta la placa contra el labio y la separa de la batería |
| [`tapa_usb.stl`](stl/tapa_usb.stl) | Tapa trasera baja (solo USB) |
| [`tapa_bateria.stl`](stl/tapa_bateria.stl) | Tapa trasera alta con cámara para la batería |
| [`base.stl`](stl/base.stl) | Base de carga inclinada (48 × 63 × 82 mm) |
| [`probeta_iman_tapa.stl`](stl/probeta_iman_tapa.stl) | Prueba de ajuste del imán de la tapa (aprietes de 0,05 / 0,10 / 0,15 mm) |
| [`probeta_ranura_iman.stl`](stl/probeta_ranura_iman.stl) | Trozo del respaldo para probar la ranura y el pisador del imán de la base |

Imprime solo la tapa que vayas a usar, o las dos.
Los STL están en [`stl/`](stl/); GitHub los muestra en 3D al abrirlos.

## Material necesario

- 1 × placa ESP32-2424S012
- 2 × imanes de neodimio de Ø11,7 × 1,7 mm (medidos; busca los de 12 × 2 mm y comprueba que entran con la probeta)
- 4 × tuercas M8 DIN 934 (lastre)
- Opcional: batería LiPo 1S 802530 con protección y **conector JST de 1,25 mm** (no el JST-PH de 2,0 mm)
- Opcional: cianoacrilato, topes de silicona adhesivos

## Ajustes de impresión

- Capa de 0,2 mm o menos, 3 perímetros.
- Base: 15–20 % de relleno.
- **PETG** si vas a usar la batería, porque aguanta mejor el calor. PLA vale para la versión USB.
- **Imprime antes las dos probetas** para comprobar que tus imanes encajan: son pequeñas y tardan pocos minutos.

## Montaje

1. Mete la placa por detrás del cuerpo, con la pantalla hacia el labio y el USB-C alineado con su túnel.
2. Pasa la antena por la ranura del vaso y encájalo: sus ranuras entran en los nervios del cuerpo y le impiden girar.
3. Con batería: conéctala por la ventana del vaso y apóyala sobre él.
4. Mete el imán a presión en la tapa y enrósca la tapa.
5. Mete el imán de la base por la ranura lateral hasta que haga clic bajo el pisador. **Antes de fijarlo, comprueba que la carcasa y la base se atraen.** Si se repelen, dale la vuelta al imán.
6. Mete las 4 tuercas M8 en sus huecos de la cara inferior.

Con el firmware de este repo basta con **deslizar el dedo en vertical** sobre la pantalla para girarla 180°.

## ⚠️ Notas sobre la batería

- En estos conectores **no hay estándar de polaridad**: comprueba con un multímetro que el + de la batería coincide con el + de la placa.
- El cargador IP5306 puede dar hasta ~2 A, demasiado para una celda pequeña. Hasta confirmarlo, carga desde un puerto USB de ordenador.
- El IP5306 suele cortar la salida con consumos muy bajos, así que el deep sleep puede apagar la placa.

## Limitaciones conocidas

- No hay acceso a los botones BOOT/RESET ni salida para el conector de 4 pines.
- La posición del conector de batería, del interruptor y de la antena está sacada de fotos. Las ventanas tienen margen, pero revisa tu primera impresión.

## Diseño paramétrico

El modelo está hecho por código en **FreeCAD** (Python), en [`fuente/`](fuente/). Las holguras, la rosca,
la inclinación y la batería se ajustan desde las constantes del principio de `carcasa.py`.

```bash
cd fuente
freecadcmd carcasa.py          # cuerpo, vaso y tapas base -> fuente/salida/
./iteraciones/run.sh it04      # base industrial, tapas con imán y probetas -> iteraciones/it04/
```

`it04/diseno.py` reutiliza las cotas de `carcasa.py` y sustituye la base y las tapas; `evaluar.py`
comprueba voladizos, interferencias y grosores, y genera las vistas.

<div align="center"><img src="img/cortes.png" width="720"><br><sub>Cortes del conjunto</sub></div>

---

<div align="center"><sub>← Volver al [proyecto principal](../README.md)</sub></div>
