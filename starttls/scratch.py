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
from typing import Any, Callable, Coroutine, Optional, Tuple, cast


class UpgradableStreamReaderProtocol(StreamReaderProtocol):

    def upgrade_reader(self, reader: StreamReader):
        if self._stream_reader is not None:  # type: ignore
            self._stream_reader.set_exception(  # type: ignore
                Exception('connection upgraded.')
            )
        self._stream_reader_wr = weakref.ref(reader)
        self._source_traceback = reader._source_traceback  # type: ignore


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

    async def upgrade(self) -> Tuple[StreamReader, StreamWriter]:
        print("Upgrading " + "server" if self.server_side else "client")
        protocol = cast(
            UpgradableStreamReaderProtocol,
            self.transport.get_protocol()
        )
        loop: AbstractEventLoop = self._loop  # type: ignore
        transport = await loop.start_tls(
            self.transport,
            protocol,
            sslcontext=self.sslcontext,
            server_side=self.server_side,
            # server_hostname=self.host
        )
        print("Upgraded")
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


async def open_connection(
    host: str,
    port: int,
    *,
    upgradeable: bool = False,
    ssl: Optional[SSLContext] = None,
    loop: Optional[AbstractEventLoop] = None,
    **kwargs
) -> Tuple[StreamReader, StreamWriter]:
    if loop is None:
        loop = asyncio.get_running_loop()

    if not upgradeable:
        return await asyncio.open_connection(host, port, ssl=ssl, loop=loop, **kwargs)

    if ssl is None:
        raise ValueError('upgradeable not valid without ssl')

    reader = StreamReader(limit=2**64, loop=loop)
    protocol = UpgradableStreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(
        lambda: protocol, host, port, family=socket.AF_INET
    )
    writer = UpgradableStreamWriter(
        transport,
        protocol,
        reader,
        ssl,
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
