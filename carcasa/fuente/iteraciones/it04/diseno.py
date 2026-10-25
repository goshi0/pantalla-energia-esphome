"""Iteracion 4: pulido de it03 (piel del iman, panal, mordazas, zocalo).

Uso:  ./run.sh it04

Base de it03:

Sugerencias del usuario para esta iteracion:
- retencion del iman sobre su CARA PLANA (un diente en el canto lo expulsa);
- estetica industrial en vez de organica;
- mantener la pantalla "flotando";
- motivos hexagonales de panal de abeja.

Forma: zocalo hexagonal alargado con chaflanes + una lamina de grosor
constante, paralela a la carcasa, que sube desde el zocalo y acaba en un
respaldo hexagonal mas pequeno que la carcasa (escondido detras) + dos
mordazas en V (como un bloque en V de taller) que recogen el canto inferior.
La lamina lleva ventanas de panal; la mas grande deja pasar el cable.

Coordenadas "locales" (las de la carcasa): origen en el centro de la cara
trasera, y hacia el USB (abajo en la base), z hacia atras (hacia el respaldo).
matriz_base() las lleva a la base: X ancho, Y hacia delante, Z arriba.
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ITER = os.path.dirname(AQUI)
exec(open(os.path.join(ITER, "comun.py")).read())
sys.path.insert(0, ITER)
from evaluar import evaluar, exportar_stl

# ----------------------------------------------------------------------------
# Parametros
# ----------------------------------------------------------------------------
ELEVACION = 16.0        # decision del usuario: sitio para la curva del cable
CABLE_R = 10.0          # radio de curvatura del cable
CABLE_D = 4.0

# Lamina y respaldo (en coordenadas locales)
LAMINA_E = 8.0          # grosor constante
RESPALDO_R = 21.5       # hexagono del respaldo (radio a los vertices; < 26)
LAMINA_ANCHO = 24.0     # ancho de la lamina por debajo del respaldo
CHAFLAN = 1.0           # chaflan de las aristas traseras

# Mordazas en V
V_ANG = 27.0            # cada cara de la V toca el canto a 27 grados del eje
MORDAZA_X = (9.5, 15.5)  # la V toca el canto en x = 11.9
MORDAZA_FONDO = 9.0     # cuanto abrazan el canto hacia delante
MORDAZA_TALUD = 50.0    # angulo de la cara inferior (>45: sin soportes)
MORDAZA_CHAFLAN = 1.0
MORDAZA_CHAFLAN_OK = True

# Panal: hexagonos con vertices arriba/abajo (eje y local)
PANAL_AF = 5.0          # entre caras (nervio >= 1.5 al canto y al chaflan)
PANAL_NERVIO = 1.6
PANAL_FILAS = [(31.5, (-6.8, 0.0, 6.8)), (37.4, (-3.4, 3.4)),
               (43.3, (-6.8, 0.0, 6.8))]
PASO_CABLE_AF = 10.0    # ventana grande del cable
PASO_CABLE_ZB = 11.0    # altura sobre la mesa del centro de esa ventana

# Zocalo: hexagono alargado (vertices delante y detras)
ZOCALO_PTS = [(0, -20), (24, -4), (24, 29), (0, 46), (-24, 29), (-24, -4)]
ZOCALO_H = 8.8            # 6.6 tuerca + 1.6 techo + 0.6 grabado
ZOCALO_CHAFLAN = 1.2
CANAL = (8.0, 6.0)      # tunel del cable bajo el zocalo
RANURA_Y0 = 10.0        # desde aqui hacia delante, ranura abierta por arriba
RANURA_CHAFLAN = 0.8
GRABADO_AF = 4.0        # panal rehundido en la cara superior del zocalo
GRABADO_NERVIO = 1.2
GRABADO_PROF = 0.6
TUERCA = (13.3, 6.6)    # tuerca M8 DIN 934: 13 e/c, 6.5 alto
TUERCAS = [(-13.5, 2.0), (13.5, 2.0), (-13.5, 22.0), (13.5, 22.0)]
PIES = []               # topes adhesivos: no necesitan hueco
PIE_D, PIE_H = 8.4, 1.0

# Iman de la base (entrada lateral por +x local)
RAN_HOLGURA_D = 1.0     # entrada 12.7 x 2.3
RAN_HOLGURA_E = 0.6
ALOJ_HOLGURA_D = 0.5    # alojamiento final 12.2 x 2.0
ALOJ_HOLGURA_E = 0.3
TRANSICION = (6.0, 9.0)
# Pisador: lamina flexible vertical (eje y local) con la raiz abajo, en
# macizo, y la punta sobre el centro del iman. Su taco plano aprieta la CARA
# PLANA del iman contra la piel: no empuja en el canto, no lo puede expulsar.
PISADOR_Y = (-3.0, 6.4)    # punta y raiz (la raiz cae fuera de la ranura, en macizo)
PISADOR_ANCHO = 6.0
PISADOR_E = 1.0
PISADOR_APRIETE = 0.25     # interferencia del taco con la cara del iman
PISADOR_TACO_X = (-3.0, 1.0)  # taco plano; de 1.0 a 3.0 rampa de entrada
PISADOR_TACO_LARGO = 4.0     # en y: de la punta (-3) a +1, centrado en el iman
CAMARA = 0.8               # hueco detras del pisador para que se doble
CORTE = 1.0
EXPULSOR_D = 1.6           # agujero en el lado opuesto para sacar el iman

# Tapa
COSTILLAS = 3
COSTILLA_R = 0.6
COSTILLA_APRIETE = 0.10
COSTILLA_CHAFLAN = 0.6

t = math.radians(INCLINACION)
ST, CT = math.sin(t), math.cos(t)
R_CUNA = R_EXT + BASE_HOLGURA

_altura_original = base_altura_eje


def base_altura_eje():
    return _altura_original() + ELEVACION


H = base_altura_eje()


def a_base(s):
    s = s.copy()
    s.transformShape(matriz_base())
    return s


def l2b(y, z):
    """Punto local (x = 0, y, z) -> (Y, Z) de la base."""
    return ST * y - CT * z, -CT * y - ST * z + H


def b2l(yb, zb):
    dy, dz = yb, zb - H
    return ST * dy - CT * dz, -CT * dy - ST * dz


def prisma(puntos, d, eje=V(0, 0, 1)):
    """Extruye un poligono cerrado (lista de V) a lo largo de eje*d."""
    pr = Part.Face(Part.makePolygon(puntos + [puntos[0]])).extrude(eje * d)
    if pr.Volume < 0:
        pr.reverse()
    return pr


def hexagono(cx, cy, af, z0, z1, vertice_y=True):
    """Prisma hexagonal en z; vertice_y: vertices sobre el eje y."""
    rc = af / math.sqrt(3)
    a0 = 90 if vertice_y else 0
    pts = [V(cx + rc * math.cos(math.radians(a0 + 60 * i)),
             cy + rc * math.sin(math.radians(a0 + 60 * i)), z0)
           for i in range(6)]
    return prisma(pts, z1 - z0)


# ----------------------------------------------------------------------------
# Iman de la base
# ----------------------------------------------------------------------------
def iman_base_referencia():
    return a_base(cil(IMAN_D / 2, IMAN_PIEL, IMAN_PIEL + IMAN_H))


def tejado_ranura(r, z0, e):
    """Tejado en gota sobre el lado alto de la ranura de entrada."""
    p1, p2 = l2b(-r, z0), l2b(-r, z0 + e)
    alto, bajo = (p1, p2) if p1[1] > p2[1] else (p2, p1)
    dz = abs(alto[0] - bajo[0]) * math.tan(math.radians(50))
    q = (alto[0], bajo[1] + dz)
    pts = [V(0, *b2l(*bajo)), V(0, *b2l(*alto)), V(0, *b2l(*q))]
    tej = prisma(pts, 40, V(1, 0, 0)).translated(V(TRANSICION[1], 0, 0))
    # nunca por delante de la piel del iman
    return tej.common(Part.makeBox(100, 100, 20, V(-50, -50, IMAN_PIEL)))


def ranura_iman():
    z0 = IMAN_PIEL
    r_e = (IMAN_D + RAN_HOLGURA_D) / 2
    e_e = IMAN_H + RAN_HOLGURA_E
    r_a = (IMAN_D + ALOJ_HOLGURA_D) / 2
    e_a = IMAN_H + ALOJ_HOLGURA_E
    x0, x1 = TRANSICION
    s = cil(r_a, z0, z0 + e_a)
    s = s.fuse(Part.makeBox(x0 + 0.01, 2 * r_a, e_a, V(0, -r_a, z0)))
    s = s.fuse(Part.makeBox(40, 2 * r_e, e_e, V(x1, -r_e, z0)))
    s = s.fuse(Part.makeLoft([
        Part.makePolygon([V(x0, -r_a, z0), V(x0, r_a, z0),
                          V(x0, r_a, z0 + e_a), V(x0, -r_a, z0 + e_a),
                          V(x0, -r_a, z0)]),
        Part.makePolygon([V(x1, -r_e, z0), V(x1, r_e, z0),
                          V(x1, r_e, z0 + e_e), V(x1, -r_e, z0 + e_e),
                          V(x1, -r_e, z0)])], True))
    s = s.fuse(tejado_ranura(r_e - 0.05, z0 + 0.05, e_e - 0.1))
    # expulsor: agujero horizontal desde la cara -x hasta el alojamiento
    exp = Part.makeCylinder(EXPULSOR_D / 2, 30, V(-r_a + 0.5, 0, 1.6),
                            V(-1, 0, 0))
    return s.fuse(exp)


def pisador():
    """(hueco, taco) del pisador que aprieta la cara plana del iman."""
    ya, yb = PISADOR_Y
    w = PISADOR_ANCHO
    c = CORTE
    z_aloj = IMAN_PIEL + IMAN_H + ALOJ_HOLGURA_E      # techo del alojamiento
    z_p1 = z_aloj + PISADOR_E                         # espalda del pisador
    z_cam = z_p1 + CAMARA
    hueco = Part.makeBox(w + 2 * c, yb - ya + c, CAMARA,
                         V(-w / 2 - c, ya - c, z_p1))                  # camara
    for x0 in (w / 2, -w / 2 - c):                                     # laterales
        hueco = hueco.fuse(Part.makeBox(c, yb - ya + c, z_cam - z_aloj + 0.01,
                                        V(x0, ya - c, z_aloj - 0.01)))
    hueco = hueco.fuse(Part.makeBox(w + 2 * c, c, z_cam - z_aloj + 0.01,
                                    V(-w / 2 - c, ya - c, z_aloj - 0.01)))
    # taco: plano sobre la cara del iman, rampa hacia la entrada (+x)
    zb = IMAN_PIEL + IMAN_H - PISADOR_APRIETE
    xa, xb = PISADOR_TACO_X
    perfil = [V(xa, ya, z_aloj + 0.2), V(xa, ya, zb), V(xb, ya, zb),
              V(xb + 2.0, ya, z_aloj + 0.2)]
    taco = prisma(perfil, PISADOR_TACO_LARGO, V(0, 1, 0))   # solo en la punta
    return hueco, taco.common(Part.makeBox(w, 50, 10, V(-w / 2, -25, 0)))


# ----------------------------------------------------------------------------
# Base
# ----------------------------------------------------------------------------
def lamina_local():
    """Respaldo hexagonal + lamina, en el plano de la cara trasera."""
    rc = RESPALDO_R
    hx = rc * math.cos(math.radians(30))
    w = LAMINA_ANCHO / 2
    pts = [V(0, -rc, 0), V(hx, -rc / 2, 0), V(hx, rc / 2, 0),
           V(w, rc / 2 + (hx - w) * math.tan(math.radians(60)), 0),
           V(w, 90, 0), V(-w, 90, 0),
           V(-w, rc / 2 + (hx - w) * math.tan(math.radians(60)), 0),
           V(-hx, rc / 2, 0), V(-hx, -rc / 2, 0)]
    s = prisma(pts, LAMINA_E)
    try:
        traseras = [e for e in s.Edges
                    if abs(e.BoundBox.ZMin - LAMINA_E) < 1e-6
                    and e.BoundBox.ZLength < 1e-6]
        s = s.makeChamfer(CHAFLAN, traseras)
    except Exception:
        pass
    return s


def panal_local():
    """Ventanas hexagonales de la lamina (atraviesan su grosor)."""
    s = None
    for (y, xs) in PANAL_FILAS:
        for x in xs:
            h = hexagono(x, y, PANAL_AF, -1, LAMINA_E + 1)
            s = h if s is None else s.fuse(h)
    # ventana grande del cable
    yl = (H - PASO_CABLE_ZB - ST * LAMINA_E / 2) / CT
    s = s.fuse(hexagono(0, yl, PASO_CABLE_AF, -1, LAMINA_E + 1))
    return s


def mordazas():
    """Bloques con la cara inferior a MORDAZA_TALUD, en coordenadas de base."""
    # punto inferior delantero del labio (y local de la V a x=0 no sirve: se
    # usa el extremo exterior de la mordaza)
    y_lab = R_CUNA + 5.0
    p_lab = l2b(y_lab, -MORDAZA_FONDO)
    # interseccion del talud con la cara delantera de la lamina (z local 0)
    tg = math.tan(math.radians(MORDAZA_TALUD))
    # recorre hacia atras-abajo desde p_lab hasta cortar el plano
    best = None
    for i in range(1, 4000):
        d = i * 0.01
        y, z = p_lab[0] - d, p_lab[1] - d * tg
        yl, zl = b2l(y, z)
        if zl >= 0.5:
            best = (y, z)
            break
    perfil = [V(0, best[0], best[1]), V(0, p_lab[0], p_lab[1]),
              V(0, p_lab[0] + 30, p_lab[1] + 40), V(0, best[0] - 30, p_lab[1] + 40)]
    x0, x1 = MORDAZA_X
    bloques = []
    for sgn in (1, -1):
        b = prisma(perfil, x1 - x0, V(1, 0, 0))
        b.translate(V(x0 if sgn > 0 else -x1, 0, 0))
        bloques.append(b)
    s = bloques[0].fuse(bloques[1])
    # solo por delante de la lamina y hasta MORDAZA_FONDO
    limite = a_base(Part.makeBox(100, 200, MORDAZA_FONDO + 0.5,
                                 V(-50, -100, -MORDAZA_FONDO)))
    s = s.common(limite)
    # chaflan inferior a 45 grados fuera de la lamina: ninguna arista suelta
    w = LAMINA_ANCHO / 2
    z0 = best[1]
    for sgn in (1, -1):
        cuna = prisma([V(sgn * w, -100, z0), V(sgn * 60, -100, z0 + 60 - w),
                       V(sgn * 60, -100, -10), V(sgn * w, -100, -10)], 300,
                      V(0, 1, 0))
        s = s.cut(cuna)
    try:
        # solo aristas altas (las vistas); un chaflan en las aristas de la
        # cara inferior crearia una cara de mas de 45 grados
        s = s.makeChamfer(MORDAZA_CHAFLAN, [e for e in s.Edges
                                            if e.Length > 2.0
                                            and e.BoundBox.ZMin > z0 + 6.0])
    except Exception:
        global MORDAZA_CHAFLAN_OK
        MORDAZA_CHAFLAN_OK = False
    return s


def corte_v():
    """Lo que hay por encima de las caras de la V y la propia carcasa."""
    a = math.radians(V_ANG)
    X = 40.0
    yv = lambda x: (R_CUNA - abs(x) * math.sin(a)) / math.cos(a)
    pts = [V(-X, -100, 0), V(X, -100, 0), V(X, yv(X), 0), V(0, yv(0), 0),
           V(-X, yv(-X), 0)]
    s = prisma(pts, 100, V(0, 0, -1))
    s = s.fuse(cil(R_CUNA, -100, 0))
    s = s.fuse(Part.makeBox(MORDAZA_X[0] * 2, 150, 100,
                            V(-MORDAZA_X[0], 15, -100)))      # clavija
    return s


def zocalo():
    pts = [V(x, y, 0) for (x, y) in ZOCALO_PTS]
    s = prisma(pts, ZOCALO_H)
    try:
        s = s.makeChamfer(ZOCALO_CHAFLAN, [e for e in s.Edges
                                           if abs(e.BoundBox.ZMin - ZOCALO_H) < 1e-6
                                           and e.BoundBox.ZLength < 1e-6])
    except Exception:
        pass
    return s


def grabado_panal(solido):
    """Celdas de 0.6 mm en la cara superior del zocalo, solo donde la cara
    esta libre (ni lamina, ni ranura, ni encima de las tuercas, ni cerca del
    chaflan)."""
    af, nerv = GRABADO_AF, GRABADO_NERVIO
    rc = af / math.sqrt(3)
    px, py = af + nerv, 1.5 * rc + nerv * math.sqrt(3) / 2
    zt = ZOCALO_H
    cara = Part.Face(Part.makePolygon([V(x, y, zt) for (x, y) in ZOCALO_PTS] +
                                      [V(ZOCALO_PTS[0][0], ZOCALO_PTS[0][1], zt)]))
    celdas = None
    motivos = {}
    j = 0
    y = -20.0
    while y < 46:
        x0 = 0.0 if j % 2 == 0 else px / 2
        for k in range(-8, 9):
            x = x0 + k * px
            h = hexagono(x, y, af, zt - GRABADO_PROF, zt + 1)
            bb = h.BoundBox
            # fuera del contorno con margen
            if cara.distToShape(Part.Vertex(V(x, y, zt)))[0] > 1e-6:
                continue
            borde = min(Part.Vertex(V(x, y, zt)).distToShape(e)[0]
                        for e in cara.Edges)
            if borde < rc + ZOCALO_CHAFLAN + 1.5:
                continue
            if abs(x) < CANAL[0] / 2 + RANURA_CHAFLAN + 1.5 + af / 2:
                continue
            # que la cara superior este libre: la celda entera fuera del resto
            # de la base por encima del zocalo
            arriba = Part.makeCylinder(rc + 1.2, 3, V(x, y, zt + 0.05))
            if solido.common(arriba).Volume > 1e-3:
                continue
            celdas = h if celdas is None else celdas.fuse(h)
        y += py
        j += 1
    return celdas if celdas is not None else Part.Shape()


def base_v():
    hueco_p, taco = pisador()
    lam = lamina_local().cut(panal_local())
    lam = lam.cut(ranura_iman().fuse(hueco_p)).fuse(taco)
    s = a_base(lam)
    s = s.fuse(mordazas())
    s = s.cut(a_base(corte_v()))
    s = s.common(Part.makeBox(300, 300, 300, V(-150, -150, 0)))
    s = s.fuse(zocalo())
    cw, ch = CANAL
    s = s.cut(Part.makeBox(cw, 100, ZOCALO_H + 2.0, V(-cw / 2, RANURA_Y0, -1)))
    s = s.cut(Part.makeBox(cw, 200, ch + 1, V(-cw / 2, -150, -1)))
    c8 = RANURA_CHAFLAN
    s = s.cut(prisma([V(-cw / 2 - c8, RANURA_Y0, ZOCALO_H + 0.01),
                      V(cw / 2 + c8, RANURA_Y0, ZOCALO_H + 0.01),
                      V(cw / 2, RANURA_Y0, ZOCALO_H - c8),
                      V(-cw / 2, RANURA_Y0, ZOCALO_H - c8)], 100, V(0, 1, 0)))
    g_ = grabado_panal(s)
    if not g_.isNull():
        s = s.cut(g_)
    for (x, y) in TUERCAS:
        s = s.cut(hexagono(x, y, TUERCA[0], -1, TUERCA[1], vertice_y=False))
    for (x, y) in PIES:
        s = s.cut(Part.makeCylinder(PIE_D / 2, PIE_H + 1, V(x, y, -1)))
    return s


# ----------------------------------------------------------------------------
# Tapa (igual que it02: costillas radiales achaflanadas)
# ----------------------------------------------------------------------------
def tapa_v(con_bateria):
    s = tapa(con_bateria)
    z_int = z_interior_tapa(con_bateria)
    rc = IMAN_D / 2 - COSTILLA_APRIETE + COSTILLA_R
    r_punta = rc - R_IMAN_HUECO
    for i in range(COSTILLAS):
        a = math.radians(90 + i * 360.0 / COSTILLAS)
        c = V(rc * math.cos(a), rc * math.sin(a), 0)
        rib = Part.makeCone(r_punta, COSTILLA_R, COSTILLA_CHAFLAN,
                            c + V(0, 0, z_int))
        rib = rib.fuse(Part.makeCylinder(COSTILLA_R,
                                         IMAN_HUECO_Z - COSTILLA_CHAFLAN,
                                         c + V(0, 0, z_int + COSTILLA_CHAFLAN)))
        s = s.fuse(rib.common(cil(R_IMAN_HUECO + 0.5, z_int,
                                  z_int + IMAN_HUECO_Z)))
    return s


def cable_referencia(con_bateria):
    """Cable de Ø4: sale de la clavija, curva R10 y vuelve por la mesa."""
    m = matriz_base(grosor(con_bateria))
    p = m.multiply(V(0, R_EXT + CLAVIJA_LIBRE, Z_USB))
    cy, cz = p.y - CABLE_R * CT, p.z - CABLE_R * ST
    a_m = math.radians((25.0 - 90.0) / 2)
    mid = V(0, cy + CABLE_R * math.cos(a_m), cz + CABLE_R * math.sin(a_m))
    fin = V(0, cy, max(cz - CABLE_R, CABLE_D / 2))
    arco = Part.Arc(V(0, p.y, p.z), mid, V(0, cy, cz - CABLE_R)).toShape()
    # tras la curva el cable cae a la mesa y vuelve por el tunel
    zb = cz - CABLE_R
    p1 = V(0, cy, zb)
    p2 = V(0, cy - max(zb - CABLE_D / 2, 0.01) * 2.0, CABLE_D / 2)
    tramos = [arco]
    if zb - CABLE_D / 2 > 0.05:
        tramos.append(Part.LineSegment(p1, p2).toShape())
    else:
        p2 = p1
    tramos.append(Part.LineSegment(p2, V(0, -40, p2.z)).toShape())
    camino = Part.Wire(tramos)
    tang = V(0, ST, -CT)
    circ = Part.Wire(Part.makeCircle(CABLE_D / 2, V(0, p.y, p.z), tang))
    return camino.makePipeShell([circ], True, True), (p.y, p.z, cz - CABLE_R)


def EN_PANAL(q):
    """q en coordenadas locales: dentro de alguna celda del panal."""
    if not (-0.5 < q.z < LAMINA_E + 0.5):
        return False
    celdas = [(x, y, PANAL_AF) for (y, xs) in PANAL_FILAS for x in xs]
    celdas.append((0.0, (H - PASO_CABLE_ZB - ST * LAMINA_E / 2) / CT, PASO_CABLE_AF))
    return any(math.hypot(q.x - x, q.y - y) < af / math.sqrt(3) + 0.3
               for (x, y, af) in celdas)


LASTRE_G = 4 * 5.6
NOTAS_METRICAS = [f"lastre: 4 tuercas M8 DIN 934 = {LASTRE_G:.0f} g"]
_b = base_v()
for cb in (False, True):
    cab, (py, pz, zb) = cable_referencia(cb)
    NOTAS_METRICAS.append(
        f"cable Ø{CABLE_D:.0f} ({'bateria' if cb else 'usb'}): clavija acaba en "
        f"y={py:.1f} z={pz:.1f}, curva R{CABLE_R:.0f} hasta z={zb:.1f}; "
        f"interferencia cable x base = {_b.common(cab).Volume:.1f} mm3 "
        f"(debe ser 0)")
del _b

X_CORTE_LATERAL = 13.0


def paredes():
    """Pared minima entre cada cavidad cerrada y el exterior."""
    lam = lamina_local()
    hueco_p, _ = pisador()
    zz = [f for f in zocalo().Faces if f.BoundBox.ZLength > 1e-6
          or f.BoundBox.ZMin > 1e-6]          # todo menos la cara de apoyo
    res = []
    camara = Part.makeBox(PISADOR_ANCHO + 2 * CORTE,
                          PISADOR_Y[1] - PISADOR_Y[0] + CORTE, CAMARA,
                          V(-PISADOR_ANCHO / 2 - CORTE, PISADOR_Y[0] - CORTE,
                            IMAN_PIEL + IMAN_H + ALOJ_HOLGURA_E + PISADOR_E))
    d_pan = camara.distToShape(panal_local())[0]
    res.append(("camara del pisador -> exterior de la lamina",
                min(camara.distToShape(Part.Shell(lam.Faces))[0], d_pan)))
    delante = [f for f in lam.Faces if f.BoundBox.ZLength < 1e-6
               and abs(f.BoundBox.ZMax) < 1e-6]
    res.append(("[piel, minimo 0.6] ranura+tejado+expulsor -> cara delantera",
                 ranura_iman().distToShape(Part.Shell(delante))[0]))
    res.append(("nervio del panal -> canto de la lamina",
                min(hexagono(x, y, PANAL_AF, 0, LAMINA_E).distToShape(
                    Part.Shell([f for f in lam.Faces if f.BoundBox.ZLength > 1e-6]))[0]
                    for (y, xs) in PANAL_FILAS for x in xs)))
    alto = [f for f in lam.Faces if f.BoundBox.ZLength > 1e-6]
    r_e = (IMAN_D + RAN_HOLGURA_D) / 2
    tej = tejado_ranura(r_e - 0.05, IMAN_PIEL + 0.05, IMAN_H + RAN_HOLGURA_E - 0.1)
    res.append(("tejado de la ranura -> canto del hexagono (cuna)",
                tej.distToShape(Part.Shell([f for f in alto
                                            if f.BoundBox.YMax < -5.0]))[0]))
    sh = Part.Shell(zz)
    canal = Part.makeBox(CANAL[0], 200, CANAL[1] + 1, V(-CANAL[0] / 2, -150, -1)).fuse(
        Part.makeBox(CANAL[0], 100, ZOCALO_H + 0.5, V(-CANAL[0] / 2, RANURA_Y0, -1)))
    for (x, y) in TUERCAS:
        h = hexagono(x, y, TUERCA[0], 0.01, TUERCA[1], vertice_y=False)
        res.append((f"tuerca ({x:+.1f},{y:+.1f}) -> contorno/techo",
                    h.distToShape(sh)[0]))
        res.append((f"tuerca ({x:+.1f},{y:+.1f}) -> canal del cable",
                    h.distToShape(canal)[0]))
    return res


def probeta_ranura():
    """Trozo del respaldo con la ranura y el pisador, en la misma inclinacion
    que en la base, cortado con un apoyo plano. Para probar el iman."""
    hueco_p, taco = pisador()
    lam = lamina_local().cut(ranura_iman().fuse(hueco_p)).fuse(taco)
    trozo = lam.common(Part.makeBox(36, 32, 20, V(-18, -11, -1)))
    trozo = a_base(trozo)
    zc = l2b(17.0, 0.0)[1]
    trozo = trozo.common(Part.makeBox(300, 300, 300, V(-150, -150, zc)))
    return trozo


for nombre, d in paredes():
    lim = "" if nombre.startswith("[piel") else " (minimo 1.5)"
    NOTAS_METRICAS.append(f"pared {nombre}: {d:.2f} mm{lim}")
NOTAS_METRICAS.append(f"chaflan de 1 mm en las mordazas aplicado: {MORDAZA_CHAFLAN_OK}")
ok = exportar_stl(probeta_ranura(), os.path.join(AQUI, "probeta_ranura_iman.stl"))
NOTAS_METRICAS.append(f"probeta_ranura_iman.stl generada (malla cerrada={ok})")
evaluar(globals(), AQUI)
