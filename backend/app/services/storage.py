"""Atomic JSON persistence for the local, single-worker deployment."""
import json
import os
import tempfile
from functools import wraps
from threading import RLock

storage_lock = RLock()


def locked(method):
    @wraps(method)
    def wrapped(*args, **kwargs):
        with storage_lock:
            return method(*args, **kwargs)
    return wrapped


def write_json(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
