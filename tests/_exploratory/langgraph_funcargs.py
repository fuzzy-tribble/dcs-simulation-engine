# langgraph_func_accepts_demo.py

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

START = "__start__"
END = "__end__"


# --- Graph 1: node does NOT accept injected args (func_accepts = {}) ---
def step(state):  # plain function
    return state + " world"


g1 = StateGraph(str)
g1.add_node("hello", step)
g1.add_edge(START, "hello")
g1.add_edge("hello", END)
cg1 = g1.compile()
print(f"graph 1 func_accepts: {cg1.get_graph()}")


# --- Graph 2: node declares it accepts `config` (func_accepts has 'config') ---
def step_with_config(state, *, config: RunnableConfig):
    # RunnableConfig is a Mapping; `config["configurable"]` is where your own fields typically go.
    run_id = config.get("configurable", {}).get("run_id")
    return f"{state} world (run_id={run_id})"


g2 = StateGraph(str)
g2.add_node("hello", step_with_config)
g2.add_edge(START, "hello")
g2.add_edge("hello", END)
cg2 = g2.compile()
print(f"graph 2 func_accepts: {cg2.get_graph()}")
