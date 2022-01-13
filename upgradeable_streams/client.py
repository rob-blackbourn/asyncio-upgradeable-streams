"""Client"""

import asyncio
from asyncio import (
    StreamReader,
    StreamWriter,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Optional, Tuple
import warnings

from .protocol import UpgradeableStreamReaderProtocol
from .writer import UpgradeableStreamWriter


async def open_connection(
    host: str,
    port: int,
    *,
    loop: Optional[AbstractEventLoop] = None,
    upgradeable: bool = False,
    ssl: Optional[SSLContext] = None,
    limit: int = 2**16,
    **kwds
) -> Tuple[StreamReader, StreamWriter]:
    if not upgradeable:
        # Without the upgradeable flag use the standard library implementation.
        return await asyncio.open_connection(
            host,
            port,
            ssl=ssl,
            limit=limit,
            loop=loop,
            **kwds
        )

    if ssl is None:
        raise ValueError('upgradeable not valid without ssl')

    if loop is None:
        loop = asyncio.get_running_loop()
    else:
        warnings.warn("The loop argument is deprecated since Python 3.8, "
                      "and scheduled for removal in Python 3.10.",
                      DeprecationWarning, stacklevel=2)

    reader = StreamReader(limit=limit, loop=loop)
    protocol = UpgradeableStreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(
        lambda: protocol, host, port, **kwds)

    # Replace the writer with the upgradeable implementation.
    writer = UpgradeableStreamWriter(
        transport,
        protocol,
        reader,
        loop,
        ssl,
        False,
        limit
    )

    return reader, writer
