"""Carcasa parametrica para el ESP32-2424S012 (pantalla redonda 1.28").

Uso:  freecadcmd carcasa.py      (genera salida/carcasa.FCStd, STL y STEP)

Sistema de ejes: visto desde ATRAS de la placa, X a la derecha, Y arriba
(el USB-C apunta a +Y) y Z hacia atras. z=0 es la cara frontal de la carcasa.
Todas las cotas en mm.
"""

import math
import os

import FreeCAD as App
import Part
from FreeCAD import Vector as V

# ----------------------------------------------------------------------------
# Medidas de la placa (carpeta medidas/)
# ----------------------------------------------------------------------------
D_CRISTAL = 41.7        # fotos: 41.6 y 41.8
D_PCB = 36.9            # foto: 36.9
GROSOR_TOTAL = 8.0      # cristal -> parte alta del USB-C (fotos: 8.0 y 8.1)
USB_SALIENTE = 1.5      # lo que sobresale el USB-C del borde del PCB (estimado)
USB_ALTO = 3.2          # alto del conector USB-C sobre el PCB
ANG_JST = 128.0         # conector de bateria JST 1.25 (grados, USB = 90)
R_JST = 15.0
ANG_INTERRUPTOR = 166.0  # interruptor deslizante del borde
ANG_ANTENA = 270.0      # salida del cable de antena (u.FL)

# ----------------------------------------------------------------------------
# Parametros de la carcasa
# ----------------------------------------------------------------------------
HOLGURA = 0.3           # holgura radial cristal/carcasa
R_EXT = 26.0            # radio exterior (diametro 52)
LABIO = 1.0             # grosor del labio frontal que retiene el cristal
R_VENTANA = 19.8        # abertura frontal (solapa ~1 mm sobre el cristal)
R_MODULO = D_CRISTAL / 2 + HOLGURA          # alojamiento del cristal
Z_REPISA = LABIO + GROSOR_TOTAL + 0.4       # apoyo del vaso interior
R_CUELLO_INT = 22.2     # interior del cuello trasero
Z_HOMBRO = 12.0         # fin de la parte ancha / inicio del cuello roscado
Z_CUELLO = 16.0         # fin del cuello

# Rosca (perfil trapezoidal imprimible sin soportes)
PASO = 2.0
ROSCA_PROF = 0.9
ROSCA_CRESTA = 0.3
ROSCA_BASE = 1.7
R_ROSCA_MACHO = 23.45   # radio de fondo de la rosca macho (cuello)
ROSCA_HOLGURA = 0.3     # holgura radial macho/hembra

# USB-C: tunel para el conector macho del cable
USB_ANCHO = 13.5
USB_ALTO_TUNEL = 7.5
Z_USB = LABIO + GROSOR_TOTAL - USB_ALTO / 2  # eje del conector

# Vaso interior (separa placa y bateria y transmite el apriete de la tapa)
VASO_FONDO = 1.2
VASO_PARED = 1.0
R_VASO = R_CUELLO_INT - 0.2
Z_VASO_FIN = Z_CUELLO + 0.2
NERVIO_ALTO = 3.0       # hueco bajo la bateria para el conector JST y cables

# Bateria de referencia: LiPo 802530 (8 x 25 x 30, ~32 con la proteccion)
BAT = (32.0, 25.0, 8.0)
BAT_HUECO_Z = 8.6       # altura libre para la bateria

# Iman de sujecion (fotos: diametro 11.7, grosor 1.7). Uno va en la tapa y
# otro igual en la base.
IMAN_D = 11.7
IMAN_H = 1.7
IMAN_PIEL = 0.6         # plastico que queda entre el iman y el exterior
R_IMAN_HUECO = (IMAN_D + 0.4) / 2
IMAN_HUECO_Z = IMAN_H + 0.2

TAPA_FONDO = IMAN_PIEL + IMAN_HUECO_Z   # 2.5: cabe el iman por dentro
Z_TAPA_INI = Z_HOMBRO + 0.2
R_CAMARA = 21.2         # interior de la tapa de bateria

