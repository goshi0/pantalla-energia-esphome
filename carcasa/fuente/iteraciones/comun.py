"""Carga las definiciones de ../carcasa.py (sin ejecutar main) para que cada
iteracion reutilice cotas y piezas y sustituya solo la base y la tapa.

Uso en itNN/diseno.py:
    exec(open(os.path.join(ITER, "comun.py")).read())
"""
import os
RAIZ = os.path.dirname(ITER)
_src = open(os.path.join(RAIZ, "carcasa.py")).read()
_src = _src[:_src.rindex("\nmain()")]
exec(compile(_src, os.path.join(RAIZ, "carcasa.py"), "exec"))
