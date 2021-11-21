"""Writer"""

from asyncio import (
    StreamReader,
    StreamWriter,
    BaseTransport,
    BaseProtocol,
    AbstractEventLoop
)
from ssl import SSLContext
from typing import Optional, Tuple, cast

from .protocol import UpgradeableStreamReaderProtocol


class UpgradeableStreamWriter(StreamWriter):

    def __init__(
            self,
            transport: BaseTransport,
            protocol: BaseProtocol,
            reader: Optional[StreamReader],
            sslcontext: SSLContext,
            server_side: bool,
            loop: AbstractEventLoop
    ) -> None:
        super().__init__(transport, protocol, reader, loop)
        self.sslcontext = sslcontext
        self.server_side = server_side

    async def upgrade(self) -> Tuple[StreamReader, StreamWriter]:
        protocol = cast(
            UpgradeableStreamReaderProtocol,
            self.transport.get_protocol()
        )
        loop: AbstractEventLoop = self._loop  # type: ignore
        transport = await loop.start_tls(
            self.transport,
            protocol,
            sslcontext=self.sslcontext,
            server_side=self.server_side,
        )
        reader = StreamReader(limit=2**64, loop=loop)
        protocol.upgrade_reader(reader)
        self._transport = transport
        writer = StreamWriter(
            transport,
            self.transport.get_protocol(),
            reader,
            loop
        )
        return reader, writer
