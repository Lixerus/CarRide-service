import aio_pika
from aio_pika.abc import AbstractExchange
import websockets
from os import environ

active_exchanges = dict()
connected = dict()
db = dict()
pairs = dict()

async def ws_server_handler(websocket):
    try:
        while True:
            data : str = await websocket.recv()
            login, state = data.split(' ')
            connected[login] = websocket
            db[login] = state
            if state == 'waiting':
                await send_msg(exchange=active_exchanges['pairingex'], routing_key="passanger_pair", msg=login)
            elif state == 'cancelled':
                driver_login = pairs.get(login, None)
                if driver_login != None:
                    db[login] = 'idle'
                    pairs[login] = None
                    await send_msg(exchange=active_exchanges['customerex'], routing_key='driver', msg=f'{login} {driver_login} {state}')
    except websockets.ConnectionClosedOK or websockets.ConnectionClosed:
        await websocket.close()
    except websockets.ConnectionClosedError:
        print("Internal Server Error.")

async def message_handler(message: aio_pika.abc.AbstractIncomingMessage,) -> None:
    async with message.process():
        driver_login, passanger_login, status = message.body.decode().split(' ')
        if status == 'accepted':
            try:
                if db[passanger_login] != 'waiting':
                    await send_msg(exchange=active_exchanges['customerex'], routing_key='driver', msg=f'{passanger_login} {driver_login} cancelled')
                else:
                    ws = connected[passanger_login]
                    pairs[passanger_login] = driver_login
                    db[passanger_login] = 'paired'
                    await ws.send(f'{driver_login} {passanger_login} {status}')
            except KeyError:
                print(f"No state available for {passanger_login}")
        elif status == 'cancelled':
            try:
                if db[passanger_login] == 'paired':
                    ws = connected[passanger_login]
                    pairs[passanger_login] = None
                    db[passanger_login] = 'idle'
                    await ws.send(f'{driver_login} {passanger_login} {status}')
                elif db[passanger_login] == 'waiting':
                    await send_msg(exchange=active_exchanges['pairingex'], routing_key='passanger_pair', msg=passanger_login)
            except KeyError:
                print(f"No state available for {passanger_login}")

async def send_msg(exchange : AbstractExchange, routing_key : str, msg : str):
        await exchange.publish(
            aio_pika.Message(body=msg.encode()),
            routing_key=routing_key,
        )

async def setup() -> None:
    rmq_host = environ.get("RMQ", 'localhost')
    connection = await aio_pika.connect_robust(f"amqp://guest:guest@{rmq_host}/",)
    channel = await connection.channel()
    pairingex = await channel.declare_exchange(name = 'pairingex')
    active_exchanges['pairingex'] = pairingex
    customerex = await channel.declare_exchange(name = 'customerex')
    active_exchanges['customerex'] = customerex
    passanger_queue = await channel.declare_queue(name = 'passanger')
    await passanger_queue.bind(exchange="customerex", routing_key='passanger')

    await channel.set_qos(prefetch_count=10)

    await passanger_queue.consume(message_handler)