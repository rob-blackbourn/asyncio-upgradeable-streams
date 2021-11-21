import asyncio
from asyncio import (
    StreamReader,
    StreamReaderProtocol,
    StreamWriter,
    BaseTransport,
    BaseProtocol,
    AbstractEventLoop
)
import socket
import warnings
import weakref
from ssl import SSLContext
from typing import Any, Callable, Coroutine, Optional, Tuple


class UpgradableStreamReaderProtocol(StreamReaderProtocol):

    def upgrade_reader(self, reader: StreamReader):
        # if self._stream_reader_wr is not None:
        #     self._stream_reader_wr.set_exception(
        #         Exception('upgraded connection to TLS, this reader is obsolete now.'))
        self._stream_reader_wr = weakref.ref(reader)
        self._source_traceback = reader._source_traceback


class UpgradableStreamWriter(StreamWriter):

    def __init__(
            self,
            transport: BaseTransport,
            protocol: BaseProtocol,
            reader: Optional[StreamReader],
            sslcontext: SSLContext,
            host: str,
            server_side: bool,
            loop: AbstractEventLoop
    ) -> None:
        super().__init__(transport, protocol, reader, loop)
        self.sslcontext = sslcontext
        self.host = host
        self.server_side = server_side

    async def upgrade(self) -> None:
        print("Upgrading " + "server" if self.server_side else "client")
        try:
            transport = await self._loop.start_tls(
                self.transport,
                self.transport.get_protocol(),
                sslcontext=self.sslcontext,
                server_side=self.server_side,
                # server_hostname=self.host
            )
            print("Upgraded")
        except Exception as error:
            print("Failed to upgrade", error)
        reader = StreamReader(limit=2**64, loop=self._loop)
        self._protocol.upgrade_reader(reader)
        self._protocol.connection_made(transport)
        writer = StreamWriter(
            transport,
            self._protocol,
            reader,
            self._loop
        )
        return reader, writer


async def open_upgradable_connection(
    host: str,
    port: int,
    sslcontext: SSLContext
) -> Tuple[StreamReader, UpgradableStreamWriter]:
    loop = asyncio.get_running_loop()
    reader = StreamReader(limit=2**64, loop=loop)
    protocol = UpgradableStreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(
        lambda: protocol, host, port, family=socket.AF_INET
    )
    writer = UpgradableStreamWriter(
        transport,
        protocol,
        reader,
        sslcontext,
        host,
        False,
        loop
    )
    return reader, writer

ClientConnectedCallback = Callable[
    [StreamReader, UpgradableStreamWriter],
    Coroutine[Any, Any, None]
]


async def start_upgradable_server(
    client_connected_cb: ClientConnectedCallback,
    sslcontext: SSLContext,
    host: Optional[str] = None,
    port: Optional[int] = None,
    *,
    loop: Optional[AbstractEventLoop] = None,
    limit: int = 2**16,
    **kwds
):
    if loop is None:
        loop = asyncio.get_event_loop()
    else:
        warnings.warn("The loop argument is deprecated since Python 3.8, "
                      "and scheduled for removal in Python 3.10.",
                      DeprecationWarning, stacklevel=2)

    async def client_callback_wrapper(reader: StreamReader, writer: StreamWriter):
        writer = UpgradableStreamWriter(
            writer.transport,
            writer._protocol,
            reader,
            sslcontext,
            host,
            True,
            loop
        )

        await client_connected_cb(reader, writer)

    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = UpgradableStreamReaderProtocol(
            reader,
            client_callback_wrapper,
            loop=loop
        )
        return protocol

    return await loop.create_server(factory, host, port, **kwds)
