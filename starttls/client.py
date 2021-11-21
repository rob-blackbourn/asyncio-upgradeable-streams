"""Client"""

import asyncio
import ssl

from starttls.scratch import open_connection


async def start_client():
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile='/etc/ssl/certs/ca-certificates.crt'
    )

    reader, writer = await open_connection(
        "beastie.jetblack.net",
        10001,
        ssl=ctx,
        upgradeable=True
    )
    print("Client connected")

    print("Sending ping")
    writer.write(b'ping\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    writer.write(b'upgrade\n')
    reader, writer = await writer.upgrade()

    print("Sending ping")
    writer.write(b'ping\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    print("Sending quit")
    writer.write(b'quit\n')
    await writer.drain()

    print("Closing client")
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")

if __name__ == '__main__':
    asyncio.run(start_client())