# Base de carga: la carcasa se apoya inclinada con el USB-C hacia abajo
INCLINACION = 25.0      # grados que se recuesta la pantalla desde la vertical
BASE_ANCHO = 34.0
BASE_ASIENTO = 22.0     # fondo de la cuna donde apoya el canto de la carcasa
BASE_HOLGURA = 0.3      # holgura radial cuna/carcasa
BASE_F_ATRAS = -12.0    # borde trasero de la huella (0 = bajo el respaldo)
BASE_V_ARRIBA = 11.0    # el respaldo sube esto por encima del centro
CLAVIJA_LIBRE = 28.0    # hueco bajo la carcasa para la clavija USB-C y el cable
CLAVIJA = (12.5, 6.5)   # seccion de la funda de la clavija
MUESCA_ANCHO = 15.0     # ranura central por la que baja la clavija
MUESCA_U0 = 5.0         # la ranura empieza a esta distancia del respaldo
CANAL_CABLE = (7.0, 6.0)  # canal inferior para sacar el cable por detras

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida")


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def cil(r, z0, z1):
    return Part.makeCylinder(r, z1 - z0, V(0, 0, z0))


def tubo(r_ext, r_int, z0, z1):
    return cil(r_ext, z0, z1).cut(cil(r_int, z0, z1))


def caja_polar(ang, r0, r1, ancho, z0, z1):
    """Caja de r0 a r1 en direccion `ang`, de anchura tangencial `ancho`."""
    c = Part.makeBox(r1 - r0, ancho, z1 - z0, V(r0, -ancho / 2, z0))
    c.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    return c


def rosca(r_fondo, prof, cresta, base, z0, z1):
    """Filete helicoidal que sobresale hacia fuera desde r_fondo."""
    r = r_fondo - 0.1  # se solapa con el cilindro base
    alto = (z1 - z0) + 2 * PASO
    helice = Part.makeHelix(PASO, alto, r)
    pts = [
        V(r, 0, -base / 2),
        V(r_fondo + prof, 0, -cresta / 2),
        V(r_fondo + prof, 0, cresta / 2),
        V(r, 0, base / 2),
        V(r, 0, -base / 2),
    ]
    perfil = Part.Wire(Part.makePolygon(pts))
    filete = Part.Wire(helice).makePipeShell([perfil], True, True)
    filete.translate(V(0, 0, z0 - PASO))
    # recorta a la zona util
    return filete.common(tubo(r_fondo + prof + 1, r - 0.5, z0, z1))


def tunel_usb():
    """Prisma de esquinas redondeadas que atraviesa la pared en +Y."""
    w, h, rad = USB_ANCHO, USB_ALTO_TUNEL, 2.5
    caja = Part.makeBox(w, 12, h, V(-w / 2, 17.5, Z_USB - h / 2))
    aristas = [e for e in caja.Edges
               if abs(e.Vertexes[0].Y - e.Vertexes[1].Y) > 1]
    return caja.makeFillet(rad, aristas)


# ----------------------------------------------------------------------------
# Piezas
# ----------------------------------------------------------------------------
def cuerpo():
    s = cil(R_EXT, 0, Z_HOMBRO).fuse(cil(R_ROSCA_MACHO, Z_HOMBRO, Z_CUELLO))
    # chaflan exterior frontal
    ch = 0.8
    s = s.cut(tubo(R_EXT + 1, R_EXT - ch, 0, ch).cut(
        Part.makeCone(R_EXT - ch, R_EXT, ch)))
    # ventana de la pantalla (con chaflan), alojamiento del modulo y cuello
    s = s.cut(Part.makeCone(R_VENTANA + 0.5, R_VENTANA, LABIO))
    s = s.cut(cil(R_MODULO, LABIO, Z_REPISA))
    s = s.cut(cil(R_CUELLO_INT, Z_REPISA, Z_CUELLO))
    # rosca macho
    s = s.fuse(rosca(R_ROSCA_MACHO, ROSCA_PROF, ROSCA_CRESTA, ROSCA_BASE,
                     Z_HOMBRO + 0.3, Z_CUELLO))
    # nervios antigiro para el vaso (0 y 180 grados)
    for ang in (0, 180):
        s = s.fuse(caja_polar(ang, R_MODULO + 0.15, R_CUELLO_INT + 0.2, 3.0,
                              Z_REPISA, Z_CUELLO))
    # USB-C
    s = s.cut(tunel_usb())
    # acceso al interruptor deslizante del borde del PCB
    z_int = LABIO + GROSOR_TOTAL - USB_ALTO + 0.7
    s = s.cut(caja_polar(ANG_INTERRUPTOR, 19, R_EXT + 1, 8.0,
                         z_int - 2.0, z_int + 2.0))
    return s.removeSplitter()


