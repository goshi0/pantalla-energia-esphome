"""Build and flash pantalla.yaml through the ESPHome add-on of Home Assistant.
Compila y flashea pantalla.yaml a través del add-on ESPHome de Home Assistant.

EN: Handy when the ESPHome dashboard runs as a Home Assistant add-on (it holds the
    Wi-Fi secrets) and you want to drive it from the command line.
ES: Útil cuando el panel de ESPHome corre como add-on de Home Assistant (es quien
    guarda los secretos del Wi-Fi) y quieres manejarlo desde la terminal.

Setup · Preparación
    Create a .env file next to this script · Crea un archivo .env junto a este script:
        HA_URL=http://homeassistant.local:8123
        HA_TOKEN=<long-lived access token · token de acceso de larga duración>
    (A .env holding only the bare token also works · También vale un .env con solo el token.)

Usage · Uso
    uv run --with aiohttp python ha.py <op> <config> [arg]

    get      pantalla.yaml                   print the config stored in the add-on · muestra la config del add-on
    put      pantalla.yaml ./pantalla.yaml   upload a local file to the add-on · sube un archivo local al add-on
    validate pantalla.yaml                   check the config · valida la config
    install  pantalla.yaml                   compile (and OTA if the add-on does) · compila (y OTA si el add-on lo hace)
    upload   pantalla.yaml                   OTA-flash the compiled firmware · flashea por OTA el firmware compilado
    logs     pantalla.yaml 60                follow the device log for 60 s · sigue el log del dispositivo 60 s
    raw      <command> '<json args>'         send any dashboard command · envía cualquier comando al panel
"""
import asyncio
import json
import os
import sys

import aiohttp


def load_env():
    """Read HA_URL / HA_TOKEN from the environment or .env · Lee HA_URL / HA_TOKEN del entorno o de .env."""
    env = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
            else:
                env["HA_TOKEN"] = line  # bare token · solo el token
    env.update({k: v for k, v in os.environ.items() if k in ("HA_URL", "HA_TOKEN")})
    if "HA_TOKEN" not in env:
        sys.exit("HA_TOKEN missing: put it in .env · Falta HA_TOKEN: ponlo en .env")
    return env.get("HA_URL", "http://homeassistant.local:8123").rstrip("/"), env["HA_TOKEN"]


HOST, TOKEN = load_env()


class HA:
    """Home Assistant websocket API · API websocket de Home Assistant."""

    async def __aenter__(self):
        self.s = aiohttp.ClientSession()
        self.ws = await self.s.ws_connect(HOST + "/api/websocket", max_msg_size=0)
        await self.ws.receive_json()  # auth_required
        await self.ws.send_json({"type": "auth", "access_token": TOKEN})
        r = await self.ws.receive_json()
        assert r["type"] == "auth_ok", r
        self.i = 0
        return self

    async def __aexit__(self, *a):
        await self.ws.close()
        await self.s.close()

    async def cmd(self, **kw):
        """Send a command and wait for its result · Envía un comando y espera su resultado."""
        self.i += 1
        await self.ws.send_json({"id": self.i, **kw})
        while True:
            r = await self.ws.receive_json()
            if r.get("id") == self.i and r.get("type") == "result":
                return r

    async def sup(self, endpoint, method="get", data=None):
        """Call the Supervisor API · Llama a la API del Supervisor."""
        kw = dict(type="supervisor/api", endpoint=endpoint, method=method)
        if data is not None:
            kw["data"] = data
        return await self.cmd(**kw)

    async def esphome(self):
        """Return the ingress URL of the ESPHome add-on (and log in to it).
        Devuelve la URL de ingress del add-on ESPHome (e inicia sesión en ella)."""
        addons = (await self.sup("/addons"))["result"]["addons"]
        slug = next(a["slug"] for a in addons if "esphome" in a["slug"])
        info = (await self.sup(f"/addons/{slug}/info"))["result"]
        session = (await self.sup("/ingress/session", "post"))["result"]["session"]
        self.s.cookie_jar.update_cookies({"ingress_session": session})
        return HOST + info["ingress_url"].rstrip("/")


class Dashboard:
    """ESPHome Device Builder websocket API · API websocket del ESPHome Device Builder."""

    def __init__(self, ha):
        self.ha = ha
        self.n = 0

    async def __aenter__(self):
        base = await self.ha.esphome()
        self.w = await self.ha.s.ws_connect(base.replace("http", "ws", 1) + "/ws", max_msg_size=0)
        self.info = await self.w.receive_json()  # server / ESPHome versions · versiones
        return self

    async def __aexit__(self, *a):
        await self.w.close()

    async def call(self, command, stream=None, timeout=1500, **args):
        """Run a command; stream its output lines to `stream` and return the result.
        Ejecuta un comando; pasa su salida a `stream` y devuelve el resultado."""
        self.n += 1
        mid = self.n
        await self.w.send_json({"command": command, "message_id": mid, "args": args})
        async with asyncio.timeout(timeout):
            while True:
                m = await self.w.receive()
                if m.type != aiohttp.WSMsgType.TEXT:
                    raise RuntimeError(f"ws closed: {m}")
                d = json.loads(m.data)
                if str(d.get("message_id")) != str(mid):
                    continue
                if "error_code" in d:
                    raise RuntimeError(f"{d['error_code']}: {d.get('details')}")
                if "event" in d:
                    if d["event"] == "output" and stream:
                        stream(d["data"])
                    elif d["event"] == "result":
                        return d["data"]
                    continue
                if "result" in d:
                    return d["result"]


def out(x):
    sys.stdout.write((x if isinstance(x, str) else json.dumps(x)).rstrip("\n") + "\n")
    sys.stdout.flush()


async def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    op, a = sys.argv[1], sys.argv[2:]
    async with HA() as ha, Dashboard(ha) as db:
        if op == "get":
            r = await db.call("devices/get_config", configuration=a[0])
            out(r if isinstance(r, str) else r.get("content", json.dumps(r)))
        elif op == "put":
            print(await db.call("devices/update_config", configuration=a[0], content=open(a[1]).read()))
        elif op == "validate":
            print("RESULT", await db.call("devices/validate", stream=out, configuration=a[0]))
        elif op == "logs":
            try:
                await db.call("devices/logs", stream=out, timeout=float(a[1]), configuration=a[0], port="OTA")
            except TimeoutError:
                pass  # EN: time is up, as asked · ES: se acabó el tiempo pedido
        elif op == "install":
            job = await db.call("firmware/install", configuration=a[0], port="OTA",
                                force_local=False, bootloader=False)
            print("JOB", job, file=sys.stderr)
            jid = job["job_id"] if isinstance(job, dict) and "job_id" in job else job
            print("RESULT", await db.call("firmware/follow_job", stream=out, job_id=jid))
        elif op == "upload":
            # EN: If it fails halfway (weak USB power -> brownout), just run it again.
            # ES: Si falla a medias (alimentación USB floja -> brownout), vuelve a lanzarlo.
            job = await db.call("firmware/upload", configuration=a[0], port="OTA")
            print("JOB", str(job)[:150], file=sys.stderr)
            print("RESULT", await db.call("firmware/follow_job", stream=out, job_id=job["job_id"]))
        elif op == "raw":
            print(json.dumps(await db.call(a[0], **(json.loads(a[1]) if len(a) > 1 else {})))[:6000])
        else:
            sys.exit(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
