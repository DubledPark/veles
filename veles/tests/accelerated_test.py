"""
Created on March 19, 2015

Copyright (c) 2013 Samsung Electronics Co., Ltd.
"""


import gc
import inspect
import logging
from six import PY3
import unittest

from veles.backends import Device, BackendRegistry
from veles.config import root
from veles.logger import Logger
if PY3:
    from veles.memory import Vector
from veles.opencl_types import dtypes


def multi_device(numpy=False):
    def real_multi_device(fn):
        def test_wrapped(self):
            backends = list(self.backends)
            if numpy:
                backends.append(None)
            for cls in backends:
                self.device = cls() if cls is not None else None
                self.info("Selected %s",
                          cls.__name__ if cls is not None else "numpy")
                fn(self)

        test_wrapped.__name__ = fn.__name__
        return test_wrapped
    return real_multi_device


def assign_backend(backend):
    def wrapped(cls):
        cls.DEVICE = BackendRegistry.backends[backend]
        cls.ABSTRACT = False
        return cls

    return wrapped


class AcceleratedTest(unittest.TestCase, Logger):
    backends = [v for k, v in sorted(BackendRegistry.backends.items())
                if k not in ("auto", "numpy")]
    DEVICE = Device
    ABSTRACT = False

    def __init__(self, *args, **kwargs):
        Logger.__init__(self)
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.device = self.DEVICE()
        self._dtype = dtypes[root.common.precision_type]

    @property
    def dtype(self):
        return self._dtype

    def tearDown(self):
        if PY3:
            Vector.reset_all()
        del self.device
        gc.collect()
        assert len(gc.garbage) == 0

    def run(self, result=None):
        failure = getattr(type(self), "__unittest_expecting_failure__", False)
        for m in inspect.getmembers(type(self), predicate=inspect.isfunction):
            m[1].__unittest_expecting_failure__ = failure
        if not type(self).ABSTRACT:
            return unittest.TestCase.run(self, result)
        else:
            return None

    @staticmethod
    def main():
        logging.basicConfig(level=logging.DEBUG)
        unittest.main()
