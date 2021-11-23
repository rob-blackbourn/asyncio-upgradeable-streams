"""
Example Client

The client connects without TLS.

First the client sends "PING" to the server. The server should respond
with "PONG".

Next the client sends "STARTTLS" to instruct the server to upgrade the
connection to TLS. The client then calls the upgrade method on the writer to
negotiate the upgrade. The upgrade method returns a new reader and writer.

Using the new writer the client sends "PING" to the server, this time over the
encrypted stream. The server should respond with "PONG".

Finally the client sends "QUIT" to the server and closes the connection.
"""

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

    print("Sending PING")
    writer.write(b'PING\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    print("Sending STARTTLS")
    writer.write(b'STARTTLS\n')

    print("Upgrading the connection")
    # Upgrade
    reader, writer = await writer.upgrade()

    print(f"The writer ssl context is {writer.get_extra_info('sslcontext')}")

    print("Sending PING")
    writer.write(b'PING\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    print("Sending QUIT")
    writer.write(b'QUIT\n')
    await writer.drain()

    print("Closing client")
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")

if __name__ == '__main__':
    asyncio.run(start_client())
