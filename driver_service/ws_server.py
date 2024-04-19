import websockets
import asyncio
import setup_driver_server
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.INFO,
)

class LoggerAdapter(logging.LoggerAdapter):
    """Add connection ID and client IP address to websockets logs."""
    def process(self, msg, kwargs):
        try:
            websocket = kwargs["extra"]["websocket"]
        except KeyError:
            return msg, kwargs
        xff = websocket.request_headers.get("X-Forwarded-For")
        return f"{websocket.id} {xff} {msg}", kwargs

STATES = ['idle', 'waiting', 'paired']

async def main():
    print("Driver service starting")
    async with websockets.serve(setup_driver_server.ws_server_handler, host="0.0.0.0", port=7880, logger=LoggerAdapter(logging.getLogger("websockets.server"))):
        await setup_driver_server.setup()
        await asyncio.Future()
 
if __name__ == "__main__":
    asyncio.run(main())