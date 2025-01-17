from __future__ import with_statement

from rpython.tool.udir import udir


class AppTestIoModule:
    spaceconfig = dict(usemodules=['_io'])

    def test_import(self):
        import io

    def test_iobase(self):
        import io
        io.IOBase()

        class MyFile(io.BufferedIOBase):
            def __init__(self, filename):
                pass
        MyFile("file")

    def test_openclose(self):
        import io
        with io.BufferedIOBase() as f:
            assert not f.closed
            f._checkClosed()
        assert f.closed
        raises(ValueError, f._checkClosed)

    def test_iter(self):
        import io
        class MyFile(io.IOBase):
            def __init__(self):
                self.lineno = 0
            def readline(self):
                self.lineno += 1
                if self.lineno == 1:
                    return "line1"
                elif self.lineno == 2:
                    return "line2"
                return ""

        assert list(MyFile()) == ["line1", "line2"]

    def test_exception(self):
        import _io
        e = _io.UnsupportedOperation("seek")

    def test_default_implementations(self):
        import _io
        file = _io._IOBase()
        raises(_io.UnsupportedOperation, file.seek, 0, 1)
        raises(_io.UnsupportedOperation, file.fileno)
        raises(_io.UnsupportedOperation, file.truncate)

    def test_blockingerror(self):
        import _io
        try:
            raise _io.BlockingIOError(42, "test blocking", 123)
        except IOError as e:
            assert isinstance(e, _io.BlockingIOError)
            assert e.errno == 42
            assert e.strerror == "test blocking"
            assert e.characters_written == 123

    def test_dict(self):
        import _io
        f = _io.BytesIO()
        f.x = 42
        assert f.x == 42
        #
        def write(data):
            try:
                data = data.tobytes().upper()
            except AttributeError:
                data = data.upper()
            return _io.BytesIO.write(f, data)
        f.write = write
        bufio = _io.BufferedWriter(f)
        bufio.write("abc")
        bufio.flush()
        assert f.getvalue() == "ABC"

    def test_destructor(self):
        import io
        io.IOBase()

        record = []
        class MyIO(io.IOBase):
            def __del__(self):
                record.append(1)
            def close(self):
                record.append(2)
                super(MyIO, self).close()
            def flush(self):
                record.append(3)
                super(MyIO, self).flush()
        MyIO()
        import gc; gc.collect()
        assert record == [1, 2, 3]

    def test_tell(self):
        import io
        class MyIO(io.IOBase):
            def seek(self, pos, whence=0):
                return 42
        assert MyIO().tell() == 42

    def test_weakref(self):
        import _io
        import weakref
        f = _io.BytesIO()
        ref = weakref.ref(f)
        assert ref() is f

    def test_rawio_read(self):
        import _io
        class MockRawIO(_io._RawIOBase):
            stack = ['abc', 'de', '']
            def readinto(self, buf):
                data = self.stack.pop(0)
                buf[:len(data)] = data
                return len(data)
        assert MockRawIO().read() == 'abcde'

    def test_rawio_read_pieces(self):
        import _io
        class MockRawIO(_io._RawIOBase):
            stack = ['abc', 'de', None, 'fg', '']
            def readinto(self, buf):
                data = self.stack.pop(0)
                if data is None:
                    return None
                if len(data) <= len(buf):
                    buf[:len(data)] = data
                    return len(data)
                else:
                    buf[:] = data[:len(buf)]
                    self.stack.insert(0, data[len(buf):])
                    return len(buf)
        r = MockRawIO()
        assert r.read(2) == 'ab'
        assert r.read(2) == 'c'
        assert r.read(2) == 'de'
        assert r.read(2) is None
        assert r.read(2) == 'fg'
        assert r.read(2) == ''

    def test_rawio_readall_none(self):
        import _io
        class MockRawIO(_io._RawIOBase):
            read_stack = [None, None, "a"]
            def readinto(self, buf):
                v = self.read_stack.pop()
                if v is None:
                    return v
                buf[:len(v)] = v
                return len(v)

        r = MockRawIO()
        s = r.readall()
        assert s =="a"
        s = r.readall()
        assert s is None

