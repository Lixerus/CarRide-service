import aio_pika
from aio_pika.abc import AbstractExchange
from random import choice
import asyncio
from os import environ


active_exchanges = dict()
drivers = set()
passangers = set()

async def pairing_corutine():
        if len(passangers) !=0 and len(drivers) !=0:
            passanger = choice(list(passangers))
            passangers.remove(passanger)
            driver = await find_optimal_pair(passanger)
            await send_msg(exchange=active_exchanges['pairingex'], routing_key='order', msg=f'{driver} {passanger}')

async def find_optimal_pair(login : str) -> str:
    driver = choice(list(drivers))
    await asyncio.sleep(1)
    drivers.remove(driver)
    return driver

async def passanger_handler(message: aio_pika.abc.AbstractIncomingMessage,) -> None:
    async with message.process():
        login = message.body.decode()
        print(f"{login} is looking for a driver")
        passangers.add(login)


async def driver_handler(message: aio_pika.abc.AbstractIncomingMessage,) -> None:
    async with message.process():
        login = message.body.decode()
        print(f"{login} is looking for a passenger")
        drivers.add(login)

async def send_msg(exchange : AbstractExchange, routing_key : str, msg : str):
        await exchange.publish(
            aio_pika.Message(body=msg.encode()),
            routing_key=routing_key,
        )

async def setup() -> None:
    print("Pairing is starting")
    rmq_host = environ.get("RMQ", 'localhost')
    connection = await aio_pika.connect_robust(f"amqp://guest:guest@{rmq_host}/",)
    channel = await connection.channel()
    pairingex = await channel.declare_exchange(name = 'pairingex')
    active_exchanges['pairingex'] = pairingex
    driver_queue = await channel.declare_queue(name = 'driver_pair')
    await driver_queue.bind(exchange="pairingex", routing_key='driver_pair')
    # order_queue = await channel.declare_queue(name = 'order')
    # await order_queue.bind(exchange='pairingex', routing_key='order')
    passanger_queue = await channel.declare_queue(name = 'passanger_pair')
    await passanger_queue.bind(exchange="pairingex", routing_key='passanger_pair')

    await channel.set_qos(prefetch_count=10)

    await passanger_queue.consume(passanger_handler)
    await driver_queue.consume(driver_handler)

    try:
        while True:
            await pairing_corutine()
            await asyncio.sleep(1)
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(setup())