def vaso():
    s = cil(R_VASO, Z_REPISA, Z_REPISA + VASO_FONDO)
    z_f = Z_REPISA + VASO_FONDO
    s = s.fuse(tubo(R_VASO, R_VASO - VASO_PARED, z_f, Z_VASO_FIN))
    # nervios sobre los que apoya la bateria
    interior = cil(R_VASO - 0.5, z_f, z_f + NERVIO_ALTO)
    for (y, x0, x1) in ((-9.0, -18.5, 18.5), (3.0, -20.5, 20.5),
                        (13.0, 2.0, 15.0)):
        n = Part.makeBox(x1 - x0, 1.6, NERVIO_ALTO, V(x0, y - 0.8, z_f))
        s = s.fuse(n.common(interior))
    # ranuras antigiro
    for ang in (0, 180):
        s = s.cut(caja_polar(ang, R_VASO - VASO_PARED - 0.5, R_VASO + 1, 3.7,
                             Z_REPISA, Z_VASO_FIN))
    # ventana del conector de bateria (JST 1.25 vertical)
    s = s.cut(caja_polar(ANG_JST, R_JST - 4.5, R_JST + 4.5, 10.0,
                         Z_REPISA, z_f))
    # paso de la antena (cable u.FL + parche adhesivo de canto)
    s = s.cut(caja_polar(ANG_ANTENA, 16.5, 20.0, 9.0, Z_REPISA, z_f))
    # rebaje para el conector macho del cable USB (el faldon queda abierto
    # ahi para no tener que imprimir un puente curvo)
    s = s.cut(Part.makeBox(USB_ANCHO + 0.5, 6, Z_VASO_FIN - Z_REPISA,
                           V(-(USB_ANCHO + 0.5) / 2, 19.3, Z_REPISA)))
    return s.removeSplitter()


def z_interior_tapa(con_bateria):
    if con_bateria:
        return Z_REPISA + VASO_FONDO + NERVIO_ALTO + BAT_HUECO_Z
    return Z_VASO_FIN


def grosor(con_bateria):
    """Grosor de la carcasa montada (cara frontal -> cara trasera)."""
    return z_interior_tapa(con_bateria) + TAPA_FONDO