class AppTestOpen:
    spaceconfig = dict(usemodules=['_io', '_locale', 'array', 'struct'])

    def setup_class(cls):
        tmpfile = udir.join('tmpfile').ensure()
        cls.w_tmpfile = cls.space.wrap(str(tmpfile))

    def test_open(self):
        import io
        f = io.open(self.tmpfile, "rb")
        assert f.name.endswith('tmpfile')
        assert f.mode == 'rb'
        f.close()

        with io.open(self.tmpfile, "rt") as f:
            assert f.mode == "rt"

    # Not supported: append
    #def test_open_writable(self):
    #    import io
    #    f = io.open(self.tmpfile, "w+b")
    #    f.close()

    def test_valid_mode(self):
        import io

        raises(ValueError, io.open, self.tmpfile, "ww")
        raises(ValueError, io.open, self.tmpfile, "rwa")
        raises(ValueError, io.open, self.tmpfile, "b", newline="\n")

    def test_array_write(self):
        import _io, array
        a = array.array(b'i', range(10))
        n = len(a.tostring())
        with _io.open(self.tmpfile, "wb", 0) as f:
            res = f.write(a)
            assert res == n

        with _io.open(self.tmpfile, "wb") as f:
            res = f.write(a)
            assert res == n

    def test_attributes(self):
        import _io

        with _io.open(self.tmpfile, "wb", buffering=0) as f:
            assert f.mode == "wb"

        with _io.open(self.tmpfile, "U") as f:
            assert f.name == self.tmpfile
            assert f.buffer.name == self.tmpfile
            assert f.buffer.raw.name == self.tmpfile
            assert f.mode == "U"
            assert f.buffer.mode == "rb"
            assert f.buffer.raw.mode == "rb"

        # Not supported: append
        #with _io.open(self.tmpfile, "w+") as f:
        #    assert f.mode == "w+"
        #    assert f.buffer.mode == "rb+"
        #    assert f.buffer.raw.mode == "rb+"

        #    with _io.open(f.fileno(), "wb", closefd=False) as g:
        #        assert g.mode == "wb"
        #        assert g.raw.mode == "wb"
        #        assert g.name == f.fileno()
        #        assert g.raw.name == f.fileno()

    # Not supported: seek, tell
    #def test_seek_and_tell(self):
    #    import _io

    #    with _io.open(self.tmpfile, "wb") as f:
    #        f.write("abcd")

    #    with _io.open(self.tmpfile) as f:
    #        decoded = f.read()

    #    # seek positions
    #    for i in xrange(len(decoded) + 1):
    #        # read lenghts
    #        for j in [1, 5, len(decoded) - i]:
    #            with _io.open(self.tmpfile) as f:
    #                res = f.read(i)
    #                assert res == decoded[:i]
    #                cookie = f.tell()
    #                res = f.read(j)
    #                assert res == decoded[i:i + j]
    #                f.seek(cookie)
    #                res = f.read()
    #                assert res == decoded[i:]

    # Not supported:
    #def test_telling(self):
    #    import _io

    #    with _io.open(self.tmpfile, "w+", encoding="utf8") as f:
    #        p0 = f.tell()
    #        f.write(u"\xff\n")
    #        p1 = f.tell()
    #        f.write(u"\xff\n")
    #        p2 = f.tell()
    #        f.seek(0)

    #        assert f.tell() == p0
    #        res = f.readline()
    #        assert res == u"\xff\n"
    #        assert f.tell() == p1
    #        res = f.readline()
    #        assert res == u"\xff\n"
    #        assert f.tell() == p2
    #        f.seek(0)

    #        for line in f:
    #            assert line == u"\xff\n"
    #            raises(IOError, f.tell)
    #        assert f.tell() == p2

    def test_chunk_size(self):
        import _io

        with _io.open(self.tmpfile) as f:
            assert f._CHUNK_SIZE >= 1
            f._CHUNK_SIZE = 4096
            assert f._CHUNK_SIZE == 4096
            raises(ValueError, setattr, f, "_CHUNK_SIZE", 0)

    # Not supported: append
    #def test_truncate(self):
    #    import _io

    #    with _io.open(self.tmpfile, "w+") as f:
    #        f.write(u"abc")

    #    with _io.open(self.tmpfile, "w+") as f:
    #        f.truncate()

    #    with _io.open(self.tmpfile, "r+") as f:
    #        res = f.read()
    #        assert res == ""

    def test_errors_property(self):
        import _io

        with _io.open(self.tmpfile, "w") as f:
            assert f.errors == "strict"
        with _io.open(self.tmpfile, "w", errors="replace") as f:
            assert f.errors == "replace"

    # Not supported: append
    #def test_append_bom(self):
    #    import _io

    #    # The BOM is not written again when appending to a non-empty file
    #    for charset in ["utf-8-sig", "utf-16", "utf-32"]:
    #        with _io.open(self.tmpfile, "w", encoding=charset) as f:
    #            f.write(u"aaa")
    #            pos = f.tell()
    #        with _io.open(self.tmpfile, "rb") as f:
    #            res = f.read()
    #            assert res == "aaa".encode(charset)
    #        with _io.open(self.tmpfile, "a", encoding=charset) as f:
    #            f.write(u"xxx")
    #        with _io.open(self.tmpfile, "rb") as f:
    #            res = f.read()
    #            assert res == "aaaxxx".encode(charset)

    def test_newlines_attr(self):
        import _io

        with _io.open(self.tmpfile, "r") as f:
            assert f.newlines is None

        with _io.open(self.tmpfile, "wb") as f:
            f.write("hello\nworld\n")

        with _io.open(self.tmpfile, "r") as f:
            res = f.readline()
            assert res == "hello\n"
            res = f.readline()
            assert res == "world\n"
            assert f.newlines == "\n"
            assert type(f.newlines) is unicode

    def test_mod(self):
        import _io
        typemods = dict((t, t.__module__) for t in vars(_io).values()
                        if isinstance(t, type))
        for t, mod in typemods.items():
            if t is _io.BlockingIOError:
                assert mod == '__builtin__'
            elif t is _io.UnsupportedOperation:
                assert mod == 'io'
            else:
                assert mod == '_io'

    # Not supported: append
    #def test_issue1902(self):
    #    import _io
    #    with _io.open(self.tmpfile, 'w+b', 4096) as f:
    #        f.write(b'\xff' * 13569)
    #        f.flush()
    #        f.seek(0, 0)
    #        f.read(1)
    #        f.seek(-1, 1)
    #        f.write(b'')

    # Not supported: append
    #def test_issue1902_2(self):
    #    import _io
    #    with _io.open(self.tmpfile, 'w+b', 4096) as f:
    #        f.write(b'\xff' * 13569)
    #        f.flush()
    #        f.seek(0, 0)

    #        f.read(1)
    #        f.seek(-1, 1)
    #        f.write(b'\xff')
    #        f.seek(1, 0)
    #        f.read(4123)
    #        f.seek(-4123, 1)

    # Not supported: append
    #def test_issue1902_3(self):
    #    import _io
    #    buffer_size = 4096
    #    with _io.open(self.tmpfile, 'w+b', buffer_size) as f:
    #        f.write(b'\xff' * buffer_size * 3)
    #        f.flush()
    #        f.seek(0, 0)

    #        f.read(1)
    #        f.seek(-1, 1)
    #        f.write(b'\xff')
    #        f.seek(1, 0)
    #        f.read(buffer_size * 2)
    #        assert f.tell() == 1 + buffer_size * 2


