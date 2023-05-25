"""
Example Client

The client connects without TLS, but using the fully qualified domain name. To
authenticate the server, the FQDN is required. This can be specified either at
connection time, or with the start_tls call.

First the client sends a "PING" over the unencrypted stream  to the server. The
server should respond with "PONG".

Next the client sends "STARTTLS" to instruct the server to upgrade the
connection to TLS. The client then calls the upgrade method on the writer to
negotiate the upgrade.

The client sends "PING" to the server, this time over the encrypted stream. The
server should respond with "PONG".

Finally the client sends "QUIT" to the server and closes the connection.
"""

import asyncio
import socket
import ssl


async def start_client():

    print("Connect to the server with using the fully qualified domain name")
    reader, writer = await asyncio.open_connection(socket.getfqdn(), 10001)

    print(f"The writer ssl context is {writer.get_extra_info('sslcontext')}")

    print("Sending PING")
    writer.write(b'PING\n')
    response = (await reader.readline()).decode('utf-8').rstrip()
    print(f"Received: {response}")

    print("Sending STARTTLS")
    writer.write(b'STARTTLS\n')

    print("Upgrade the connection to TLS")
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile='/etc/ssl/certs/ca-certificates.crt'
    )
    await writer.start_tls(ctx)

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
