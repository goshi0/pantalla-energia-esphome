<div align="center">

# ⚡ Pantalla de energía redonda

**Un mini panel de 240×240 px para la casa: consumo eléctrico en tiempo real, coste del día y del mes,
temperaturas de cada habitación… y un Gengar que te da consejos para ahorrar.**

![ESPHome](https://img.shields.io/badge/ESPHome-2026.10-000000?logo=esphome&logoColor=white)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-41BDF5?logo=homeassistant&logoColor=white)
![ESP32-C3](https://img.shields.io/badge/ESP32--C3-E7352C?logo=espressif&logoColor=white)
![LVGL](https://img.shields.io/badge/LVGL-9-7E5CAA)

![Todas las pantallas](banner.png)

</div>

---

## ✨ Qué hace

- **Potencia al instante** en un arco que pasa de verde a ámbar y a rojo según lo que gastas.
- **Precio PVPC** de la hora actual, coloreado según si es de las horas baratas o caras del día.
- **kWh y € de hoy y del mes**, calculados en el propio dispositivo y guardados en flash para que sobrevivan a un corte.
- **Temperatura y humedad** de cada habitación, más un **gráfico de las últimas 24 h**.
- **Alerta**: si te acercas a la potencia contratada, la pantalla se enciende sola y parpadea en rojo.
- **Gengar** 👻 flota, guiña el ojo, saca la lengua y suelta consejos de ahorro (algunos reaccionan al precio y al consumo del momento).

## 📱 Pantallas

Un **toque** pasa a la siguiente página y un **deslizamiento vertical** gira la pantalla 180° (se recuerda tras reiniciar).
A los 15 s sin tocarla vuelve a la principal.

| | | |
|:---:|:---:|:---:|
| <img src="preview-1-ahora.png" width="200"><br>**Ahora**<br>potencia y precio | <img src="preview-2-hoy.png" width="200"><br>**Hoy**<br>kWh y € del día | <img src="preview-3-mes.png" width="200"><br>**Mes**<br>kWh y € del mes |
| <img src="preview-5-casa.png" width="200"><br>**Casa**<br>temperatura y humedad | <img src="preview-6-grafico.png" width="200"><br>**Gráfico**<br>últimas 24 h | <img src="gengar.gif" width="200"><br>**Gengar**<br>consejos con humor |

<details>
<summary>🚨 Modo alerta</summary>
<br>
<div align="center"><img src="preview-4-alerta.png" width="200"></div>

Por encima de `power_alert_on_w` (5000 W) la pantalla se despierta, salta a la página de potencia
y parpadea en rojo hasta que el consumo baja de `power_alert_off_w` (4800 W).
</details>

## 👻 Gengar

<img align="right" src="gengar.gif" width="180">

Pixel art de 32×32 dibujado a mano (en código) y pintado ×3 en un canvas de LVGL.
Solo se anima mientras su página está visible, así que no gasta CPU el resto del tiempo.

Cada 7 s cambia el consejo. Uno de cada tres depende de lo que pase en ese momento:

- 🟢 precio barato → *«¡Luz barata ahora! Pon la lavadora, ji ji.»*
- 🔴 precio caro → *«¡Luz cara! Deja el horno para luego o te asusto.»*
- ⚡ consumo alto → *«¡Cuánto gastas! Hasta a mí me da miedo.»*

Los consejos están en el script `gengar_tip` de [`pantalla.yaml`](pantalla.yaml). Si añades alguno con
letras nuevas, recuerda incluirlas en los `glyphs` de `font_tip`.

<br clear="right">

## 🔧 Hardware

| Pieza | Detalle |
|---|---|
| Placa | ESP32-C3 (`esp32-c3-devkitm-1`) |
| Pantalla | GC9A01A redonda 240×240, SPI (CLK `GPIO6`, MOSI `GPIO7`, CS `GPIO10`, DC `GPIO2`) |
| Táctil | CST816 por I²C (SDA `4`, SCL `5`, INT `0`, RST `1`) |
| Retroiluminación | PWM en `GPIO3`, controlable desde Home Assistant |

Es la típica placa «ESP32-C3 round display» de 1,28".

## 🏠 Datos de Home Assistant

| Qué | Entidad |
|---|---|
| Potencia instantánea (W) | `sensor.shellyem_…_channel_2_power` (Shelly EM) |
| Energía total (kWh) | `sensor.shellyem_…_channel_2_energy` |
| Precio PVPC (€/kWh) y `price_ratio` | `sensor.esios_pvpc` |
| Temperatura / humedad | un sensor por habitación |

Cambia los `entity_id` en la sección `sensor:` para adaptarlo a tu casa.

## ⚙️ Personalización

Casi todo se ajusta en `substitutions` al principio de [`pantalla.yaml`](pantalla.yaml):

```yaml
power_green_max_w: "1800"   # verde por debajo
power_amber_max_w: "3600"   # ámbar por debajo, rojo por encima
power_gauge_max_w: "5500"   # fondo de escala (potencia contratada)
power_alert_on_w:  "5000"   # empieza a parpadear
graph_sample_min:  "10"     # minutos entre muestras del gráfico
gengar_tip_steps:  "47"     # pasos entre consejos (47 × 150 ms ≈ 7 s)
```

Los colores de cada página y habitación también están ahí (`col_*`).

## 🚀 Compilar y flashear

Necesitas un `secrets.yaml` con `wifi_ssid` y `wifi_password`.

**Con ESPHome normal:**

```bash
esphome run pantalla.yaml
```

**A través del add-on ESPHome de Home Assistant** con [`ha.py`](ha.py). Pon un token de larga duración en un archivo `.env`
(no se sube al repo) y ajusta `HOST` en el script:

```bash
uv run --with aiohttp python ha.py put pantalla.yaml pantalla.yaml   # subir la config
uv run --with aiohttp python ha.py validate pantalla.yaml
uv run --with aiohttp python ha.py install pantalla.yaml             # compilar
uv run --with aiohttp python ha.py upload pantalla.yaml              # OTA
uv run --with aiohttp python ha.py logs pantalla.yaml 60             # ver el log
```

> [!TIP]
> Si la OTA falla a medias y el dispositivo reinicia con *brownout*, la fuente USB va justa: reintenta o usa un cargador mejor.
> El firmware anterior sigue intacto.

## 📁 Estructura

```
pantalla.yaml     configuración ESPHome completa (UI LVGL incluida)
ha.py             cliente del add-on ESPHome de Home Assistant
preview-*.png     capturas de cada página
gengar.gif        animación de la página de Gengar
```

---

<div align="center">
<sub>Gengar es © Nintendo / Game Freak / The Pokémon Company. Proyecto personal sin ánimo de lucro.</sub>
</div>
