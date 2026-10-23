import asyncio

from backend.config.settings import PROCESS_INTERVAL
from backend.state import latest_results, ws_clients


async def broadcaster():
    while True:
        for vid_id, result in list(latest_results.items()):
            dead = []
            for ws in ws_clients.get(vid_id, []):
                try:
                    await ws.send_json(result)
                except:
                    dead.append(ws)
            for ws in dead:
                ws_clients[vid_id].remove(ws)
        await asyncio.sleep(PROCESS_INTERVAL)
