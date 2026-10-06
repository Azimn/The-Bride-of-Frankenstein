from __future__ import annotations

from pathlib import Path
import os
import time


class FileLock:
    """Small cross-platform advisory single-writer lock.

    This protects the gap between committing a canonical event and advancing
    projections. It is not a distributed lock and must not be used for a state
    directory on a network filesystem shared by multiple machines.
    """

    def __init__(self, path: str | Path, *, timeout: float = 30.0, poll: float = 0.05):
        self.path = Path(path)
        self.timeout = timeout
        self.poll = poll
        self._fh = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+b")
        self._fh.seek(0)
        if self._fh.tell() == 0:
            self._fh.write(b"0")
            self._fh.flush()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._acquire()
                return self
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    self._fh.close()
                    self._fh = None
                    raise TimeoutError(f"timed out waiting for writer lock {self.path}")
                time.sleep(self.poll)

    def _acquire(self) -> None:
        self._fh.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, exc_type, exc, tb):
        if self._fh is None:
            return
        try:
            self._fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None
