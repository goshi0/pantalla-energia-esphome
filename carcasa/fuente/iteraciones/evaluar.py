"""Exporta y evalua una iteracion de base + tapa.

Uso desde iteraciones/itNN/diseno.py:
    evaluar(ns, carpeta)   # ns = globals() con base_v(), tapa_v(con_bateria)

Genera en la carpeta: base.stl, tapa_usb.stl, tapa_bateria.stl,
metricas.txt y vistas/*.png (renders, cortes y detalle de los imanes).
"""
import math
import os

import FreeCAD as App
import MeshPart
import Part
from FreeCAD import Vector as V

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

PLA = 1.24e-3            # g/mm3
COL = {"base": "#8a7fc0", "cuerpo": "#4c72b0", "tapa": "#55a868",
       "clavija": "#444444", "iman": "#e0b030", "placa": "#999999"}


def malla(s, fino=0.03):
    return MeshPart.meshFromShape(Shape=s, LinearDeflection=fino,
                                  AngularDeflection=0.15)


def exportar_stl(shape, ruta, girar=False):
    s = shape.copy()
    if girar:
        s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    s.translate(V(0, 0, -s.BoundBox.ZMin))
    m = malla(s, 0.02)
    m.write(ruta)
    return m.isSolid() and not m.hasNonManifolds()


def _tri(s, fino=0.05):
    m = malla(s, fino)
    pts = np.array([[p.x, p.y, p.z] for p in m.Points])
    return pts[np.array([f.PointIndices for f in m.Facets])]


def render(ax, piezas, elev, azim, lim):
    """Todas las piezas en una sola coleccion: matplotlib ordena por
    triangulo y no se ven piezas a traves de otras."""
    luz = np.array([0.4, 0.6, 0.9]); luz /= np.linalg.norm(luz)
    luz2 = np.array([-0.7, -0.4, 0.3]); luz2 /= np.linalg.norm(luz2)
    tris, cols = [], []
    for s, color in piezas:
        tri = _tri(s)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        k = 0.28 + 0.6 * np.abs(n @ luz) + 0.15 * np.abs(n @ luz2)
        c = np.array(matplotlib.colors.to_rgb(color))
        tris.append(tri)
        cols.append(np.clip(k[:, None] * c[None, :], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(tris),
                                         facecolors=np.concatenate(cols),
                                         linewidths=0))
    (x0, x1), (y0, y1), (z0, z1) = lim
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0))
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass


def corte(ax, piezas, punto, normal, ejes, titulo):
    for s, color in piezas:
        verts, codes = [], []
        for pl in malla(s, 0.02).crossSections([(punto, normal)], 0.01)[0]:
            if len(pl) < 3:
                continue
            for i, p in enumerate(pl):
                verts.append((getattr(p, ejes[0]), getattr(p, ejes[1])))
                codes.append(Path.MOVETO if i == 0 else Path.LINETO)
            verts.append(verts[-len(pl)]); codes.append(Path.CLOSEPOLY)
        if verts:
            ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec="k",
                                   lw=0.4, alpha=0.85))
    ax.set_aspect("equal"); ax.set_title(titulo, fontsize=10)
    ax.grid(alpha=0.3)


