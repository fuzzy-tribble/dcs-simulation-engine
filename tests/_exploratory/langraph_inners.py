# type: ignore
"""Test that the process flow for langgraph is as expected

A minimal example with 3 agents with different jobs and private and public parts of their conversations
- agent_a: counts characters in users reply
- agent_b: characterizes sentiment in users reply
- agent_c: generates a reply using the sentiment from agent_b

- So no system prompts in state (just in their nodes)
- Artifacts between agents are put in structured keys (e.g., analysis_from_a: dict) rather than in messages.

Uses custom ChatOpenRouter which you can use just like ChatOpenAI:
model = ChatOpenRouter(model="deepseek/deepseek-chat-v3-0324", temperature=0.7)

Runs the graph and prints out the flow of messages and state so we can see what happened.
"""

from typing import Annotated, Any, Dict, Iterable, List, TypedDict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from dcs_simulation_engine.utils.chat import ChatOpenRouter

try:
    from langchain_core.messages import (
        AIMessage,
        BaseMessage,
        HumanMessage,
        SystemMessage,
    )
except Exception:  # fallback if langchain_core isn't available
    BaseMessage = object

    class HumanMessage:
        """Fallback HumanMessage class."""

        pass

    class AIMessage:
        """Fallback AIMessage class."""

        pass

    class SystemMessage:
        """Fallback SystemMessage class."""

        pass


class State(TypedDict, total=False):
    """State for the graph nodes."""

    messages: Annotated[List[Dict[str, Any]], add_messages]
    a_notes: Annotated[List[str], add_messages]
    b_notes: Annotated[List[str], add_messages]
    c_notes: Annotated[List[str], add_messages]
    analysis_from_a: Dict[str, Any]
    analysis_from_b: Dict[str, Any]
    final_reply: str


llm = ChatOpenRouter(model="openai/gpt-oss-20b:free", temperature=0.7)


try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
except Exception:
    HumanMessage = type("HumanMessage", (), {})
    AIMessage = type("AIMessage", (), {})
    SystemMessage = type("SystemMessage", (), {})


def _role_of(m: Any) -> str:
    if isinstance(m, HumanMessage):
        return "user"
    if isinstance(m, AIMessage):
        return "assistant"
    if isinstance(m, SystemMessage):
        return "system"
    if isinstance(m, dict):
        return m.get("role", "unknown")
    return getattr(m, "role", getattr(m, "type", "unknown"))


def _content_of(m: Any) -> str:
    if isinstance(m, (HumanMessage, AIMessage, SystemMessage)):
        return getattr(m, "content", "")
    if isinstance(m, dict):
        return m.get("content", "")
    return str(m)


def last_n_user_ai(msgs: Iterable[Any], n: int = 3) -> List[Any]:
    """Keep only user/assistant messages, supporting dicts *and* BaseMessage objs."""
    filtered = [m for m in msgs if _role_of(m) in ("user", "assistant")]
    return filtered[-n:]


A_SYS = "You are Agent A. Count characters in the latest user message. \
    Return only the integer count."
B_SYS = "You are Agent B. Read the user's latest message and give 1 word sentiment \
    label (eg. witty, friendly, grumpy)"
C_SYS = "You are Agent C. Draft a concise reply using the a tone that is the \
    OPPOSITE of Agent B's sentiment."


def agent_a_node(state: State) -> State:
    """Count characters in the latest user message."""
    view = last_n_user_ai(state.get("messages", []), n=1)
    prompt = ChatPromptTemplate.from_messages(
        [("system", A_SYS), MessagesPlaceholder("history")]
    )
    out = (prompt | llm).invoke({"history": view})
    raw = (out.content or "").strip()

    try:
        count = int("".join(ch for ch in raw if ch.isdigit()))
    except ValueError:
        count = None

    print("[agent_a] system_prompt ->", A_SYS)
    print("\n[agent_a] view ->", view)
    print("[agent_a] model_output ->", raw)
    print("[agent_a] parsed_char_count ->", count)

    return {
        "messages": [{"role": "assistant", "content": "A: processed"}],
        "a_notes": [f"raw_count:{raw}"],
        "analysis_from_a": {"char_count": count, "raw": raw},
    }


def agent_b_node(state: State) -> State:
    """Characterize sentiment in the latest user message."""
    view = last_n_user_ai(state.get("messages", []), n=3)
    prompt = ChatPromptTemplate.from_messages(
        [("system", B_SYS), MessagesPlaceholder("history")]
    )
    out = (prompt | llm).invoke({"history": view})
    text = (out.content or "").strip()

    print("[agent_b] system_prompt ->", B_SYS)
    print("\n[agent_b] view ->", view)
    print("[agent_b] model_output ->", text)
    print("[agent_b] sentiment_label ->", text)

    return {
        "b_notes": [f"raw_sentiment:{text}"],
        "analysis_from_b": {"sentiment": text, "explanation": text},
    }


def agent_c_node(state: State) -> State:
    """Generate a reply using the sentiment from agent_b."""
    view = last_n_user_ai(state.get("messages", []), n=3)
    sentiment = state.get("analysis_from_b", {}).get("sentiment", "unknown")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", C_SYS),
            ("system", f"Detected sentiment from Agent B: {sentiment}"),
            MessagesPlaceholder("history"),
        ]
    )
    out = (prompt | llm).invoke({"history": view})
    reply = (out.content or "").strip()

    print("[agent_c] system_prompt ->", C_SYS)
    print("\n[agent_c] view ->", view)
    print("[agent_c] sentiment_from_b ->", sentiment)
    print("[agent_c] model_output(final_reply) ->", reply)

    return {
        "messages": [{"role": "assistant", "content": reply}],
        "c_notes": [f"final_reply_len:{len(reply)}"],
        "final_reply": reply,
    }


graph = StateGraph(State)
graph.add_node("agent_a", agent_a_node)
graph.add_node("agent_b", agent_b_node)
graph.add_node("agent_c", agent_c_node)
graph.add_edge("__start__", "agent_a")
graph.add_edge("agent_a", "agent_b")
graph.add_edge("agent_b", "agent_c")
graph.add_edge("agent_c", "__end__")
compiled = graph.compile()


# @pytest.mark.experimental
def inspect_langgraph_flow():
    """Run the graph and print out the flow of messages and state so we can see."""
    initial_state: State = {
        "messages": [
            {
                "role": "user",
                "content": "Hey team—could you help me draft a short, friendly reply \
                    about meeting tomorrow at 2pm?",
            }
        ]
    }

    final_state: State = compiled.invoke(initial_state)

    print("\n=== Final State Snapshot ===")
    for i, m in enumerate(final_state.get("messages", []), 1):
        print(f"{i:02d}. [{_role_of(m)}] {_content_of(m)}")

    print("\nArtifacts:")
    print("analysis_from_a:", final_state.get("analysis_from_a"))
    print("analysis_from_b:", final_state.get("analysis_from_b"))
    print("\nFinal reply:", final_state.get("final_reply"))
