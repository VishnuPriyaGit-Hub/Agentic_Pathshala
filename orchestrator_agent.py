from __future__ import annotations

from typing import Any, Dict, TypedDict

from langgraph.graph import END, StateGraph


class OrchestratorState(TypedDict, total=False):
    normalized_event: Dict[str, Any]
    routed_task: Dict[str, Any]
    error: str


def validate_event(state: OrchestratorState) -> OrchestratorState:
    event = state.get("normalized_event")
    if not isinstance(event, dict):
        return {"error": "Missing normalized_event."}

    routing = event.get("routing")
    if not isinstance(routing, dict):
        return {"error": "normalized_event.routing is required."}

    intent = routing.get("intent")
    if not intent:
        return {"error": "normalized_event.routing.intent is required."}

    return {}


def route_intent(state: OrchestratorState) -> str:
    if state.get("error"):
        return "invalid"

    event = state["normalized_event"]
    intent = event["routing"]["intent"]

    if intent == "ASSESSMENT_CREATE":
        return "assessment_agent"
    if intent == "CONTENT_PUBLISH":
        return "learning_agent"
    if intent == "ASSESSMENT_FETCH":
        return "assessment_agent"
    if intent == "LEARN_CONTENT_FETCH":
        return "learning_agent"
    if intent == "ASSESSMENT_SUBMIT":
        return "evaluation_agent"
    if intent == "PARENT_VIEW":
        return "parent_agent"
    return "invalid"


def send_to_assessment_agent(state: OrchestratorState) -> OrchestratorState:
    return _route_to_agent(state, "assessment_agent")


def send_to_learning_agent(state: OrchestratorState) -> OrchestratorState:
    return _route_to_agent(state, "learning_agent")


def send_to_evaluation_agent(state: OrchestratorState) -> OrchestratorState:
    return _route_to_agent(state, "evaluation_agent")


def send_to_parent_agent(state: OrchestratorState) -> OrchestratorState:
    return _route_to_agent(state, "parent_agent")


def invalid_event(state: OrchestratorState) -> OrchestratorState:
    return {"error": state.get("error", "Unsupported routing intent.")}


def _route_to_agent(state: OrchestratorState, destination_agent: str) -> OrchestratorState:
    event = state["normalized_event"]
    routed_task = {
        "orchestrator_action": "route",
        "destination_agent": destination_agent,
        "intent": event["routing"]["intent"],
        "payload_type": event.get("payload_type"),
        "source_portal": event.get("source_portal"),
        "event_id": event.get("event_id"),
        "data": event.get("data", {}),
    }
    return {"routed_task": routed_task}


def build_orchestrator_graph():
    graph = StateGraph(OrchestratorState)
    graph.add_node("validate_event", validate_event)
    graph.add_node("send_to_assessment_agent", send_to_assessment_agent)
    graph.add_node("send_to_learning_agent", send_to_learning_agent)
    graph.add_node("send_to_evaluation_agent", send_to_evaluation_agent)
    graph.add_node("send_to_parent_agent", send_to_parent_agent)
    graph.add_node("invalid_event", invalid_event)

    graph.set_entry_point("validate_event")
    graph.add_conditional_edges(
        "validate_event",
        route_intent,
        {
            "assessment_agent": "send_to_assessment_agent",
            "learning_agent": "send_to_learning_agent",
            "evaluation_agent": "send_to_evaluation_agent",
            "parent_agent": "send_to_parent_agent",
            "invalid": "invalid_event",
        },
    )

    graph.add_edge("send_to_assessment_agent", END)
    graph.add_edge("send_to_learning_agent", END)
    graph.add_edge("send_to_evaluation_agent", END)
    graph.add_edge("send_to_parent_agent", END)
    graph.add_edge("invalid_event", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_orchestrator_graph()
    sample_event = {
        "normalized_event": {
            "event_id": "sample-1",
            "source_portal": "teacher",
            "action": "create_assessment_request",
            "payload_type": "portal_input",
            "data": {"grade": "8", "subject": "Science", "topics": ["Cell Structure"]},
            "routing": {"target_agent": "orchestrator", "intent": "ASSESSMENT_CREATE", "priority": "normal"},
        }
    }
    print(app.invoke(sample_event))