def tapa(con_bateria):
    r_hembra = R_ROSCA_MACHO + ROSCA_HOLGURA     # diametro menor hembra
    z_escalon = Z_VASO_FIN                       # aprieta el borde del vaso
    z_int = z_interior_tapa(con_bateria)
    z_fin = z_int + TAPA_FONDO
    s = cil(R_EXT, Z_TAPA_INI, z_fin)
    ch = 0.8
    s = s.cut(tubo(R_EXT + 1, R_EXT - ch, z_fin - ch, z_fin).cut(
        Part.makeCone(R_EXT, R_EXT - ch, ch, V(0, 0, z_fin - ch))))
    s = s.cut(cil(r_hembra, Z_TAPA_INI, z_escalon))
    if con_bateria:
        s = s.cut(cil(R_CAMARA, z_escalon, z_int))
    # alojamiento del iman, abierto hacia dentro (centrado: da igual como
    # quede girada la tapa al roscar)
    s = s.cut(cil(R_IMAN_HUECO, z_int, z_int + IMAN_HUECO_Z))
    # rosca hembra (filete algo mas gordo que el macho = holgura)
    s = s.cut(rosca(r_hembra, ROSCA_PROF, ROSCA_CRESTA + 0.2, ROSCA_BASE + 0.2,
                    Z_TAPA_INI, z_escalon))
    # entrada conica de la rosca
    s = s.cut(Part.makeCone(r_hembra + ROSCA_PROF + 0.1, r_hembra, 1.0,
                            V(0, 0, Z_TAPA_INI)))
    # estrias de agarre
    n = 30
    for i in range(n):
        a = math.radians(i * 360.0 / n)
        g = Part.makeCylinder(0.9, z_fin - Z_TAPA_INI - 2.0,
                              V((R_EXT + 0.35) * math.cos(a),
                                (R_EXT + 0.35) * math.sin(a),
                                Z_TAPA_INI + 1.0))
        s = s.cut(g)
    return s.removeSplitter()


# ----------------------------------------------------------------------------
# Base de carga
# ----------------------------------------------------------------------------
# La base se modela ya en su posicion de uso: X ancho, Y hacia delante,
# Z arriba y z=0 la mesa. El centro de la cara trasera de la carcasa queda en
# (0, 0, base_altura_eje()).
def base_altura_eje():
    """Altura del centro de la tapa para que la clavija no toque la mesa."""
    t = math.radians(INCLINACION)
    u_min = grosor(False) - Z_USB - USB_ALTO_TUNEL / 2
    return (R_EXT + CLAVIJA_LIBRE) * math.cos(t) - u_min * math.sin(t) + 1.0


def matriz_base(T=0.0):
    """Lleva la carcasa (de grosor T) a su posicion sobre la base.

    Con T=0 parte de un sistema con origen en el centro de la cara trasera.
    El USB-C (+Y de la carcasa) queda hacia abajo.
    """
    t = math.radians(INCLINACION)
    st, ct = math.sin(t), math.cos(t)
    return App.Matrix(-1, 0, 0, 0,
                      0, st, -ct, ct * T,
                      0, -ct, -st, st * T + base_altura_eje(),
                      0, 0, 0, 1)


def base():
    t = math.radians(INCLINACION)
    st, ct = math.sin(t), math.cos(t)
    r_cuna = R_EXT + BASE_HOLGURA
    f_frente = BASE_ASIENTO * ct + r_cuna * st
    # respaldo + cuna, definidos respecto a la cara trasera de la carcasa
    respaldo = Part.makeBox(200, 150 + BASE_V_ARRIBA, 120,
                            V(-100, -BASE_V_ARRIBA, 0))
    cuna = Part.makeBox(200, 150, BASE_ASIENTO, V(-100, 0, -BASE_ASIENTO))
    cuna = cuna.cut(Part.makeCylinder(r_cuna, BASE_ASIENTO + 2,
                                      V(0, 0, -BASE_ASIENTO - 1)))
    forma = respaldo.fuse(cuna)
    forma.transformShape(matriz_base())
    # huella: prisma vertical de esquinas redondeadas
    bloque = Part.makeBox(BASE_ANCHO, f_frente - BASE_F_ATRAS, 200,
                          V(-BASE_ANCHO / 2, BASE_F_ATRAS, 0))
    verticales = [e for e in bloque.Edges
                  if abs(e.Vertexes[0].Z - e.Vertexes[1].Z) > 1]
    bloque = bloque.makeFillet(3.0, verticales)
    s = bloque.common(forma)
    # ranura central para la clavija, abierta por delante y hasta la mesa
    f_muesca = MUESCA_U0 * ct + r_cuna * st
    s = s.cut(Part.makeBox(MUESCA_ANCHO, 100, 200,
                           V(-MUESCA_ANCHO / 2, f_muesca, -1)))
    # canal inferior: el cable sale por detras
    s = s.cut(Part.makeBox(CANAL_CABLE[0], f_muesca - BASE_F_ATRAS + 2,
                           CANAL_CABLE[1] + 1,
                           V(-CANAL_CABLE[0] / 2, BASE_F_ATRAS - 1, -1)))
    # ranura del iman: entra de canto por un lateral y hace tope en el centro
    r = (IMAN_D + 0.5) / 2
    ranura = Part.makeBox(100, 2 * r, IMAN_H + 0.3, V(-r, -r, IMAN_PIEL))
    ranura.transformShape(matriz_base())
    s = s.cut(ranura)
    return s.removeSplitter()


