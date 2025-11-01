"""Builds a basic langgraph StateGraph with a single actor node."""

from typing import Annotated

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from loguru import logger
from typing_extensions import TypedDict

from dcs_simulation_engine.utils.chat import ChatOpenRouter


class State(TypedDict):
    """State schema for the graph."""

    messages: Annotated[list, add_messages]


def build_graph() -> CompiledStateGraph:
    """Builds and returns the StateGraph."""
    graph_builder = StateGraph(State)

    actor_model_id = "deepseek/deepseek-chat-v3-0324"

    def actor_node(state: State) -> State:
        """Actor node replies in the /type of the character."""
        logger.info("Calling actor with state: {}", state)
        llm: BaseChatModel = ChatOpenRouter(model=actor_model_id)
        response = llm.invoke(state["messages"])

        logger.debug("Actor response: {}", response)
        return {"messages": [response]}

    # build graph ENTRY --> actor --> EXIT
    graph_builder.add_node("actor", actor_node)
    graph_builder.add_edge(START, "actor")
    graph_builder.add_edge("actor", END)
    compiled_graph = graph_builder.compile()

    graph = compiled_graph.get_graph()
    logger.debug("Graph built: {}", graph)
    logger.debug("Graph ascii: {}", graph.draw_ascii())
    return compiled_graph
