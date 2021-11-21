"""Client"""

import asyncio
from asyncio import (
    StreamReader,
    StreamWriter,
    AbstractEventLoop
)
import socket
from ssl import SSLContext
from typing import Optional, Tuple

from .protocol import UpgradeableStreamReaderProtocol
from .writer import UpgradeableStreamWriter


async def open_connection(
    host: str,
    port: int,
    *,
    upgradeable: bool = False,
    ssl: Optional[SSLContext] = None,
    loop: Optional[AbstractEventLoop] = None,
    **kwargs
) -> Tuple[StreamReader, StreamWriter]:
    if not upgradeable:
        return await asyncio.open_connection(
            host,
            port,
            ssl=ssl,
            loop=loop,
            **kwargs
        )

    if ssl is None:
        raise ValueError('upgradeable not valid without ssl')

    if loop is None:
        loop = asyncio.get_running_loop()

    reader = StreamReader(limit=2**64, loop=loop)
    protocol = UpgradeableStreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(
        lambda: protocol, host, port, family=socket.AF_INET
    )
    writer = UpgradeableStreamWriter(
        transport,
        protocol,
        reader,
        ssl,
        False,
        loop
    )
    return reader, writer
