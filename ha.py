"""Helper: push pantalla.yaml to the ESPHome Device Builder add-on of Home Assistant and flash it over Wi-Fi.

Usage (needs aiohttp, e.g. `uv run --with aiohttp python ha.py <op> ...`):
  get pantalla.yaml                 print the config stored in the add-on
  put pantalla.yaml ./pantalla.yaml upload the local config to the add-on
  validate pantalla.yaml
  install pantalla.yaml             compile in the add-on and upload over the air
  upload pantalla.yaml              upload the already compiled firmware
  logs pantalla.yaml 60             follow the device log for 60 s
"""
import asyncio, json, os, sys, aiohttp

HOST = "http://192.168.1.101:8123"
TOKEN = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")).read().strip()


class HA:
    async def __aenter__(self):
        self.s = aiohttp.ClientSession()
        self.ws = await self.s.ws_connect(HOST + "/api/websocket", max_msg_size=0)
        await self.ws.receive_json()
        await self.ws.send_json({"type": "auth", "access_token": TOKEN})
        r = await self.ws.receive_json()
        assert r["type"] == "auth_ok", r
        self.i = 0
        return self

    async def __aexit__(self, *a):
        await self.ws.close()
        await self.s.close()

    async def cmd(self, **kw):
        self.i += 1
        await self.ws.send_json({"id": self.i, **kw})
        while True:
            r = await self.ws.receive_json()
            if r.get("id") == self.i and r.get("type") == "result":
                return r

    async def sup(self, endpoint, method="get", data=None):
        kw = dict(type="supervisor/api", endpoint=endpoint, method=method)
        if data is not None:
            kw["data"] = data
        return await self.cmd(**kw)

    async def esphome(self):
        """Return (base_url, slug) of the ESPHome dashboard ingress."""
        r = await self.sup("/addons")
        addons = r["result"]["addons"]
        slug = next(a["slug"] for a in addons if "esphome" in a["slug"])
        info = (await self.sup(f"/addons/{slug}/info"))["result"]
        sess = (await self.sup("/ingress/session", "post"))["result"]["session"]
        self.s.cookie_jar.update_cookies({"ingress_session": sess})
        return HOST + info["ingress_url"].rstrip("/"), slug


class DB:
    """ESPHome Device Builder websocket client."""
    def __init__(self, ha): self.ha = ha; self.n = 0
    async def __aenter__(self):
        base, _ = await self.ha.esphome()
        self.w = await self.ha.s.ws_connect(base.replace("http", "ws", 1) + "/ws", max_msg_size=0)
        self.info = await self.w.receive_json()
        return self
    async def __aexit__(self, *a): await self.w.close()
    async def call(self, command, stream=None, timeout=1500, **args):
        self.n += 1; mid = self.n
        await self.w.send_json({"command": command, "message_id": mid, "args": args})
        async with asyncio.timeout(timeout):
            while True:
                m = await self.w.receive()
                if m.type != aiohttp.WSMsgType.TEXT:
                    raise RuntimeError(f"ws closed: {m}")
                d = json.loads(m.data)
                if str(d.get("message_id")) != str(mid): continue
                if "error_code" in d: raise RuntimeError(f"{d['error_code']}: {d.get('details')}")
                if "event" in d:
                    if d["event"] == "output" and stream: stream(d["data"])
                    elif d["event"] == "result": return d["data"]
                    continue
                if "result" in d: return d["result"]


def out(x):
    sys.stdout.write((x if isinstance(x, str) else json.dumps(x)).rstrip("\n") + "\n"); sys.stdout.flush()


async def main():
    op, a = sys.argv[1], sys.argv[2:]
    async with HA() as ha, DB(ha) as db:
        if op == "get":
            r = await db.call("devices/get_config", configuration=a[0])
            out(r if isinstance(r, str) else r.get("content", json.dumps(r)))
        elif op == "put":
            print(await db.call("devices/update_config", configuration=a[0], content=open(a[1]).read()))
        elif op == "validate":
            print("RESULT", await db.call("devices/validate", stream=out, configuration=a[0]))
        elif op == "logs":
            try: await db.call("devices/logs", stream=out, timeout=float(a[1]), configuration=a[0], port="OTA")
            except TimeoutError: pass
        elif op == "install":
            job = await db.call("firmware/install", configuration=a[0], port="OTA", force_local=False, bootloader=False)
            print("JOB", job, file=sys.stderr)
            jid = job["job_id"] if isinstance(job, dict) and "job_id" in job else job
            print("RESULT", await db.call("firmware/follow_job", stream=out, job_id=jid))
        elif op == "upload":
            job = await db.call("firmware/upload", configuration=a[0], port="OTA")
            print("JOB", str(job)[:150], file=sys.stderr)
            print("RESULT", await db.call("firmware/follow_job", stream=out, job_id=job["job_id"]))
        elif op == "raw":
            print(json.dumps(await db.call(a[0], **(json.loads(a[1]) if len(a) > 1 else {})))[:6000])


if __name__ == "__main__":
    asyncio.run(main())
