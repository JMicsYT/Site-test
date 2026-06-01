"""JSON-форматтер для структурированных логов."""
import json
import logging
import traceback


class JsonFormatter(logging.Formatter):
    """Пишет одну JSON-строку на запись лога. Удобно для агрегаторов (Loki/ELK)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
        }
        for key in ("user_id", "ip", "event", "path", "request_id"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, ensure_ascii=False)
