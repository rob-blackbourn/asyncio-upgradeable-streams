"""Protocol"""

from asyncio import StreamReader, StreamReaderProtocol
import weakref


class UpgradeableStreamReaderProtocol(StreamReaderProtocol):

    def set_reader(self, reader: StreamReader):
        if self._stream_reader is not None:  # type: ignore
            self._stream_reader.set_exception(  # type: ignore
                Exception('connection upgraded.')
            )
        self._stream_reader_wr = weakref.ref(reader)
        self._source_traceback = reader._source_traceback  # type: ignore
