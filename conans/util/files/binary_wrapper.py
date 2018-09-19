
import os
from contextlib import contextmanager, ExitStack
from conans.util.progress_bar import progress_bar, tqdm_file_defaults


class BinaryFileWrapper(object):

    def __init__(self, fileobj):
        self._fileobj = fileobj

    def seek(self, *args, **kwargs):
        return self._fileobj.seek(*args, **kwargs)

    def tell(self):
        return self._fileobj.tell()

    def read(self, size):
        return self._fileobj.read(size)

    def close(self):
        self._fileobj.close()


class ChunkedMixin(object):
    """ Mixin to return file in chunks """

    def __init__(self, chunk_size, *args, **kwargs):
        self._chunk_size = chunk_size
        super(ChunkedMixin, self).__init__(*args, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        data = self.read(self._chunk_size)
        if not data:
            raise StopIteration
        return data

    next = __next__  # For python2 compatibility


class ProgressBarMixin(object):

    def __init__(self, pb, *args, **kwargs):
        self._pb = pb
        super(ProgressBarMixin, self).__init__(*args, **kwargs)

    def read(self, size):
        import time
        time.sleep(0.2)
        self._pb.update(size)
        return super(ProgressBarMixin, self).read(size)

    def close(self):
        super(ProgressBarMixin, self).close()
        self._pb.close()


@contextmanager
def open_binary(path, output=None, chunk_size=None, desc=None, **kwargs):
    base_classes = ()

    with ExitStack() as stack:
        # If output is given, then add a progress bar
        if output:
            base_classes += (ProgressBarMixin,)
            total_size = os.stat(path).st_size
            pb = stack.enter_context(progress_bar(output=output, total=total_size, desc=desc,
                                                  **tqdm_file_defaults))
            kwargs.update({'pb': pb})

        # If chunk_size, then return file in chunks
        if chunk_size:
            base_classes += (ChunkedMixin,)
            kwargs.update({'chunk_size': chunk_size})

        base_classes = base_classes + (BinaryFileWrapper,)
        wrapper_class = type('WrapperClass', base_classes, {})
        f = stack.enter_context(open(path, mode='rb'))
        file_wrapper = wrapper_class(fileobj=f, **kwargs)
        yield file_wrapper