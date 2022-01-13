"""Server"""

import asyncio
from asyncio import (
    StreamReader,
    StreamWriter,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Awaitable, Callable, Optional
import warnings

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
        # Without the upgradeable flag use the standard library implementation.
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
    else:
        warnings.warn("The loop argument is deprecated since Python 3.8, "
                      "and scheduled for removal in Python 3.10.",
                      DeprecationWarning, stacklevel=2)

    async def client_connected_cb_shim(
            reader: StreamReader,
            writer: StreamWriter
    ) -> None:
        # Shim the client callback to replace the writer with the upgradeable
        # implementation.
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

        # Now call the client callback.
        future = client_connected_cb(reader, writer)
        if future is not None:
            await future

    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = UpgradeableStreamReaderProtocol(
            reader,
            client_connected_cb_shim,
            loop=loop
        )
        return protocol

    return await loop.create_server(factory, host, port, **kwargs)
