"""Server"""

import asyncio
from asyncio import (
    StreamReader,
    StreamWriter,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Any, Callable, Coroutine, Optional

from .protocol import UpgradeableStreamReaderProtocol
from .writer import UpgradeableStreamWriter


ClientConnectedCallback = Callable[
    [StreamReader, UpgradeableStreamWriter],
    Coroutine[Any, Any, None]
]


async def start_server(
    client_connected_cb: ClientConnectedCallback,
    host: Optional[str] = None,
    port: Optional[int] = None,
    *,
    upgradeable: bool = False,
    ssl: Optional[SSLContext] = None,
    loop: Optional[AbstractEventLoop] = None,
    limit: int = 2**16,
    **kwargs
):
    if not upgradeable:
        return await start_server(
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
        loop = asyncio.get_event_loop()

    async def client_callback_wrapper(reader: StreamReader, writer: StreamWriter):
        writer = UpgradeableStreamWriter(
            writer.transport,
            writer.transport.get_protocol(),
            reader,
            ssl,
            True,
            loop
        )

        await client_connected_cb(reader, writer)

    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = UpgradeableStreamReaderProtocol(
            reader,
            client_callback_wrapper,
            loop=loop
        )
        return protocol

    return await loop.create_server(factory, host, port, **kwargs)
