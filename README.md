# asyncio-upgradeable-streams

An experiment in upgradeable streams.

## Overview

An upgradeable stream starts life as a plain socket connection, but is capable
of being "upgraded" to TLS. This is sometimes known as [STARTTLS](https://en.wikipedia.org/wiki/Opportunistic_TLS). Common examples of this are
SMTP, LDAP, and HTTP proxy tunneling with CONNECT.

The asyncio library provides [loop.start_tls](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.start_tls) for this purpose.
This project provides an implementation of [asyncio.open_connection](https://docs.python.org/3/library/asyncio-stream.html#asyncio.open_connection)
and [asyncio.start_server](https://docs.python.org/3/library/asyncio-stream.html#asyncio.start_server)
with an extra optional boolean parameter `upgradeadble`. When this is set, the `writer` has a new method `upgrade` which can be called to
upgrade the connection to TLS.

This was tested using Python 3.9.7 on Ubuntu Linux 21.10.

## Issues

The solution makes use of private variables in the python standard library which
may change at the will of the python library maintainer.

# Installation

This can be installed with pip.

```bash
pip install jetblack-upgradeable-streams
```

## Examples

The following examples can be found in the "demos" folder. They expect a Linux
environment.

### Client

Here is the client. A new argument `upgradeable` has been added to the
`open_connection` function, to enable upgrading. The `writer` has a new method
`upgrade` to upgrade the connection.

The client connects without TLS.

First the client sends "PING" to the server. The server should respond
with "PONG".

Next the client sends "STARTTLS" to instruct the server to upgrade the
connection to TLS. The client then calls the `upgrade` method on the `writer` to
negotiate the secure connection. The method returns a new `reader` and `writer`.

Using the new writer the client sends "PING" to the server, this time over the
encrypted stream. The server should respond with "PONG".

Finally the client sends "QUIT" to the server and closes the connection.

```python
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
```

### Server

An extra argument `upgradeable` has been added to the `start_server` function
to enable upgrading to TLS. The `writer` has a new method `upgrade` to upgrade
the connection to TLS.

The server listens for client connections.

On receiving a connection it enters a read loop.

When the server receives "PING" it responds with "PONG".

When the server receives "QUIT" it closes the connection.

When the server receives "STARTTLS" it calls the `upgrade` method on the `writer`
to negotiate the TLS connection. The method returns a new `reader` and `writer`.

The code expects certificate and key PEM files in "~/.keys/server.{crt,key}".

```python
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

        if request == 'QUIT':
            break

        elif request == 'PING':
            print("Sending pong")
            writer.write(b'PONG\n')
            await writer.drain()

        elif request == 'STARTTLS':
            if not isinstance(writer, UpgradeableStreamWriter):
                raise ValueError('writer not upgradeable')
            print("Upgrading connection to TLS")
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
```
