"""Example Server"""

import asyncio
from asyncio import StreamReader, StreamWriter
from os.path import expanduser
import socket
import ssl
from typing import Union

from upgradeable_streams import start_server, UpgradeableStreamWriter


async def handle_client(
        reader: StreamReader,
        writer: Union[UpgradeableStreamWriter, StreamWriter]
) -> None:
    print("Client connected")

    while True:
        request = (await reader.readline()).decode('utf8').rstrip()
        print(f"Read '{request}'")

        if request == 'quit':
            break

        elif request == 'ping':
            print("Sending pong")
            writer.write(b'pong\n')
            await writer.drain()

        elif request == 'upgrade':
            if not isinstance(writer, UpgradeableStreamWriter):
                raise ValueError('writer not upgradeable')
            print("Upgrading")
            # Upgrade
            reader, writer = await writer.upgrade()

    print("Closing client")
    writer.close()
    await writer.wait_closed()
    print("Client closed")


async def run_server():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_verify_locations(cafile="/etc/ssl/certs/ca-certificates.crt")
    ctx.load_cert_chain(
        expanduser("~/.keys/server.crt"),
        expanduser("~/.keys/server.key")
    )
    host = socket.getfqdn()

    print("Starting server as upgradeable")
    server = await start_server(
        handle_client,
        host,
        10001,
        ssl=ctx,
        upgradeable=True
    )

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(run_server())
