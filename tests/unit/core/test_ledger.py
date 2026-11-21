import subprocess
import sys

import pytest

from agentic_engineering.core.models import GateDecision


def test_blocked_gate_survives_writer_exit(tmp_path):
    from agentic_engineering.runtime.ledger import GateLedger

    db = tmp_path / "events.sqlite"
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
from pathlib import Path
import sys
from agentic_engineering.runtime.ledger import GateLedger
from agentic_engineering.core.models import GateDecision
ledger = GateLedger(Path(sys.argv[1]))
decision = GateDecision(gate_id='review', required_evidence=('ev-test',),
    missing_evidence=('ev-test',), status='NO_GO', decision_reason='No test result',
    decided_by='policy:review')
ledger.append('run-1', decision)
ledger.append('run-2', decision)
""",
            str(db),
        ],
        check=True,
    )
    ledger = GateLedger(db)
    events = ledger.history("run-1")
    assert len(events) == 1 and events[0].status == "NO_GO"
    approved = GateDecision.model_validate(
        {
            **events[0].model_dump(),
            "status": "GO",
            "missing_evidence": (),
            "decision_reason": "Test result recorded",
        }
    )
    ledger.append("run-1", approved)
    assert ledger.history("run-1") == [events[0], approved]
    assert ledger.history("run-2") == events
    assert ledger.history("absent") == []
    with pytest.raises(ValueError):
        ledger.append("", approved)
