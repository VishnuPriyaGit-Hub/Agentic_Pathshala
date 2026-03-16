from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class ParsedAnswerItem(BaseModel):
    question_id: str = Field(description="Question identifier such as Q1")
    type: str = Field(description="MCQ or SHORT_ANSWER")
    selected_option_ids: Optional[List[str]] = None
    text: Optional[str] = None


class ParsedAnswerSubmission(BaseModel):
    portal: str = Field(description="Must be student")
    action: str = Field(description="Canonical action only. Use assessment_submission")
    student_id: Optional[str] = None
    assessment_id: Optional[str] = None
    answers: Optional[List[ParsedAnswerItem]] = None
    submitted_at: Optional[str] = None


class AnswerSubmissionState(TypedDict, total=False):
    ui_input: Any
    parsed_input: Dict[str, Any]
    normalized_event: Dict[str, Any]
    error: str


def llm_parse_answer_submission(state: AnswerSubmissionState) -> AnswerSubmissionState:
    raw_input = state.get("ui_input")
    if raw_input is None:
        return {"error": "Missing ui_input."}

    llm_kwargs = {"model": "gpt-4o-mini", "temperature": 0}
    api_base = os.getenv("OPENAI_API_BASE")
    if api_base:
        llm_kwargs["base_url"] = api_base

    llm = ChatOpenAI(**llm_kwargs)
    structured_llm = llm.with_structured_output(ParsedAnswerSubmission, method="function_calling")

    system_prompt = (
        "You extract only student assessment submissions for an education platform. "
        "Extract only what is explicitly present in the user input into the schema. "
        "Do not hallucinate, infer missing facts, create fake answers, or fill optional fields unless they are clearly provided. "
        "For portal use exactly student. "
        "For action use exactly assessment_submission. "
        "If the input explicitly contains identifiers like S123, A789, Q1, or O2, copy them exactly. "
        "For answers, convert explicit statements into structured items only when the answer content is clearly present. "
        "Use type MCQ when an option selection is given. "
        "Use type SHORT_ANSWER when answer text is given. "
        "Return only structured data through the schema."
    )

    user_payload = json.dumps(raw_input, ensure_ascii=True) if isinstance(raw_input, dict) else str(raw_input)

    try:
        parsed: ParsedAnswerSubmission = structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ]
        )
    except Exception as exc:
        return {"error": f"LLM parsing failed: {exc}"}

    data = parsed.model_dump(exclude_none=True)
    if isinstance(raw_input, str):
        _fill_ids_and_answers_from_text(data, raw_input)

    if str(data.get("portal", "")).strip().lower() != "student":
        return {"error": "Answer submission agent only supports student portal."}

    return {"parsed_input": data}


def _fill_ids_and_answers_from_text(data: Dict[str, Any], raw_text: str) -> None:
    id_patterns = {
        "student_id": r"\bS\d+\b",
        "assessment_id": r"\bA\d+\b",
    }
    for field, pattern in id_patterns.items():
        if data.get(field):
            continue
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            data[field] = match.group(0)

    if data.get("answers"):
        return

    answers: List[Dict[str, Any]] = []
    mcq_matches = re.finditer(r"\bQ(\d+)\b[^\.\n]*?\boption\s+(O\d+)\b", raw_text, re.IGNORECASE)
    for match in mcq_matches:
        answers.append(
            {
                "question_id": f"Q{match.group(1)}",
                "type": "MCQ",
                "selected_option_ids": [match.group(2).upper()],
            }
        )

    short_matches = re.finditer(r"\bQ(\d+)\b[^\.\n]*?saying\s+([^\.]+)", raw_text, re.IGNORECASE)
    for match in short_matches:
        answers.append(
            {
                "question_id": f"Q{match.group(1)}",
                "type": "SHORT_ANSWER",
                "text": match.group(2).strip(),
            }
        )

    if answers:
        answers.sort(key=lambda item: item["question_id"])
        data["answers"] = answers


def extract_submission(state: AnswerSubmissionState) -> AnswerSubmissionState:
    try:
        payload = dict(state.get("parsed_input", {}))
        answers = payload.get("answers")
        if not isinstance(answers, list) or not answers:
            return {"error": "Student assessment submission requires non-empty answers list."}

        normalized_answers: List[Dict[str, Any]] = []
        for entry in answers:
            question_id = entry.get("question_id")
            if not question_id:
                continue
            answer_type = str(entry.get("type", "")).strip().upper()
            if answer_type == "MCQ":
                normalized_answers.append(
                    {
                        "question_id": question_id,
                        "type": "MCQ",
                        "selected_option_ids": entry.get("selected_option_ids", []),
                    }
                )
            else:
                normalized_answers.append(
                    {
                        "question_id": question_id,
                        "type": "SHORT_ANSWER",
                        "text": entry.get("text"),
                    }
                )

        if not normalized_answers:
            return {"error": "Student assessment submission requires non-empty answers list."}

        event = {
            "event_id": str(uuid.uuid4()),
            "source_portal": "student",
            "action": "assessment_submission",
            "payload_type": "answer_submission",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "data": {
                "student_id": _require(payload, "student_id"),
                "assessment_id": _require(payload, "assessment_id"),
                "answers": normalized_answers,
                "submitted_at": payload.get("submitted_at"),
            },
            "routing": {
                "target_agent": "orchestrator",
                "intent": "ASSESSMENT_SUBMIT",
                "priority": "normal",
            },
        }
        return {"normalized_event": event}
    except Exception as exc:
        return {"error": str(exc)}


def invalid_input(state: AnswerSubmissionState) -> AnswerSubmissionState:
    return {"error": state.get("error", "Invalid input.")}


def _require(payload: Dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Missing required field '{key}'.")
    return value


def route_submission(state: AnswerSubmissionState) -> str:
    return "extract_submission" if not state.get("error") else "invalid_input"


def build_answer_submission_extractor_graph():
    graph = StateGraph(AnswerSubmissionState)
    graph.add_node("llm_parse_answer_submission", llm_parse_answer_submission)
    graph.add_node("extract_submission", extract_submission)
    graph.add_node("invalid_input", invalid_input)
    graph.set_entry_point("llm_parse_answer_submission")
    graph.add_conditional_edges(
        "llm_parse_answer_submission",
        route_submission,
        {"extract_submission": "extract_submission", "invalid_input": "invalid_input"},
    )
    graph.add_edge("extract_submission", END)
    graph.add_edge("invalid_input", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_answer_submission_extractor_graph()
    print(app.invoke({"ui_input": "Student S456 submits assessment A789 with one MCQ answer for Q1 option O2 and one short answer for Q2 saying photosynthesis needs sunlight."}))