import sys, os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida")
OUT = os.path.join(P, "vistas")
os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(P, "carcasa.FCStd"))
# la base esta modelada en su posicion de uso; su Placement en el documento
# es la inversa de la matriz que lleva la carcasa (con bateria) a la base
M_BASE = doc.getObject("base").Placement.toMatrix().inverse()
sh = {}
for o in doc.Objects:
    c = o.Shape.copy(); c.Placement = App.Placement(); sh[o.Name] = c
col = {"cuerpo": "#4c72b0", "vaso_interior": "#dd8452", "tapa_usb": "#55a868",
       "tapa_bateria": "#55a868", "ref_placa": "#999999", "ref_bateria": "#c44e52",
       "base": "#8172b3", "ref_clavija": "#444444", "ref_iman": "#e0c040"}

for n, s in sh.items():
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2)
    bb = m.BoundBox
    print(f"{n:14s} malla x=[{bb.XMin:.2f},{bb.XMax:.2f}] y=[{bb.YMin:.2f},{bb.YMax:.2f}] z=[{bb.ZMin:.2f},{bb.ZMax:.2f}]")

mallas = {n: MeshPart.meshFromShape(Shape=s, LinearDeflection=0.03, AngularDeflection=0.2)
          for n, s in sh.items()}
for n, m in mallas.items():
    print(f"{n:14s} solido={m.isSolid()} no_manifold={m.hasNonManifolds()} "
          f"autointersec={m.hasSelfIntersections()} vol={m.Volume/1000:.2f}")


