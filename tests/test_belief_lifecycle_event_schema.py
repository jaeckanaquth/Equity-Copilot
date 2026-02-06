from uuid import uuid4
from datetime import datetime, timezone

from core.models.belief_lifecycle_event import (
    BeliefLifecycleEvent,
    LifecycleTrigger,
    LifecycleJustification,
    RecordedBy,
    BeliefState,
    TriggerType,
)


def test_belief_lifecycle_event_valid():
    event = BeliefLifecycleEvent(
        event_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
        recorded_by=RecordedBy.human,
        reasoning_id=uuid4(),
        previous_state=BeliefState.active,
        new_state=BeliefState.under_review,
        trigger=LifecycleTrigger(
            trigger_type=TriggerType.scheduled_review,
            description="Quarterly review",
        ),
        justification=LifecycleJustification(
            summary="Scheduled reassessment of thesis",
            snapshot_ids=[uuid4()],
        ),
    )

    assert event.schema_version == "v1"
