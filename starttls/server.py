"""Server"""

import asyncio
from asyncio import StreamReader
from os.path import expanduser
import ssl

from starttls.scratch import start_upgradable_server, UpgradableStreamWriter


async def handle_client(reader: StreamReader, writer: UpgradableStreamWriter) -> None:
    print("Client connected")

    while True:
        print("Wating for client request")
        request = (await reader.readline()).decode('utf8').rstrip()
        print(f"Read '{request}'")
        if request == 'quit' or request == '':
            break
        elif request == 'upgrade':
            reader, writer = await writer.upgrade()

    print("Closing client")
    writer.close()
    await writer.wait_closed()
    print("Client closed")


async def run_server():
    print("Starting server")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_verify_locations(cafile="/etc/ssl/certs/ca-certificates.crt")
    ctx.load_cert_chain(
        expanduser("~/.keys/server.crt"),
        expanduser("~/.keys/server.key")
    )
    server = await start_upgradable_server(
        handle_client,
        ctx,
        'beastie.jetblack.net',
        10001
    )
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(run_server())