def seccion(ax, nombres, normal, titulo):
    """Corte de las mallas (mas robusto que cortar el B-rep)."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    yz = abs(normal.x) > 0.5
    base = V(0.37, 0, 0) if yz else V(0, 0.37, 0)  # fuera de costuras
    for n in nombres:
        verts, codes = [], []
        for pl in mallas[n].crossSections([(base, normal)], 0.01)[0]:
            if len(pl) < 3:
                continue
            for i, p in enumerate(pl):
                verts.append(((p.y if yz else p.x), p.z))
                codes.append(Path.MOVETO if i == 0 else Path.LINETO)
            verts.append(verts[-len(pl)]); codes.append(Path.CLOSEPOLY)
        if verts:
            ax.add_patch(PathPatch(Path(verts, codes), fc=col[n], ec="k",
                                   lw=0.4, alpha=0.85))
    ax.set_aspect("equal"); ax.set_title(titulo); ax.grid(alpha=0.3)
    ax.set_xlim(-28, 28); ax.set_ylim(27, -1)

fig, axs = plt.subplots(2, 2, figsize=(16, 13))
bat = ["cuerpo", "vaso_interior", "tapa_bateria", "ref_placa", "ref_bateria",
       "ref_iman"]
usb = ["cuerpo", "vaso_interior", "tapa_usb", "ref_placa"]
seccion(axs[0][0], bat, V(1, 0, 0), "Bateria - corte YZ (USB a la derecha, frontal arriba)")
seccion(axs[0][1], bat, V(0, 1, 0), "Bateria - corte XZ")
seccion(axs[1][0], usb, V(1, 0, 0), "Solo USB - corte YZ")
seccion(axs[1][1], usb, V(0, 1, 0), "Solo USB - corte XZ")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "secciones.png"), dpi=110)

def render(ax, nombres, elev, azim, expl=None):
    for n in nombres:
        s = sh[n].copy()
        if expl: s.translate(V(0, 0, expl.get(n, 0)))
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.08, AngularDeflection=0.3)
        pts = np.array([[p.x, p.y, p.z] for p in m.Points])
        tri = pts[np.array([f.PointIndices for f in m.Facets])]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nrm /= (np.linalg.norm(nrm, axis=1)[:, None] + 1e-12)
        L = np.array([0.3, -0.5, 0.8]); L = L / np.linalg.norm(L)
        sh_ = 0.35 + 0.65 * np.abs(nrm @ L)
        base = np.array(matplotlib.colors.to_rgb(col[n]))
        pc = Poly3DCollection(tri, facecolors=sh_[:, None] * base[None, :], linewidths=0)
        ax.add_collection3d(pc)
    ax.set_xlim(-30, 30); ax.set_ylim(-30, 30); ax.set_zlim(-20, 40)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()

fig = plt.figure(figsize=(18, 12))
sh["tapa_usb"].translate(V(0,0,0))
ex = {"cuerpo": 0, "ref_placa": 0, "vaso_interior": 14, "ref_bateria": 24, "tapa_bateria": 36}
for i, (noms, el, az, e) in enumerate([
    (["cuerpo", "tapa_bateria"], -25, 60, None),
    (["cuerpo", "tapa_bateria"], 25, 100, None),
    (["cuerpo", "ref_placa"], 50, 100, None),
    (["cuerpo", "ref_placa", "vaso_interior"], 50, 100, None),
    (["cuerpo", "vaso_interior", "ref_bateria", "tapa_bateria"], 20, 100, ex),
    (["tapa_bateria"], -50, 100, None)]):
    ax = fig.add_subplot(2, 3, i + 1, projection="3d")
    render(ax, noms, el, az, e)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "render.png"), dpi=90)

# ---------------------------------------------------------------------------
# Carcasa (con bateria) sobre la base de carga
# ---------------------------------------------------------------------------
from matplotlib.path import Path
from matplotlib.patches import PathPatch

en_base = ["cuerpo", "vaso_interior", "tapa_bateria", "ref_placa",
           "ref_bateria", "ref_iman", "ref_clavija"]
dock = {"base": sh["base"]}
for n in en_base:
    c = sh[n].copy(); c.transformShape(M_BASE); dock[n] = c
mdock = {n: MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05,
                                   AngularDeflection=0.2)
         for n, s in dock.items()}


def corte(ax, base_pt, normal, ejes, titulo):
    for n, m in mdock.items():
        verts, codes = [], []
        for pl in m.crossSections([(base_pt, normal)], 0.01)[0]:
            if len(pl) < 3:
                continue
            for i, p in enumerate(pl):
                verts.append((getattr(p, ejes[0]), getattr(p, ejes[1])))
                codes.append(Path.MOVETO if i == 0 else Path.LINETO)
            verts.append(verts[-len(pl)]); codes.append(Path.CLOSEPOLY)
        if verts:
            ax.add_patch(PathPatch(Path(verts, codes), fc=col[n], ec="k",
                                   lw=0.4, alpha=0.85))
    ax.set_aspect("equal"); ax.set_title(titulo); ax.grid(alpha=0.3)


def render_dock(ax, nombres, elev, azim):
    for n in nombres:
        m = MeshPart.meshFromShape(Shape=dock[n], LinearDeflection=0.08,
                                   AngularDeflection=0.3)
        pts = np.array([[p.x, p.y, p.z] for p in m.Points])
        tri = pts[np.array([f.PointIndices for f in m.Facets])]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nrm /= (np.linalg.norm(nrm, axis=1)[:, None] + 1e-12)
        L = np.array([0.3, 0.5, 0.8]); L = L / np.linalg.norm(L)
        luz = 0.35 + 0.65 * np.abs(nrm @ L)
        c = np.array(matplotlib.colors.to_rgb(col[n]))
        ax.add_collection3d(Poly3DCollection(tri, facecolors=luz[:, None] * c[None, :],
                                             linewidths=0))
    ax.set_xlim(-45, 45); ax.set_ylim(-30, 60); ax.set_zlim(0, 90)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()


fig = plt.figure(figsize=(18, 12))
ax = fig.add_subplot(2, 3, 1)
corte(ax, V(0.37, 0, 0), V(1, 0, 0), "yz", "Corte lateral por el centro (delante a la derecha)")
ax.set_xlim(-20, 65); ax.set_ylim(-2, 90)
ax = fig.add_subplot(2, 3, 2)
corte(ax, V(12, 0, 0), V(1, 0, 0), "yz", "Corte lateral por una mejilla (x=12)")
ax.set_xlim(-20, 65); ax.set_ylim(-2, 90)
ax = fig.add_subplot(2, 3, 3)
corte(ax, V(0, 0, 3), V(0, 0, 1), "xy", "Planta a 3 mm de la mesa (canal del cable)")
ax.set_xlim(-30, 30); ax.set_ylim(-20, 65)
solo = ["base"]
todo_d = ["base", "cuerpo", "tapa_bateria", "ref_clavija"]
for i, (noms, el, az) in enumerate([(todo_d, 15, 35), (solo, 30, 35), (solo, 25, 140)]):
    ax = fig.add_subplot(2, 3, 4 + i, projection="3d")
    render_dock(ax, noms, el, az)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "base.png"), dpi=90)
print("ok")
