"""Client"""

import asyncio
import ssl

from starttls.scratch import open_upgradable_connection


async def start_client():
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile='/etc/ssl/certs/ca-certificates.crt'
    )

    reader, writer = await open_upgradable_connection(
        "beastie.jetblack.net",
        10001,
        ctx
    )
    print("Client connected")

    writer.write(b'upgrade\n')
    reader, writer = await writer.upgrade()

    writer.write(b'quit\n')
    await writer.drain()
    print("Closing client")
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")

if __name__ == '__main__':
    asyncio.run(start_client())
