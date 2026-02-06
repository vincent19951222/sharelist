import time
from typing import Dict
from collections import deque

class Telemetry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        # Gauges (Instantaneous values)
        self.active_connections = 0
        
        # Counters (Cumulative values)
        self.connections_total = 0
        self.events_total = 0
        self.errors_total = 0
        self.broadcasts_total = 0
        self.broadcast_errors_total = 0
        self.db_writes_total = 0
        self.db_reads_total = 0
        
        # Histograms (Approximated by simple moving average)
        self.db_latency_ms_avg = 0.0
        self.last_db_latencies = deque(maxlen=50) # Keep last 50 samples

    def increment_connections(self):
        self.active_connections += 1
        self.connections_total += 1

    def decrement_connections(self):
        self.active_connections = max(0, self.active_connections - 1)

    def track_event(self):
        self.events_total += 1

    def track_error(self):
        self.errors_total += 1
        
    def track_broadcast_error(self):
        self.broadcast_errors_total += 1

    def track_db_latency(self, start_time: float, is_write: bool = True):
        """
        Records latency in milliseconds.
        """
        duration = (time.time() - start_time) * 1000
        self.last_db_latencies.append(duration)
        # Recalculate moving average
        self.db_latency_ms_avg = sum(self.last_db_latencies) / len(self.last_db_latencies)
        
        if is_write:
            self.db_writes_total += 1
        else:
            self.db_reads_total += 1

    def get_stats(self) -> Dict:
        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "connections": {
                "active": self.active_connections,
                "total_cumulative": self.connections_total
            },
            "traffic": {
                "events_processed": self.events_total,
                "broadcasts_sent": self.broadcasts_total,
                "broadcast_failure_rate": round((self.broadcast_errors_total / max(1, self.broadcasts_total)) * 100, 2)
            },
            "health": {
                "errors_count": self.errors_total,
                "avg_db_latency_ms": round(self.db_latency_ms_avg, 2)
            }
        }
    
    def set_start_time(self):
        self.start_time = time.time()

# Singleton Instance
metrics = Telemetry()
metrics.set_start_time()
