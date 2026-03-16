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


class ParsedPortalInput(BaseModel):
    portal: str = Field(description="teacher | student | parent")
    action: Optional[str] = Field(
        default=None,
        description="Canonical action only. Use one of: publish_curriculum, create_assessment_request, progress_view.",
    )
    grade: Optional[str] = None
    subject: Optional[str] = None
    topics: Optional[List[str]] = None
    assessment_type: Optional[str] = Field(default=None, description="MCQ | SHORT_ANSWER | MIXED")
    total_questions: Optional[int] = None
    mcq_count: Optional[int] = None
    short_answer_count: Optional[int] = None
    student_id: Optional[str] = None
    parent_id: Optional[str] = None
    mode: Optional[str] = Field(
        default=None,
        description="Canonical student mode only. Use one of: learn_mode, assessment_mode. Use assessment_mode when the student wants to start or take an assessment.",
    )
    submitted_at: Optional[str] = None
    difficulty: Optional[str] = None
    duration_minutes: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class PortalInputState(TypedDict, total=False):
    ui_input: Any
    parsed_input: Dict[str, Any]
    portal: str
    normalized_event: Dict[str, Any]
    error: str


ALLOWED_PORTALS = {"teacher", "student", "parent"}


def llm_parse_portal_input(state: PortalInputState) -> PortalInputState:
    raw_input = state.get("ui_input")
    if raw_input is None:
        return {"error": "Missing ui_input."}

    llm_kwargs = {"model": "gpt-4o-mini", "temperature": 0}
    api_base = os.getenv("OPENAI_API_BASE")
    if api_base:
        llm_kwargs["base_url"] = api_base

    llm = ChatOpenAI(**llm_kwargs)
    structured_llm = llm.with_structured_output(ParsedPortalInput, method="function_calling")

    system_prompt = (
        "You extract portal input for an education platform. "
        "Extract only what is explicitly present in the user input into the schema. "
        "Do not hallucinate, infer missing facts, guess IDs, invent answers, or fill optional fields unless they are clearly provided. "
        "If a value is not explicitly given, leave it unset. "
        "Normalize synonyms such as class to grade, chapter to topics, and test or quiz to assessment. "
        "Return canonical values only. "
        "For portal use exactly one of: teacher, student, parent. "
        "For teacher action use exactly one of: publish_curriculum, create_assessment_request. "
        "For parent action use progress_view unless another supported parent action is explicitly stated. "
        "For student mode in this agent use learn_mode when learn intent is clearly present. "
        "Use assessment_mode when the student wants to start, open, attempt, or take an assessment but is not yet submitting answers. "
        "Do not extract assessment submission answers in this agent. "
        "If the input explicitly contains identifiers like S123 or P100, copy them exactly into student_id or parent_id. "
        "Return only structured data through the schema."
    )

    user_payload = json.dumps(raw_input, ensure_ascii=True) if isinstance(raw_input, dict) else str(raw_input)

    try:
        parsed: ParsedPortalInput = structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ]
        )
    except Exception as exc:
        return {"error": f"LLM parsing failed: {exc}"}

    data = parsed.model_dump(exclude_none=True)
    if isinstance(raw_input, str):
        _fill_explicit_ids_from_text(data, raw_input)

    portal = str(data.get("portal", "")).strip().lower()
    if portal not in ALLOWED_PORTALS:
        return {"error": f"Unsupported portal '{portal}'."}

    return {"parsed_input": data, "portal": portal}


def _fill_explicit_ids_from_text(data: Dict[str, Any], raw_text: str) -> None:
    patterns = {
        "student_id": r"\bS\d+\b",
        "parent_id": r"\bP\d+\b",
    }
    for field, pattern in patterns.items():
        if data.get(field):
            continue
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            data[field] = match.group(0)


def route_portal(state: PortalInputState) -> str:
    if state.get("error"):
        return "invalid"
    portal = state.get("portal")
    if portal in ALLOWED_PORTALS:
        return portal
    return "invalid"


def extract_teacher(state: PortalInputState) -> PortalInputState:
    try:
        payload = dict(state.get("parsed_input", {}))
        action = _normalize_teacher_action(payload.get("action"))

        if action == "publish_curriculum":
            grade = _require(payload, "grade")
            subject = _require(payload, "subject")
            topics = _listify(payload.get("topics"))
            if not topics:
                return {"error": "Teacher curriculum publish requires at least one topic."}
            data = {"grade": grade, "subject": subject, "topics": topics}
            return {"normalized_event": _event("teacher", action, "portal_input", data, "CONTENT_PUBLISH")}

        if action == "create_assessment_request":
            grade = _require(payload, "grade")
            subject = _require(payload, "subject")
            topics = _listify(payload.get("topics"))
            if not topics:
                return {"error": "Assessment request requires topic(s)."}
            question_mix = _resolve_question_mix(payload)
            data = {
                "grade": grade,
                "subject": subject,
                "topics": topics,
                "assessment_format": _normalize_assessment_format(payload.get("assessment_type", "MIXED")),
                "total_questions": question_mix["total_questions"],
                "mcq_count": question_mix["mcq_count"],
                "short_answer_count": question_mix["short_answer_count"],
                "difficulty": payload.get("difficulty"),
                "duration_minutes": payload.get("duration_minutes"),
            }
            return {"normalized_event": _event("teacher", action, "portal_input", data, "ASSESSMENT_CREATE")}

        return {"error": f"Unsupported teacher action '{action}'."}
    except Exception as exc:
        return {"error": str(exc)}


