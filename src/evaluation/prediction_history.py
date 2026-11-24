"""Local history for authenticated batch predictions."""

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime

HISTORY_LIMIT = 100


class PredictionHistory:
    def __init__(self, path):
        self.path = path

    def append(self, result, representation):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "representation": representation,
            "model_version": result["model_version"],
            "preprocessing_id": result["preprocessing_id"],
            "feature_schema_sha256": result["feature_schema_sha256"],
            "threshold": result["threshold"],
            "detector_status": None,
            "predictions": result["predictions"],
        }
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
            )
            cursor = db.execute("INSERT INTO batches(payload) VALUES (?)", (json.dumps(entry),))
            db.execute(
                "DELETE FROM batches WHERE id <= (SELECT max(id) FROM batches) - ?",
                (HISTORY_LIMIT,),
            )
            return {"batch_id": cursor.lastrowid, **entry}

    def list(self):
        if not self.path.is_file():
            return []
        with closing(sqlite3.connect(self.path)) as db:
            # A first writer may have opened the file and still be creating the table.
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'batches'"
            ).fetchone()
            if not exists:
                return []
            rows = db.execute(
                "SELECT id, payload FROM batches ORDER BY id DESC LIMIT ?", (HISTORY_LIMIT,)
            ).fetchall()
        return [{"batch_id": batch_id, **json.loads(payload)} for batch_id, payload in rows]