class AppTestIoAferClose:
    spaceconfig = dict(usemodules=['_io'])

    def setup_class(cls):
        tmpfile = udir.join('tmpfile').ensure()
        cls.w_tmpfile = cls.space.wrap(str(tmpfile))

    # Not supported: append, seek, tell
    def test_io_after_close(self):
        import _io
        for kwargs in [
                {"mode": "w"},
                {"mode": "wb"},
                {"mode": "w", "buffering": 1},
                {"mode": "w", "buffering": 2},
                {"mode": "wb", "buffering": 0},
                {"mode": "r"},
                {"mode": "rb"},
                {"mode": "r", "buffering": 1},
                {"mode": "r", "buffering": 2},
                {"mode": "rb", "buffering": 0},
                #{"mode": "w+"},
                #{"mode": "w+b"},
                #{"mode": "w+", "buffering": 1},
                #{"mode": "w+", "buffering": 2},
                #{"mode": "w+b", "buffering": 0},
            ]:
            print kwargs
            if "b" not in kwargs["mode"]:
                kwargs["encoding"] = "ascii"
            f = _io.open(self.tmpfile, **kwargs)
            f.close()
            raises(ValueError, f.flush)
            raises(ValueError, f.fileno)
            raises(ValueError, f.isatty)
            raises(ValueError, f.__iter__)
            if hasattr(f, "peek"):
                raises(ValueError, f.peek, 1)
            raises(ValueError, f.read)
            if hasattr(f, "read1"):
                raises(ValueError, f.read1, 1024)
            if hasattr(f, "readall"):
                raises(ValueError, f.readall)
            if hasattr(f, "readinto"):
                raises(ValueError, f.readinto, bytearray(1024))
            raises(ValueError, f.readline)
            raises(ValueError, f.readlines)
            #raises(ValueError, f.seek, 0)
            #raises(ValueError, f.tell)
            raises(ValueError, f.truncate)
            raises(ValueError, f.write, b"" if "b" in kwargs['mode'] else u"")
            raises(ValueError, f.writelines, [])
            raises(ValueError, next, f)
