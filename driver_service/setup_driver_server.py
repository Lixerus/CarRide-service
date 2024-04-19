import aio_pika
import websockets
from aio_pika.abc import AbstractExchange
from os import environ

connected = dict()
db = dict()
pairs = dict()
active_exchanges = dict()

async def ws_server_handler(websocket):
    try:
        while True:
            data : str = await websocket.recv()
            login, state = data.split(' ')
            connected[login] = websocket
            db[login] =state
            if state == 'waiting':
                await send_msg(exchange=active_exchanges['pairingex'], routing_key="driver_pair", msg=login)
            elif state == 'cancelled':
                passanger_login = pairs.get(login, None)
                db[login] = 'idle'
                if passanger_login != None:
                    pairs[login] = None
                    await send_msg(exchange=active_exchanges['customerex'], routing_key='passanger', msg=f'{login} {passanger_login} {state}')
            elif state == 'accepted':
                db[login] = 'paired'
                passanger_login = pairs[login]
                await send_msg(exchange=active_exchanges['customerex'], routing_key='passanger', msg=f'{login} {passanger_login} {state}')
            
    except websockets.ConnectionClosedOK or websockets.ConnectionClosed:
        #connected.pop(login)
        await websocket.close()
    except websockets.ConnectionClosedError:
        print("Internal Server Error.")


async def message_handler(message: aio_pika.abc.AbstractIncomingMessage,) -> None:
    async with message.process():
        passanger_login, driver_login, status = message.body.decode().split(' ')
        if status == 'cancelled':
            try:
                ws = connected[driver_login]
                if db[driver_login] == 'paired':
                    db[driver_login] == 'idle'
                    pairs[driver_login] == None
                    await ws.send(f'{driver_login} {passanger_login} cancelled')
            except KeyError:
                print(f"No state availabel for {driver_login}")

async def order_handler(message: aio_pika.abc.AbstractIncomingMessage,) -> None:
    async with message.process():
        driver_login, passanger_login = message.body.decode().split(' ')
        if db[driver_login] != 'waiting':
            await send_msg(exchange=active_exchanges['customerex'], routing_key='passangers', msg=f"{driver_login} {passanger_login} cancelled")
        else:
            ws = connected.get(driver_login)
            pairs[driver_login] = passanger_login
            if ws != None:
                await ws.send(f"{driver_login} {passanger_login} order")

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
    driver_queue = await channel.declare_queue(name = 'driver')
    await driver_queue.bind(exchange="customerex", routing_key='driver')
    order_queue = await channel.declare_queue(name = 'order')
    await order_queue.bind(exchange='pairingex', routing_key='order')

    await channel.set_qos(prefetch_count=10)

    await driver_queue.consume(message_handler)
    await order_queue.consume(order_handler)