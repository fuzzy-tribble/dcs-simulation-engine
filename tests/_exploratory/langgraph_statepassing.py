from operator import add
from typing import List

from langgraph.graph import StateGraph
from typing_extensions import Annotated, TypedDict


class Context(TypedDict):
    pass


# 1) Public input/output schemas (what callers see)
class PublicIn(TypedDict):
    question: str


class PublicOut(TypedDict):
    answer: str
    # show a global counter publicly too:
    turns: int


# 2) Overall/internal schema = everything the graph may use
class OverallState(TypedDict):
    # public channels
    question: str
    answer: str
    turns: int
    # private channels (NOT in PublicIn/Out)
    search_query: str
    docs: Annotated[List[str], add]  # reducer: append docs across nodes


# --- Nodes ---


def gen_query(state: OverallState) -> dict:
    # writes a PRIVATE key
    return {"search_query": f"{state['question']} english meaning"}


def retrieve_docs(state: OverallState) -> dict:
    # reads a PRIVATE key and writes another PRIVATE key (with reducer)
    return {"docs": [f"Result for {state['search_query']}"]}


def synthesize(state: OverallState) -> dict:
    # reads PRIVATE docs, writes PUBLIC answer,
    # and also updates a GLOBAL (public) counter
    return {
        "answer": f"Based on {len(state.get('docs', []))} docs.",
        "turns": state.get("turns", 0) + 1,  # <-- global/public state update
    }


# --- Graph ---

graph = StateGraph(
    state_schema=OverallState,
    context_schema=Context,  # TODO: add a context schema example
    input_schema=PublicIn,  # callers pass only PublicIn
    output_schema=PublicOut,  # callers receive only PublicOut
)

graph.add_node("gen_query", gen_query)
graph.add_node("retrieve_docs", retrieve_docs)
graph.add_node("synthesize", synthesize)
graph.add_edge("gen_query", "retrieve_docs")
graph.add_edge("retrieve_docs", "synthesize")
graph.set_entry_point("gen_query")
graph.set_finish_point("synthesize")

app = graph.compile()

# Callers provide only PublicIn; internal/private keys never appear in the result:
out = app.invoke({"question": "What is LangGraph?"}, context=None)
# -> {'answer': 'Based on 1 docs.', 'turns': 1}
print(out)
