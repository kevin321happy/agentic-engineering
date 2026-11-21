import sqlite3
import subprocess
import sys

import pytest

from agentic_engineering.core.models import GateDecision
from agentic_engineering.runtime.ledger import GateLedger


def decision(status):
    return GateDecision(
        gate_id="review",
        status=status,
        required_evidence=("ev-test",),
        missing_evidence=() if status == "GO" else ("ev-test",),
        decision_reason="Test review",
        decided_by="policy:review",
    )


@pytest.mark.parametrize("damage", ["missing", "stale", "foreign"])
def test_restart_recovers_latest_decision_from_events(tmp_path, damage):
    db = tmp_path / "ledger.sqlite"
    ledger = GateLedger(db)
    ledger.append("run-a", decision("GO"))
    ledger.append("run-a", decision("NO_GO"))
    ledger.append("run-b", decision("GO"))
    assert ledger.restore("run-a") == decision("NO_GO")
    with sqlite3.connect(db) as conn:
        if damage == "missing":
            conn.execute("DELETE FROM gate_checkpoints WHERE run_id='run-a'")
        else:
            conn.execute(
                "UPDATE gate_checkpoints SET sequence=? WHERE run_id='run-a'",
                (1 if damage == "stale" else 3,),
            )
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from pathlib import Path
from agentic_engineering.runtime.ledger import GateLedger
ledger = GateLedger(Path(sys.argv[1]))
assert ledger.restore('run-a').status == 'NO_GO'
assert ledger.restore('run-b').status == 'GO'
assert ledger.restore('unknown') is None
""",
            str(db),
        ],
        check=True,
    )
    with sqlite3.connect(db) as conn:
        assert conn.execute(
            "SELECT sequence FROM gate_checkpoints WHERE run_id='run-a'"
        ).fetchone() == (2,)
    assert ledger.history("run-a") == [decision("GO"), decision("NO_GO")]
