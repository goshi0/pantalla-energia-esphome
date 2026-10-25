#!/bin/sh
# Ejecuta una iteracion sin el ruido de progreso de FreeCAD: ./run.sh it01
cd "$(dirname "$0")" && freecadcmd "$1/diseno.py" 2>&1 | tr '\r' '\n' | grep -v -e '%)' -e '^\s*$' -e 'saving' -e 'Checking topology' -e 'FreeCAD' -e 'LGPL'