def extract_student(state: PortalInputState) -> PortalInputState:
    try:
        payload = dict(state.get("parsed_input", {}))
        mode = _normalize_student_mode(payload.get("mode") or payload.get("action"))
        if mode == "learn_mode":
            data = {
                "student_id": _require(payload, "student_id"),
                "grade": _require(payload, "grade"),
                "subject": _require(payload, "subject"),
                "topics": _listify(payload.get("topics")),
            }
            return {"normalized_event": _event("student", "learn_mode_access", "portal_input", data, "LEARN_CONTENT_FETCH")}

        if mode == "assessment_mode":
            data = {
                "student_id": _require(payload, "student_id"),
                "grade": payload.get("grade"),
                "subject": payload.get("subject"),
                "topics": _listify(payload.get("topics")),
            }
            return {"normalized_event": _event("student", "assessment_mode_access", "portal_input", data, "ASSESSMENT_FETCH")}

        return {"error": f"Unsupported student mode '{mode}'."}
    except Exception as exc:
        return {"error": str(exc)}


def extract_parent(state: PortalInputState) -> PortalInputState:
    try:
        payload = dict(state.get("parsed_input", {}))
        data = {
            "parent_id": _require(payload, "parent_id"),
            "student_id": _require(payload, "student_id"),
            "grade": payload.get("grade"),
            "subject": payload.get("subject"),
            "requested_at": payload.get("submitted_at"),
            "meta": payload.get("meta", {}),
        }
        action = payload.get("action") or "progress_view"
        return {"normalized_event": _event("parent", action, "portal_input", data, "PARENT_VIEW")}
    except Exception as exc:
        return {"error": str(exc)}


def invalid_input(state: PortalInputState) -> PortalInputState:
    return {"error": state.get("error", "Invalid input.")}


def _event(source_portal: str, action: str, payload_type: str, data: Dict[str, Any], intent: str) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "source_portal": source_portal,
        "action": action,
        "payload_type": payload_type,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "routing": {
            "target_agent": "orchestrator",
            "intent": intent,
            "priority": "normal",
        },
    }


def _normalize_teacher_action(action: Optional[str]) -> str:
    if not action:
        return "publish_curriculum"
    value = str(action).strip().lower()
    mapping = {
        "publish_curriculum": "publish_curriculum",
        "publish": "publish_curriculum",
        "push": "publish_curriculum",
        "push_subject_topic": "publish_curriculum",
        "create_assessment_request": "create_assessment_request",
        "create_assessment": "create_assessment_request",
        "create assessment": "create_assessment_request",
        "assessment_request": "create_assessment_request",
    }
    return mapping.get(value, value)


def _normalize_student_mode(mode: Optional[str]) -> str:
    if not mode:
        return ""
    value = str(mode).strip().lower()
    mapping = {
        "learn_mode": "learn_mode",
        "learn": "learn_mode",
        "assessment_mode": "assessment_mode",
        "assessment": "assessment_mode",
        "take_assessment": "assessment_mode",
        "take assessment": "assessment_mode",
    }
    return mapping.get(value, value)


def _normalize_assessment_format(value: str) -> str:
    v = str(value).strip().upper()
    aliases = {
        "MCQ": "MCQ",
        "SHORT_ANSWER": "SHORT_ANSWER",
        "SHORT": "SHORT_ANSWER",
        "MIXED": "MIXED",
        "BOTH": "MIXED",
        "COMBINED": "MIXED",
    }
    return aliases.get(v, "MIXED")


def _resolve_question_mix(payload: Dict[str, Any]) -> Dict[str, int]:
    explicit_mcq = payload.get("mcq_count")
    explicit_short = payload.get("short_answer_count")
    if explicit_mcq is not None and explicit_short is not None:
        mcq_count = int(explicit_mcq)
        short_count = int(explicit_short)
        return {
            "total_questions": mcq_count + short_count,
            "mcq_count": mcq_count,
            "short_answer_count": short_count,
        }

    total_questions = int(payload.get("total_questions") or payload.get("question_count") or 10)
    assessment_format = _normalize_assessment_format(payload.get("assessment_type", "MIXED"))

    if assessment_format == "MCQ":
        return {
            "total_questions": total_questions,
            "mcq_count": total_questions,
            "short_answer_count": 0,
        }

    if assessment_format == "SHORT_ANSWER":
        return {
            "total_questions": total_questions,
            "mcq_count": 0,
            "short_answer_count": total_questions,
        }

    mcq_count = max(0, round(total_questions * 0.8))
    return {
        "total_questions": total_questions,
        "mcq_count": mcq_count,
        "short_answer_count": max(0, total_questions - mcq_count),
    }


def _require(payload: Dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Missing required field '{key}'.")
    return value


def _listify(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def build_portal_input_extractor_graph():
    graph = StateGraph(PortalInputState)
    graph.add_node("llm_parse_portal_input", llm_parse_portal_input)
    graph.add_node("extract_teacher", extract_teacher)
    graph.add_node("extract_student", extract_student)
    graph.add_node("extract_parent", extract_parent)
    graph.add_node("invalid_input", invalid_input)
    graph.set_entry_point("llm_parse_portal_input")
    graph.add_conditional_edges(
        "llm_parse_portal_input",
        route_portal,
        {"teacher": "extract_teacher", "student": "extract_student", "parent": "extract_parent", "invalid": "invalid_input"},
    )
    graph.add_edge("extract_teacher", END)
    graph.add_edge("extract_student", END)
    graph.add_edge("extract_parent", END)
    graph.add_edge("invalid_input", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_portal_input_extractor_graph()
    print(app.invoke({"ui_input": "Teacher wants Grade 8 Science assessment on Cell Structure with 20 questions"}))