def evaluar(ns, carpeta):
    g = ns

    def solido(s):
        return s.Solids[0] if len(s.Solids) == 1 else s
    os.makedirs(os.path.join(carpeta, "vistas"), exist_ok=True)
    base = solido(g["base_v"]())
    tapas = {False: solido(g["tapa_v"](False)), True: solido(g["tapa_v"](True))}
    cuerpo = g["cuerpo"]()
    placa = g["placa_referencia"]()
    lin = []
    p = lin.append

    p("== Piezas ==")
    for nombre, s, girar in (("base", base, False),
                             ("tapa_usb", tapas[False], True),
                             ("tapa_bateria", tapas[True], True)):
        ok = exportar_stl(s, os.path.join(carpeta, nombre + ".stl"), girar)
        bb = malla(s, 0.05).BoundBox
        p(f"{nombre:13s} valido={s.isValid()} solidos={len(s.Solids)} "
          f"malla_cerrada={ok} vol={s.Volume / 1000:.1f} cm3 "
          f"masa_maciza_PLA={s.Volume * PLA:.0f} g  caja="
          f"{bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm")
    # masa impresa aproximada: 3 perimetros (~1.2 mm) + 15 % relleno
    area = base.Area
    pared = min(base.Volume, area / 2 * 1.2)
    masa_imp = (pared + 0.15 * (base.Volume - pared)) * PLA
    p(f"base: masa impresa estimada (1.2 mm de pared + 15 % relleno) "
      f"~{masa_imp:.0f} g")

    # voladizos: caras de la base que miran hacia abajo a mas de 45 grados
    # de la vertical (necesitarian soporte), por encima de la primera capa
    mb_ = malla(base, 0.05)
    area_mala = area_puente = area_iman = area_panal = 0.0
    inv_ = g["matriz_base"]().inverse()

    def _en_cavidad_iman(pt):
        """Interior de la ranura/pisador: en coordenadas locales, entre las
        caras delantera y trasera del respaldo y cerca del iman."""
        q = inv_.multiply(pt)
        return 0.3 < q.z < 6.0 and abs(q.y) < 8.0 and abs(q.x) < 25.0

    def _en_panal(pt):
        f_ = g.get("EN_PANAL")
        return bool(f_ and f_(inv_.multiply(pt)))
    for f in mb_.Facets:
        if f.Normal.z < -0.7072 and min(p_[2] for p_ in f.Points) > 0.3:
            if f.Normal.z < -0.999:
                area_puente += f.Area     # techo plano: puente
            elif _en_cavidad_iman(f.InCircle[0]):
                area_iman += f.Area       # techos cortos dentro de la ranura
            elif _en_panal(f.InCircle[0]):
                area_panal += f.Area      # techos de las celdas del panal
            else:
                area_mala += f.Area
    p(f"base: caras inclinadas con voladizo > 45 grados (necesitan soporte): "
      f"{area_mala:.0f} mm2; techos planos (puentes, revisar luces): "
      f"{area_puente:.0f} mm2; techos dentro de la cavidad del iman "
      f"(luces <= 2.3 mm): {area_iman:.0f} mm2; techos de celdas del panal: "
      f"{area_panal:.0f} mm2")

    p("\n== Interferencias con la base (deben ser 0) ==")
    H = g["base_altura_eje"]()
    for con_bat in (False, True):
        T = g["grosor"](con_bat)
        m = g["matriz_base"](T)
        nombre = "tapa_bateria" if con_bat else "tapa_usb"
        for etiqueta, s in (("cuerpo", cuerpo), (nombre, tapas[con_bat]),
                            ("clavija", g["clavija_referencia"]())):
            c = s.copy(); c.transformShape(m)
            p(f"base x {etiqueta:12s} ({nombre}) = "
              f"{base.common(c).Volume:.3f} mm3   z_min={c.BoundBox.ZMin:.1f}")

    # imanes: el de la tapa y el de la base en su sitio
    iman_base = g["iman_base_referencia"]()
    p(f"base x iman_base (debe ser ~0 o la interferencia de apriete) = "
      f"{base.common(iman_base).Volume:.3f} mm3")
    for con_bat in (False, True):
        it = g["iman_tapa_referencia"](con_bat)
        p(f"tapa {'bateria' if con_bat else 'usb'} x iman (apriete de las "
          f"costillas) = {tapas[con_bat].common(it).Volume:.3f} mm3")
    # distancia entre imanes (cara a cara)
    for con_bat in (False, True):
        it = g["iman_tapa_referencia"](con_bat)
        it.transformShape(g["matriz_base"](g["grosor"](con_bat)))
        d = it.distToShape(iman_base)[0]
        p(f"separacion entre imanes ({'bateria' if con_bat else 'usb'}): "
          f"{d:.2f} mm")

    p("\n== Estabilidad ==")
    bb = base.BoundBox
    sec = base.common(Part.makeBox(400, 400, 0.6, V(-200, -200, 0)))
    planta = sec.BoundBox
    p(f"huella sobre la mesa: x {planta.XMin:.1f}..{planta.XMax:.1f}, "
      f"y {planta.YMin:.1f}..{planta.YMax:.1f}")
    cdg_base = sum((so.CenterOfMass * so.Volume for so in base.Solids),
                   V()) * (1.0 / base.Volume)
    for con_bat in (False, True):
        T = g["grosor"](con_bat)
        m = g["matriz_base"](T)
        masas = [(cuerpo, PLA * 0.5), (tapas[con_bat], PLA * 0.5),
                 (placa, 14.0 / placa.Volume)]
        if con_bat:
            bat = g["bateria_referencia"]()
            masas.append((bat, 12.0 / bat.Volume))
        mt = cy = cz = 0.0
        for s, d in masas:
            c = s.copy(); c.transformShape(m)
            for sol in c.Solids:
                mt += sol.Volume * d
                cy += sol.Volume * d * sol.CenterOfMass.y
                cz += sol.Volume * d * sol.CenterOfMass.z
        cy /= mt; cz /= mt
        mb = masa_imp + g.get("LASTRE_G", 0.0)
        cy_t = (cy * mt + cdg_base.y * mb) / (mt + mb)
        margen = min(cy_t - planta.YMin, planta.YMax - cy_t)
        # fuerza horizontal hacia delante (al arrancar la pantalla) a la
        # altura del iman que vuelca el conjunto sobre el borde delantero
        brazo = planta.YMax - cy_t
        f_vuelco = (mt + mb) * 9.81e-3 * brazo / H
        p(f"{'bateria' if con_bat else 'usb':8s}: carcasa ~{mt:.0f} g "
          f"(c.d.g. y={cy:.1f}), conjunto c.d.g. y={cy_t:.1f}, margen al "
          f"borde mas cercano {margen:.1f} mm; con la base sola (~{mb:.0f} g "
          f"con lastre), "
          f"tirar hacia delante a la altura del iman vuelca con "
          f"~{mb * 9.81e-3 * (planta.YMax - cdg_base.y) / H:.2f} N")
    p(f"base: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm, "
      f"eje de la pantalla a {H:.1f} mm de la mesa")
    for extra in g.get("NOTAS_METRICAS", []):
        p(extra)

    with open(os.path.join(carpeta, "metricas.txt"), "w") as f:
        f.write("\n".join(lin) + "\n")
    print("\n".join(lin))

    # ------------------------------------------------------------------
    # Vistas
    # ------------------------------------------------------------------
    vis = os.path.join(carpeta, "vistas")
    T = g["grosor"](True)
    m = g["matriz_base"](T)
    cu = cuerpo.copy(); cu.transformShape(m)
    ta = tapas[True].copy(); ta.transformShape(m)
    cl = g["clavija_referencia"](); cl.transformShape(m)
    Tu = g["grosor"](False)
    mu = g["matriz_base"](Tu)
    cuu = cuerpo.copy(); cuu.transformShape(mu)
    tau = tapas[False].copy(); tau.transformShape(mu)
    clu = g["clavija_referencia"](); clu.transformShape(mu)
    pl = placa.copy(); pl.transformShape(m)
    conj = [(base, COL["base"]), (cu, COL["cuerpo"]), (ta, COL["tapa"]),
            (cl, COL["clavija"]), (pl, "#202428")]
    lim = ((-38, 38), (-30, 46), (0, 86))

    fig = plt.figure(figsize=(20, 13))
    # azim 90 = mirando desde delante (+Y) hacia atras
    vistas = [(conj, 15, 50, "Conjunto (tapa bateria) 3/4 delantero"),
              (conj, 5, 90, "Conjunto, frente"),
              (conj, 5, 0, "Conjunto, perfil derecho"),
              ([(base, COL["base"])], 25, 55, "Base sola 3/4 delantero"),
              ([(base, COL["base"])], 25, -125, "Base sola 3/4 trasero"),
              ([(base, COL["base"])], -40, 60, "Base sola desde abajo")]
    for i, (pz, el, az, t) in enumerate(vistas):
        ax = fig.add_subplot(2, 3, i + 1, projection="3d")
        render(ax, pz, el, az, lim)
        ax.set_title(t)
    fig.tight_layout(); fig.savefig(os.path.join(vis, "renders.png"), dpi=100)
    plt.close(fig)

    # cortes laterales y planta
    ib = iman_base.copy()
    it = g["iman_tapa_referencia"](True); it.transformShape(m)
    pz = conj + [(ib, COL["iman"]), (it, COL["iman"])]
    pzu = [(base, COL["base"]), (cuu, COL["cuerpo"]), (tau, COL["tapa"]),
           (clu, COL["clavija"]), (ib, COL["iman"])]
    fig, axs = plt.subplots(2, 3, figsize=(20, 13))
    xs = g.get("X_CORTE_LATERAL", 11.0)
    for ax, (pp, x, t) in zip(axs[0], (
            (pz, 0.37, "Corte central, tapa bateria (delante a la derecha)"),
            (pzu, 0.37, "Corte central, tapa USB"),
            (pz, xs, f"Corte lateral x={xs}, tapa bateria"))):
        corte(ax, pp, V(x, 0, 0), V(1, 0, 0), "yz", t)
        ax.set_xlim(-30, 55); ax.set_ylim(-2, 90)
    corte(axs[1][0], [(base, COL["base"])], V(0, 0, 2.5), V(0, 0, 1), "xy",
          "Planta de la base a 2.5 mm de la mesa")
    axs[1][0].set_xlim(-35, 35); axs[1][0].set_ylim(-30, 50)
    # plano del iman de la base, en coordenadas de la carcasa
    inv = g["matriz_base"]().inverse()
    bl = base.copy(); bl.transformShape(inv)
    il = iman_base.copy(); il.transformShape(inv)
    zc = g["IMAN_PIEL"] + g["IMAN_H"] / 2
    corte(axs[1][1], [(bl, COL["base"]), (il, COL["iman"])], V(0, 0, zc),
          V(0, 0, 1), "xy",
          "Base: plano medio del iman (vista desde atras)")
    axs[1][1].set_xlim(-30, 30); axs[1][1].set_ylim(30, -30)
    corte(axs[1][2], [(bl, COL["base"]), (il, COL["iman"])], V(10.0, 0, 0),
          V(1, 0, 0), "yz",
          "Base: corte transversal de la ranura en x=10 (z hacia atras)")
    axs[1][2].set_xlim(-12, 12); axs[1][2].set_ylim(12, -2)
    fig.tight_layout(); fig.savefig(os.path.join(vis, "cortes.png"), dpi=80)
    plt.close(fig)

    # detalle del iman en la ranura (a lo largo de la entrada) y de la tapa
    fig, axs = plt.subplots(1, 3, figsize=(20, 7))
    corte(axs[0], [(bl, COL["base"]), (il, COL["iman"])], V(0, 0.37, 0),
          V(0, 1, 0), "xz", "Base: ranura del iman a lo largo (z hacia atras)")
    axs[0].set_xlim(-22, 24); axs[0].set_ylim(10, -2)
    for ax, cb in zip(axs[1:], (False, True)):
        t = tapas[cb]; im = g["iman_tapa_referencia"](cb)
        zi = im.BoundBox.ZMin + g["IMAN_H"] / 2
        corte(ax, [(t, COL["tapa"]), (im, COL["iman"])], V(0, 0, zi),
              V(0, 0, 1), "xy",
              f"Tapa {'bateria' if cb else 'USB'}: alojamiento del iman")
        ax.set_xlim(-12, 12); ax.set_ylim(-12, 12)
    fig.tight_layout(); fig.savefig(os.path.join(vis, "imanes.png"), dpi=90)
    plt.close(fig)
    print("vistas en", vis)
