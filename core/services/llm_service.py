"""
Phase 3.3 — LLM assistive layer.

Assistive, optional, attributable, sandboxed.
Never structural glue. Never auto-mutation.

Backend: Ollama (free, local). Run `ollama serve` and use a model from `ollama list`.
Fits 8GB VRAM. Strong instruction following. Good JSON compliance.
"""
import os
from typing import Optional

import requests

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")  # Use model you have (ollama list)
TEMPERATURE = 0.2  # Deterministic
MAX_TOKENS = 1024
CONTEXT_LIMIT_CHARS = 2000

SYSTEM_MESSAGE = "You are a precise, literal assistant. Follow instructions strictly."


class LLMNotConfigured(Exception):
    """Raised when no LLM backend is available."""
    pass


class LLMService:
    """Sandboxed LLM calls via Ollama. User-initiated only. No side effects."""

    def __init__(self):
        self._base_url = OLLAMA_BASE_URL.rstrip("/")
        self._model = OLLAMA_MODEL
        self._backend = "ollama" if self._check_ollama_available() else None

    def _check_ollama_available(self) -> bool:
        try:
            r = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    @property
    def available(self) -> bool:
        return self._backend is not None

    @property
    def backend_name(self) -> str:
        return self._backend or "none"

    def draft_refined_belief(
        self,
        statement: str,
        artifact_type: str,
        snapshot_summary: str = "",
    ) -> str:
        """Option 1 — Drafting Assistant. Only rephrase/clarify. No new factual claims."""
        prompt = f"""You are a drafting assistant for an equity research system. Refine this belief into clearer, more precise language.

STRICT RULES:
- Do not introduce new factual claims not present in the original.
- Do not assume unseen data.
- Only rephrase or clarify.
- Preserve the original intent.
- Preserve epistemic tone if present (e.g., "may", "could", "likely") — do not inflate to certainty.
- Do not imply observed evidence unless explicitly stated in the original.

Artifact type: {artifact_type}
Belief: {statement}
"""
        if snapshot_summary:
            prompt += f"\nReferenced snapshots (ticker + as_of) for context only:\n{snapshot_summary}\n"
        prompt += "\nOutput only the refined belief text, no preamble."
        return self._call(prompt, max_tokens=512)

    def draft_refined_question(self, question: str, snapshot_summary: str = "") -> str:
        """Option 1 — Drafting Assistant. Only rephrase/clarify."""
        prompt = f"""You are a drafting assistant. Refine this research question into clearer, more focused language.

STRICT RULES:
- Do not introduce new factual claims. Only rephrase or clarify.
- Preserve epistemic tone if present (e.g., "may", "could") — do not inflate to certainty.
- Do not imply observed evidence unless explicitly stated.

Question: {question}
"""
        if snapshot_summary:
            prompt += f"\nSnapshot context (reference only):\n{snapshot_summary}\n"
        prompt += "\nOutput only the refined question text, no preamble."
        return self._call(prompt, max_tokens=512)

    def suggest_sub_questions(self, question: str) -> str:
        """Suggest clarifying sub-questions for a research question."""
        prompt = f"""You are a research assistant. Given this research question, suggest 2-4 focused sub-questions that would help answer it. Output as a bullet list.
Optional brainstorming only—do not imply these are required.

Question: {question}

Output only the sub-questions, one per line with a leading dash."""
        return self._call(prompt)

    def summarize_snapshots(self, snapshot_texts: list[str]) -> str:
        """Summarize snapshot metrics in plain language."""
        if not snapshot_texts:
            return "No snapshots available."
        combined = "\n---\n".join(snapshot_texts[:5])
        prompt = f"""You are a research assistant. Summarize the key metrics and context from these equity snapshots in 2-4 sentences. Focus on: revenue, margins, market state, notable changes. Be factual.

Snapshots:
{combined}

Output only the summary."""
        return self._call(prompt)

    def explain_proposal_trigger(
        self,
        proposal_type: str,
        belief_text: str,
        condition_state: Optional[dict] = None,
    ) -> str:
        """Explain why a structural proposal was triggered."""
        cond = condition_state or {}
        cond_type = cond.get("type", proposal_type)
        triggered_at = cond.get("triggered_at", "unknown")
        belief_snippet = (belief_text or "")[:300]

        prompt = f"""Explain in 1-3 sentences why this structural proposal was triggered. Be factual and structural only—do not interpret or recommend.

Proposal type: {proposal_type}
Condition type: {cond_type}
Triggered at: {triggered_at}
Belief: {belief_snippet}

Output only the explanation."""
        return self._call(prompt, max_tokens=256)

    def analyze_belief_changes(
        self,
        belief_text: str,
        last_review_iso: str,
        previous_snapshots_summary: str,
        newer_snapshots_summary: str,
    ) -> dict:
        """Option 2 — Structural Change Analysis. Structured JSON."""
        prev = (previous_snapshots_summary or "None")[:CONTEXT_LIMIT_CHARS]
        newer = (newer_snapshots_summary or "")[:CONTEXT_LIMIT_CHARS]

        prompt = f"""You are analyzing structural change for an equity research belief. The snapshots below are the ONLY ones referenced by this belief — no other companies.

Produce a structured analysis. Return strictly valid JSON. Do not wrap in code blocks. Do not include commentary. Output only the JSON object with these exact keys:
- delta_summary: string — 2-4 sentence summary of key metric changes. If no material structural change is evident, explicitly state "No material change detected."
- potential_tensions: array of strings (0-3 items) — ways the new data might tension the belief. Empty array if none.
- questions_raised: array of strings (0-3 items) — questions the new data raises. Empty array if none.

Do NOT modify the belief. Do NOT recommend actions. Analysis only. If nothing material changed, say so — do not invent tensions.

Belief: {belief_text[:500]}
Last review: {last_review_iso}

Previous snapshot metrics (at last review, this belief's referenced snapshots only):
{prev}

New snapshot metrics (same companies, since last review):
{newer}
"""
        raw = self._call(prompt, max_tokens=MAX_TOKENS, json_mode=True)
        return self._parse_analysis_json(raw)

    def _parse_analysis_json(self, raw: str) -> dict:
        import json
        raw = raw.strip()
        for start in ("```json", "```"):
            if start in raw:
                raw = raw.split(start, 1)[-1].split("```", 1)[0].strip()
        try:
            d = json.loads(raw)
            tensions = d.get("potential_tensions") or []
            questions = d.get("questions_raised") or []
            return {
                "delta_summary": str(d.get("delta_summary") or ""),
                "potential_tensions": [str(x) for x in tensions if x is not None],
                "questions_raised": [str(x) for x in questions if x is not None],
            }
        except (json.JSONDecodeError, TypeError):
            return {
                "delta_summary": raw[:800],
                "potential_tensions": [],
                "questions_raised": [],
            }

    def _call(
        self,
        prompt: str,
        max_tokens: int = MAX_TOKENS,
        json_mode: bool = False,
    ) -> str:
        if not self._backend:
            raise LLMNotConfigured(
                "Ollama not available. Run `ollama serve` and ensure a model is installed (see `ollama list`)."
            )
        return self._call_ollama(prompt, max_tokens, json_mode)

    def _call_ollama(
        self,
        prompt: str,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        try:
            payload = {
                "model": self._model,
                "prompt": prompt,
                "system": SYSTEM_MESSAGE,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE,
                    "num_predict": max_tokens,
                },
            }
            if json_mode:
                payload["format"] = "json"

            r = requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            response = (data.get("response") or "").strip()

            if json_mode and "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                if end > start:
                    response = response[start:end]

            return response
        except Exception as e:
            return f'{{"delta_summary": "[LLM error: ' + str(e).replace('"', "'") + ']", "potential_tensions": [], "questions_raised": []}}'
