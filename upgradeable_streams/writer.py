"""Writer"""

from asyncio import (
    StreamReader,
    StreamWriter,
    BaseTransport,
    BaseProtocol,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Optional, Tuple

from .protocol import UpgradeableStreamReaderProtocol


class UpgradeableStreamWriter(StreamWriter):

    def __init__(
            self,
            transport: BaseTransport,
            protocol: BaseProtocol,
            reader: Optional[StreamReader],
            loop: AbstractEventLoop,
            sslcontext: SSLContext,
            server_side: bool,
            limit: int
    ) -> None:
        super().__init__(transport, protocol, reader, loop)
        self._sslcontext = sslcontext
        self._server_side = server_side
        self._limit = limit

    async def start_tls(self) -> Tuple[StreamReader, StreamWriter]:
        protocol = self.transport.get_protocol()
        if not isinstance(protocol, UpgradeableStreamReaderProtocol):
            raise ValueError(
                "protocol must be UpgradeableStreamReaderProtocol"
            )
        loop: AbstractEventLoop = self._loop  # type: ignore
        transport = await loop.start_tls(
            self.transport,
            protocol,
            sslcontext=self._sslcontext,
            server_side=self._server_side,
        )
        reader = StreamReader(limit=self._limit, loop=loop)
        protocol.set_reader(reader)
        self._transport = transport
        writer = StreamWriter(
            transport,
            self.transport.get_protocol(),
            reader,
            loop
        )
        return reader, writer
