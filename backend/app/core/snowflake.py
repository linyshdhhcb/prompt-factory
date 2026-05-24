from __future__ import annotations

import time
import threading


class SnowflakeGenerator:
    def __init__(self, worker_id: int = 1, datacenter_id: int = 1, epoch: int = 1704067200000):
        self.worker_id = worker_id & 0x1F
        self.datacenter_id = datacenter_id & 0x1F
        self.epoch = epoch
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last: int) -> int:
        ts = self._current_millis()
        while ts <= last:
            ts = self._current_millis()
        return ts

    def generate(self) -> int:
        with self._lock:
            ts = self._current_millis() - self.epoch

            if ts == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:
                    ts = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = ts

            return (
                (ts << 22)
                | (self.datacenter_id << 17)
                | (self.worker_id << 12)
                | self.sequence
            )

    def generate_str(self) -> str:
        return str(self.generate())


_snowflake: SnowflakeGenerator | None = None


def get_snowflake() -> SnowflakeGenerator:
    global _snowflake
    if _snowflake is None:
        _snowflake = SnowflakeGenerator()
    return _snowflake


def snowflake_id() -> str:
    return get_snowflake().generate_str()
