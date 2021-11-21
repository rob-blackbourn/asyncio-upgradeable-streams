"""Example Client"""

import asyncio
import socket
import ssl

from upgradeable_streams import open_connection


async def start_client():
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile='/etc/ssl/certs/ca-certificates.crt'
    )
    host = socket.getfqdn()

    print("Connect to server as upgradeable")
    reader, writer = await open_connection(
        host,
        10001,
        ssl=ctx,
        upgradeable=True
    )

    print(f"The writer ssl context is {writer.get_extra_info('sslcontext')}")

    print("Sending ping")
    writer.write(b'ping\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    print("Sending upgrade")
    writer.write(b'upgrade\n')

    print("Upgrading the connection")
    # Upgrade
    reader, writer = await writer.upgrade()

    print(f"The writer ssl context is {writer.get_extra_info('sslcontext')}")

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
