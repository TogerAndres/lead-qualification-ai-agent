"""
Métricas en memoria, expuestas vía GET /metrics.

Nota de diseño (documentado también en el README): al ser en memoria, estas
métricas viven dentro de un único proceso/instancia. Si Cloud Run escala a más
de una instancia, cada una llevará su propio contador — es una limitación
conocida y aceptable para el alcance de este proyecto (no reemplaza un backend
de métricas real como Cloud Monitoring/Prometheus en un escenario de producción
a mayor escala).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _Metrics:
    leads_processed: int = 0
    leads_qualified: int = 0
    leads_rejected: int = 0
    classification_errors: int = 0
    total_response_time_seconds: float = 0.0
    started_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_lead(self, qualified: bool, elapsed_seconds: float, errored: bool = False) -> None:
        with self._lock:
            self.leads_processed += 1
            if errored:
                self.classification_errors += 1
            elif qualified:
                self.leads_qualified += 1
            else:
                self.leads_rejected += 1
            self.total_response_time_seconds += elapsed_seconds

    def snapshot(self) -> dict:
        with self._lock:
            avg_time = (
                self.total_response_time_seconds / self.leads_processed
                if self.leads_processed
                else 0.0
            )
            return {
                "leads_procesados": self.leads_processed,
                "leads_cualificados": self.leads_qualified,
                "leads_rechazados": self.leads_rejected,
                "errores_clasificacion": self.classification_errors,
                "tiempo_promedio_respuesta_segundos": round(avg_time, 3),
                "uptime_segundos": round(time.time() - self.started_at, 1),
            }


_metrics = _Metrics()


def record_lead(qualified: bool, elapsed_seconds: float, errored: bool = False) -> None:
    _metrics.record_lead(qualified, elapsed_seconds, errored)


def snapshot() -> dict:
    return _metrics.snapshot()
