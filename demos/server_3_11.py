"""
Example Server

The server listens for client connections.

On receiving a connection it enters a read loop.

When the server receives "PING" it responds with "PONG".

When the server receives "QUIT" it closes the connection.

When the server receives "STARTTLS" it calls the upgrade method on the writer
to negotiate the TLS connection. The method returns a new reader and writer.
"""

import asyncio
from asyncio import StreamReader, StreamWriter
from functools import partial
from os.path import expanduser
import socket
import ssl


async def handle_client(
        ctx: ssl.SSLContext,
        reader: StreamReader,
        writer: StreamWriter
) -> None:
    print("Client connected")

    while True:
        request = (await reader.readline()).decode('utf8').rstrip()
        print(f"Read '{request}'")

        if request == 'QUIT':
            break

        elif request == 'PING':
            print("Sending pong")
            writer.write(b'PONG\n')
            await writer.drain()

        elif request == 'STARTTLS':
            print("Upgrading connection to TLS")
            # Upgrade
            await writer.start_tls(ctx)

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
    server = await asyncio.start_server(partial(handle_client, ctx), host, 10001)

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(run_server())
