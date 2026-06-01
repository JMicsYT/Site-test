"""
Команда резервного копирования БД.

Работает в двух режимах:
  1. pg_dump — если доступен (PostgreSQL в настройках + pg_dump в PATH).
     Экономнее по размеру, быстрее восстанавливается, рекомендуется для прода.
  2. Django dumpdata (JSON) — fallback, работает всегда.

Примеры:
    python manage.py dump_db
    python manage.py dump_db --out ./backups
    python manage.py dump_db --format json
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создаёт резервную копию базы данных (pg_dump или dumpdata)."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="backups", help="Директория для бэкапов")
        parser.add_argument(
            "--format",
            choices=["auto", "pg", "json"],
            default="auto",
            help="auto — pg_dump если доступен, иначе json",
        )

    def handle(self, *args, **opts):
        out_dir = Path(opts["out"])
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        fmt = opts["format"]
        db = settings.DATABASES["default"]
        is_pg = "postgresql" in db.get("ENGINE", "")

        if fmt == "pg" or (fmt == "auto" and is_pg and shutil.which("pg_dump")):
            return self._pg_dump(db, out_dir, ts)
        return self._dumpdata(out_dir, ts)

    def _pg_dump(self, db, out_dir: Path, ts: str):
        if not shutil.which("pg_dump"):
            raise CommandError(
                "pg_dump не найден в PATH. Используйте --format json для JSON-бэкапа."
            )
        out_file = out_dir / f"shoshop_{ts}.sql.gz"
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]
        cmd = [
            "pg_dump",
            "-h", db.get("HOST") or "localhost",
            "-p", str(db.get("PORT") or 5432),
            "-U", db.get("USER") or "postgres",
            "-d", db["NAME"],
            "--no-owner",
            "--no-privileges",
            "-F", "c",  # custom format
            "-Z", "9",
        ]
        self.stdout.write(f"Запуск pg_dump -> {out_file}")
        try:
            with open(out_file, "wb") as fh:
                proc = subprocess.run(cmd, env=env, stdout=fh, stderr=subprocess.PIPE)
                if proc.returncode != 0:
                    err = proc.stderr.decode("utf-8", errors="replace")
                    raise CommandError(f"pg_dump завершился с ошибкой:\n{err}")
        except FileNotFoundError:
            raise CommandError("Не удалось запустить pg_dump.")

        self.stdout.write(self.style.SUCCESS(f"Готово: {out_file} ({out_file.stat().st_size} байт)"))

    def _dumpdata(self, out_dir: Path, ts: str):
        out_file = out_dir / f"shoshop_{ts}.json.gz"
        import gzip
        import io

        self.stdout.write(f"Django dumpdata -> {out_file}")
        buf = io.StringIO()
        call_command(
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--exclude=contenttypes",
            "--exclude=auth.Permission",
            "--indent", "0",
            stdout=buf,
        )
        with gzip.open(out_file, "wt", encoding="utf-8") as gz:
            gz.write(buf.getvalue())
        self.stdout.write(self.style.SUCCESS(f"Готово: {out_file} ({out_file.stat().st_size} байт)"))