def clavija_referencia():
    """Clavija USB-C enchufada (funda + tramo recto de cable)."""
    return Part.makeBox(CLAVIJA[0], R_EXT + CLAVIJA_LIBRE - 20.0, CLAVIJA[1],
                        V(-CLAVIJA[0] / 2, 20.0, Z_USB - CLAVIJA[1] / 2))


def iman_tapa_referencia(con_bateria):
    z = z_interior_tapa(con_bateria) + IMAN_HUECO_Z - IMAN_H
    return cil(IMAN_D / 2, z, z + IMAN_H)


def placa_referencia():
    """Modelo simplificado de la placa para comprobar interferencias."""
    z_usb_top = LABIO + GROSOR_TOTAL
    z_pcb_top = z_usb_top - USB_ALTO
    r_pcb = D_PCB / 2
    piezas = [
        cil(D_CRISTAL / 2, LABIO, LABIO + 1.4),              # cristal
        cil(16.6, LABIO + 1.4, z_pcb_top - 1.0),             # LCD
        cil(r_pcb, z_pcb_top - 1.0, z_pcb_top),              # PCB
        Part.makeBox(9.0, 7.5, USB_ALTO,                     # USB-C
                     V(-4.5, r_pcb + USB_SALIENTE - 7.5, z_pcb_top)),
        caja_polar(ANG_JST, R_JST - 2.2, R_JST + 2.2, 5.0,   # JST bateria
                   z_pcb_top, z_pcb_top + 4.3),
        caja_polar(ANG_INTERRUPTOR, r_pcb - 3.0, r_pcb + 1.0, 6.5,
                   z_pcb_top, z_pcb_top + 1.5),              # interruptor
    ]
    s = piezas[0]
    for p in piezas[1:]:
        s = s.fuse(p)
    return s


def bateria_referencia():
    z0 = Z_REPISA + VASO_FONDO + NERVIO_ALTO
    return Part.makeBox(BAT[0], BAT[1], BAT[2],
                        V(-BAT[0] / 2, -BAT[1] / 2, z0))


# ----------------------------------------------------------------------------
# Generacion
# ----------------------------------------------------------------------------
def exportar_stl(shape, nombre, girar=False):
    import MeshPart
    s = shape.copy()
    if girar:  # las tapas se imprimen con el fondo sobre la cama
        s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    s.translate(V(0, 0, -s.BoundBox.ZMin))
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02,
                               AngularDeflection=0.15)
    m.write(os.path.join(SALIDA, nombre + ".stl"))
    return m.isSolid() and not m.hasNonManifolds(), m.BoundBox


