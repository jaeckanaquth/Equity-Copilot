from collections import defaultdict
from datetime import UTC, datetime

from core.models.reasoning_artifact import ArtifactType


class IntrospectionService:

    def __init__(self, artifact_repo, answered_question_ids: set[str] | None = None):
        self.artifact_repo = artifact_repo
        self.answered_question_ids = answered_question_ids or set()

    def get_open_questions(self) -> dict[str, list]:
        """Questions that have no recorded answer (open = unanswered)."""
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        now = datetime.now(UTC)

        flat_results = []

        for artifact in artifacts:
            if artifact.artifact_type != ArtifactType.question:
                continue
            if str(artifact.reasoning_id) in self.answered_question_ids:
                continue

            age_days = (now - artifact.created_at).days

            tickers = set()
            for sid in artifact.references.snapshot_ids:
                snapshot = self.artifact_repo.get(str(sid))
                if snapshot and snapshot.company.ticker:
                    tickers.add(snapshot.company.ticker)

            flat_results.append({
                "question_id": str(artifact.reasoning_id),
                "question_text": artifact.claim.statement,
                "age_days": age_days,
                "snapshot_ids": [str(s) for s in artifact.references.snapshot_ids],
                "company_tickers": sorted(list(tickers)),
            })

        flat_results.sort(key=lambda x: x["age_days"], reverse=True)

        grouped = defaultdict(list)
        for item in flat_results:
            if not item["company_tickers"]:
                grouped["uncoupled"].append(item)
            else:
                key = ", ".join(item["company_tickers"])
                grouped[key].append(item)

        return dict(grouped)
