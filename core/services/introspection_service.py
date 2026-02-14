from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List
from core.models.reasoning_artifact import ArtifactType


class IntrospectionService:

    def __init__(self, artifact_repo):
        self.artifact_repo = artifact_repo

    def get_open_questions(self) -> Dict[str, List]:
        artifacts = self.artifact_repo.list_by_type("ReasoningArtifact")
        now = datetime.now(timezone.utc)

        flat_results = []

        for artifact in artifacts:
            if artifact.artifact_type != ArtifactType.question:
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