def main():
    os.makedirs(SALIDA, exist_ok=True)
    doc = App.newDocument("carcasa")
    piezas = {
        "cuerpo": (cuerpo(), False),
        "vaso_interior": (vaso(), False),
        "tapa_usb": (tapa(False), True),
        "tapa_bateria": (tapa(True), True),
        "base": (base(), False),
    }
    ref = {"ref_placa": placa_referencia(), "ref_bateria": bateria_referencia(),
           "ref_clavija": clavija_referencia(),
           "ref_iman": iman_tapa_referencia(True)}

    print("\n--- Piezas ---")
    alto = {}
    for nombre, (s, girar) in piezas.items():
        doc.addObject("Part::Feature", nombre).Shape = s
        # la caja de la malla es exacta; la del B-rep se infla con la rosca
        cerrada, bb = exportar_stl(s, nombre, girar)
        alto[nombre] = bb.ZLength
        print(f"{nombre:14s} valido={s.isValid()} malla_cerrada={cerrada} "
              f"vol={s.Volume / 1000:.2f} cm3  diam={bb.XLength:.1f} "
              f"alto={bb.ZLength:.1f}")
    for nombre, s in ref.items():
        doc.addObject("Part::Feature", nombre).Shape = s

    # la tapa USB y la de bateria ocupan el mismo sitio: separa la USB
    doc.getObject("tapa_usb").Placement.Base = V(60, 0, 0)
    # la base se coloca bajo la carcasa montada con la tapa de bateria
    doc.getObject("base").Placement = App.Placement(
        matriz_base(grosor(True)).inverse())

    print("\n--- Interferencias (deben ser 0) ---")
    pares = [
        ("cuerpo", "ref_placa"), ("vaso_interior", "ref_placa"),
        ("cuerpo", "vaso_interior"), ("cuerpo", "tapa_bateria"),
        ("cuerpo", "tapa_usb"), ("vaso_interior", "tapa_bateria"),
        ("vaso_interior", "tapa_usb"), ("ref_bateria", "vaso_interior"),
        ("ref_bateria", "tapa_bateria"), ("ref_bateria", "cuerpo"),
        ("ref_iman", "tapa_bateria"), ("ref_iman", "ref_bateria"),
    ]
    todo = {k: v[0] for k, v in piezas.items()}
    todo.update(ref)
    for a, b in pares:
        v = todo[a].common(todo[b]).Volume
        print(f"{a:14s} x {b:14s} = {v:.3f} mm3")

    # carcasa sobre la base, con cada una de las dos tapas
    print("\n--- Base (interferencias deben ser 0) ---")
    b = todo["base"]
    for nombre, con_bat in (("tapa_usb", False), ("tapa_bateria", True)):
        m = matriz_base(grosor(con_bat))
        for otro in ("cuerpo", nombre, "ref_clavija"):
            c = todo[otro].copy()
            c.transformShape(m)
            print(f"base x {otro:12s} ({nombre}) = {b.common(c).Volume:.3f} "
                  f"mm3  z_min={c.BoundBox.ZMin:.1f}")
    # vuelco: el centro de gravedad debe caer dentro de la huella
    bb = b.BoundBox
    for nombre, con_bat in (("tapa_usb", False), ("tapa_bateria", True)):
        m = matriz_base(grosor(con_bat))
        masas = [(todo[n], 1.27e-3) for n in ("cuerpo", "vaso_interior", nombre)]
        masas.append((todo["ref_placa"], 14.0 / todo["ref_placa"].Volume))
        if con_bat:
            masas.append((todo["ref_bateria"], 12.0 / todo["ref_bateria"].Volume))
        mt, cy = 0.0, 0.0
        for sh, dens in masas:
            c = sh.copy()
            c.transformShape(m)
            for sol in c.Solids:
                mt += sol.Volume * dens
                cy += sol.Volume * dens * sol.CenterOfMass.y
        print(f"{nombre:12s}: carcasa {mt:.0f} g, c.d.g. en y={cy / mt:.1f} "
              f"(huella de la base y={bb.YMin:.1f}..{bb.YMax:.1f})")
    print(f"base: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm, "
          f"eje de la pantalla a {base_altura_eje():.1f} mm de la mesa")

    doc.recompute()
    doc.saveAs(os.path.join(SALIDA, "carcasa.FCStd"))
    Part.export([doc.getObject(n) for n in piezas],
                os.path.join(SALIDA, "carcasa.step"))
    print("\nGrosor con tapa USB:     %.1f mm" % (Z_TAPA_INI + alto["tapa_usb"]))
    print("Grosor con tapa bateria: %.1f mm" % (Z_TAPA_INI + alto["tapa_bateria"]))

main()
