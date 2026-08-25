"""Host system hardware and process monitoring module (CPU, RAM, Disks, GPU, and Network)."""

import os
import platform
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psutil
from app.helps.utils import logger

try:
    import GPUtil

    GPU_AVAILABLE = True
except Exception as error:
    GPU_AVAILABLE = False
    logger.warning(f"[WARNING NODE-VM] GPUtil not available, GPU monitoring disabled: {error}")


def _get_cpu_info() -> Dict[str, Any]:
    """Retrieve host CPU metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        temperatures = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if "coretemp" in name.lower() or "cpu" in name.lower():
                        temperatures = [entry.current for entry in entries]
                        break
        except (AttributeError, OSError):
            pass

        return {
            "usage": round(cpu_percent, 2),
            "cores": cpu_count,
            "threads": cpu_count_logical,
            "frequency": (
                {
                    "current": round(cpu_freq.current, 2) if cpu_freq else None,
                    "min": round(cpu_freq.min, 2) if cpu_freq else None,
                    "max": round(cpu_freq.max, 2) if cpu_freq else None,
                }
                if cpu_freq
                else None
            ),
            "temperatures": temperatures,
        }
    except Exception as err:
        logger.error(f"[ERROR NODE-VM] Error retrieving CPU metrics: {err}", exc_info=True)
        return {"usage": 0, "cores": None, "threads": None}


class SystemMonitor:
    """Hardware diagnostic monitor with thread-safe caching and metrics history."""

    def __init__(self, cache_duration: int = 5, history_size: int = 100):
        self._cache = None
        self._cache_time = None
        self._cache_duration = timedelta(seconds=cache_duration)
        self._lock = threading.Lock()

        self._history = {
            "cpu": deque(maxlen=history_size),
            "ram": deque(maxlen=history_size),
            "disk": deque(maxlen=history_size),
            "network": deque(maxlen=history_size),
        }

        self._is_windows = platform.system() == "Windows"
        self._disk_path = "C:\\" if self._is_windows else "/"

    def _get_ram_info(self) -> Dict[str, Any]:
        """Retrieve host RAM and Swap memory metrics."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "usage": round(memory.percent, 2),
                "total": self._format_bytes(memory.total),
                "available": self._format_bytes(memory.available),
                "used": self._format_bytes(memory.used),
                "swap": {
                    "usage": round(swap.percent, 2),
                    "total": self._format_bytes(swap.total),
                    "used": self._format_bytes(swap.used),
                },
            }
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error retrieving RAM metrics: {err}", exc_info=True)
            return {"usage": 0, "total": "0 B", "available": "0 B"}

    def _get_disk_info(self) -> Dict[str, Any]:
        """Retrieve disk space and I/O counters."""
        try:
            disk = psutil.disk_usage(self._disk_path)
            io_counters = psutil.disk_io_counters()

            return {
                "usage": round(disk.percent, 2),
                "total": self._format_bytes(disk.total),
                "used": self._format_bytes(disk.used),
                "free": self._format_bytes(disk.free),
                "io": (
                    {
                        "readBytes": self._format_bytes(io_counters.read_bytes) if io_counters else None,
                        "writeBytes": self._format_bytes(io_counters.write_bytes) if io_counters else None,
                        "readCount": io_counters.read_count if io_counters else None,
                        "writeCount": io_counters.write_count if io_counters else None,
                    }
                    if io_counters
                    else None
                ),
            }
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error retrieving Disk metrics: {err}", exc_info=True)
            return {"usage": 0, "total": "0 B", "used": "0 B"}

    def _get_network_info(self) -> Dict[str, Any]:
        """Retrieve network traffic statistics."""
        try:
            net_io = psutil.net_io_counters()

            return {
                "bytesSent": self._format_bytes(net_io.bytes_sent),
                "bytesReceived": self._format_bytes(net_io.bytes_recv),
                "packetsSent": net_io.packets_sent,
                "packetsReceived": net_io.packets_recv,
                "errorsIn": net_io.errin,
                "errorsOut": net_io.errout,
                "dropsIn": net_io.dropin,
                "dropsOut": net_io.dropout,
            }
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error retrieving Network metrics: {err}", exc_info=True)
            return {"bytesSent": "0 B", "bytesReceived": "0 B"}

    def _get_gpu_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve GPU metrics using GPUtil."""
        if not GPU_AVAILABLE:
            return None

        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return None

            return [
                {
                    "id": gpu.id,
                    "name": gpu.name,
                    "load": round(gpu.load * 100, 2),
                    "memoryUsed": self._format_bytes(gpu.memoryUsed * 1024 * 1024),
                    "memoryTotal": self._format_bytes(gpu.memoryTotal * 1024 * 1024),
                    "memoryPercent": round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2) if gpu.memoryTotal > 0 else 0,
                    "temperature": gpu.temperature if hasattr(gpu, "temperature") else None,
                }
                for gpu in gpus
            ]
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error retrieving GPU metrics: {err}", exc_info=True)
            return None

    def _get_process_info(self) -> Dict[str, Any]:
        """Retrieve resource consumption metrics for the active Python bot process."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "pid": process.pid,
                "memoryUsage": self._format_bytes(memory_info.rss),
                "cpuPercent": round(process.cpu_percent(interval=0.1), 2),
                "threads": process.num_threads(),
                "status": process.status(),
            }
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error retrieving process metrics: {err}", exc_info=True)
            return {"pid": os.getpid()}

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format byte counts into human-readable strings."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def get_hardware_info(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieve complete hardware and system diagnostics."""
        try:
            if use_cache:
                with self._lock:
                    if self._cache and self._cache_time:
                        if datetime.now() - self._cache_time < self._cache_duration:
                            return self._cache.copy()

            cpu_info = _get_cpu_info()
            ram_info = self._get_ram_info()
            disk_info = self._get_disk_info()
            network_info = self._get_network_info()
            gpu_info = self._get_gpu_info()
            process_info = self._get_process_info()
            boot_time = psutil.boot_time()
            uptime_seconds = (datetime.now() - datetime.fromtimestamp(boot_time)).total_seconds()

            result = {
                "timestamp": datetime.now().isoformat(),
                "cpu": cpu_info,
                "ram": ram_info,
                "disk": disk_info,
                "network": network_info,
                "gpu": gpu_info,
                "process": process_info,
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python": platform.python_version(),
                    "uptime": uptime_seconds,
                },
            }

            with self._lock:
                self._cache = result
                self._cache_time = datetime.now()
            self._update_history(cpu_info, ram_info, disk_info, network_info)

            return result

        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Failed to retrieve system hardware info: {err}", exc_info=True)
            return None

    def _update_history(self, cpu_info: Dict, ram_info: Dict, disk_info: Dict, network_info: Dict):
        """Update metrics rolling buffer."""
        try:
            with self._lock:
                self._history["cpu"].append(
                    {"timestamp": datetime.now().isoformat(), "value": cpu_info.get("usage", 0)}
                )
                self._history["ram"].append(
                    {"timestamp": datetime.now().isoformat(), "value": ram_info.get("usage", 0)}
                )
                self._history["disk"].append(
                    {"timestamp": datetime.now().isoformat(), "value": disk_info.get("usage", 0)}
                )
                self._history["network"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "sent": network_info.get("bytesSent", "0 B"),
                        "received": network_info.get("bytesReceived", "0 B"),
                    }
                )
        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error updating metric history: {err}", exc_info=True)

    def get_history(self, metric: str = "all") -> Dict[str, List]:
        """Retrieve metrics historical timeline."""
        with self._lock:
            if metric == "all":
                return {k: list(v) for k, v in self._history.items()}
            if metric in self._history:
                return {metric: list(self._history[metric])}
            logger.warning(f"[WARNING NODE-VM] Unknown metric: '{metric}'")
            return {}

    def get_alerts(self, thresholds: Optional[Dict[str, float]] = None) -> List[Dict[str, str]]:
        """Evaluate resource thresholds and generate system alerts."""
        if not thresholds:
            thresholds = {"cpu": 85.0, "ram": 90.0, "disk": 95.0}

        alerts = []
        info = self.get_hardware_info(use_cache=True)

        if not info:
            return alerts

        try:
            if info["cpu"]["usage"] > thresholds.get("cpu", 85):
                alerts.append(
                    {
                        "type": "cpu",
                        "level": "warning",
                        "message": f"High CPU usage: {info['cpu']['usage']}%",
                    }
                )

            if info["ram"]["usage"] > thresholds.get("ram", 90):
                alerts.append(
                    {
                        "type": "ram",
                        "level": "warning",
                        "message": f"High RAM usage: {info['ram']['usage']}%",
                    }
                )

            if info["disk"]["usage"] > thresholds.get("disk", 95):
                alerts.append(
                    {
                        "type": "disk",
                        "level": "critical",
                        "message": f"Critical disk space: {info['disk']['usage']}%",
                    }
                )

            if info.get("gpu"):
                for gpu in info["gpu"]:
                    if gpu["load"] > 95:
                        alerts.append(
                            {
                                "type": "gpu",
                                "level": "warning",
                                "message": f"GPU {gpu['id']} overloaded: {gpu['load']}%",
                            }
                        )

        except Exception as err:
            logger.error(f"[ERROR NODE-VM] Error checking alerts: {err}", exc_info=True)

        return alerts

    def clear_cache(self):
        """Clear cached hardware info."""
        with self._lock:
            self._cache = None
            self._cache_time = None

    def clear_history(self):
        """Clear metrics history deque."""
        with self._lock:
            for key in self._history:
                self._history[key].clear()


def hardware_info() -> Optional[Dict[str, Any]]:
    """Legacy helper for hardware info retrieval."""
    monitor = SystemMonitor(cache_duration=5)
    return monitor.get_hardware_info(use_cache=False)