import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic import TypeAdapter

from agentic_engineering.core.models import GateDecision, Identifier

_RUN_ID = TypeAdapter[str](Identifier)


class GateLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS gate_events (
                sequence INTEGER PRIMARY KEY, run_id TEXT NOT NULL, decision TEXT NOT NULL
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS gate_run ON gate_events(run_id, sequence)")

            conn.execute("""CREATE TABLE IF NOT EXISTS gate_checkpoints (
                run_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL
            )""")

    @staticmethod
    def _checkpoint(conn: sqlite3.Connection, key: str, sequence: int) -> None:
        conn.execute(
            """INSERT INTO gate_checkpoints(run_id, sequence) VALUES (?, ?)
            ON CONFLICT(run_id) DO UPDATE SET sequence=excluded.sequence
            WHERE sequence != excluded.sequence""",
            (key, sequence),
        )

    def restore(self, run_id: str) -> GateDecision | None:
        key = _RUN_ID.validate_python(run_id)
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """SELECT sequence, decision FROM gate_events
                WHERE run_id=? ORDER BY sequence DESC LIMIT 1""",
                (key,),
            ).fetchone()
            if row is None:
                return None
            record = GateDecision.model_validate_json(row[1])
            self._checkpoint(conn, key, row[0])
            return record

    def append(self, run_id: str, decision: GateDecision) -> None:
        key = _RUN_ID.validate_python(run_id)
        record = GateDecision.model_validate_json(decision.model_dump_json())
        with closing(sqlite3.connect(self.path)) as conn, conn:
            cursor = conn.execute(
                "INSERT INTO gate_events(run_id, decision) VALUES (?, ?)",
                (key, record.model_dump_json()),
            )
            sequence = cursor.lastrowid
            if sequence is None:
                raise RuntimeError("Gate event has no sequence")
            self._checkpoint(conn, key, sequence)

    def history(self, run_id: str) -> list[GateDecision]:
        with closing(sqlite3.connect(self.path)) as conn:
            rows = conn.execute(
                "SELECT decision FROM gate_events WHERE run_id=? ORDER BY sequence",
                (_RUN_ID.validate_python(run_id),),
            )
            return [GateDecision.model_validate_json(row[0]) for row in rows]
