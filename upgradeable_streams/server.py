"""Server"""

import asyncio
from asyncio import (
    StreamReader,
    StreamWriter,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Awaitable, Callable, Optional

from .protocol import UpgradeableStreamReaderProtocol
from .writer import UpgradeableStreamWriter

ClientConnectedCallback = Callable[
    [StreamReader, StreamWriter],
    Awaitable[None]
]


async def start_server(
    client_connected_cb: ClientConnectedCallback,
    host: str,
    port: int,
    *,
    upgradeable: bool = False,
    ssl: Optional[SSLContext] = None,
    loop: Optional[AbstractEventLoop] = None,
    limit: int = 2**16,
    **kwargs
):
    if not upgradeable:
        return await asyncio.start_server(
            client_connected_cb,
            host,
            port,
            ssl=ssl,
            loop=loop,
            limit=limit,
            **kwargs
        )

    if ssl is None:
        raise ValueError('upgradeable not valid without ssl')

    if loop is None:
        loop = asyncio.get_running_loop()

    async def client_callback_wrapper(reader: StreamReader, writer: StreamWriter):
        assert loop is not None
        assert ssl is not None
        writer = UpgradeableStreamWriter(
            writer.transport,
            writer.transport.get_protocol(),
            reader,
            loop,
            ssl,
            True,
            limit
        )

        future = client_connected_cb(reader, writer)
        if future is not None:
            await future

    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = UpgradeableStreamReaderProtocol(
            reader,
            client_callback_wrapper,
            loop=loop
        )
        return protocol

    return await loop.create_server(factory, host, port, **kwargs)
