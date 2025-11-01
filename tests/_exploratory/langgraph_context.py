from langgraph.graph import END, StateGraph
from langgraph.runtime import Runtime  # <-- new
from typing_extensions import TypedDict


class MyState(TypedDict):
    count: int
    result: str


class MyContext(TypedDict):
    user_name: str
    db_conn: object  # or any tool/service


def my_node(state: MyState, runtime: Runtime[MyContext]) -> dict:
    # access static context
    name = runtime.context["user_name"]
    # do something with state + context
    return {
        "count": state["count"] + 1,
        "result": f"Hello {name}, count is {state['count'] + 1}",
    }


graph = StateGraph(state_schema=MyState, context_schema=MyContext)
graph.add_node("node1", my_node)
graph.set_entry_point("node1")
graph.add_edge("node1", END)
app = graph.compile()

context = MyContext(user_name="Alice", db_conn=None)

output = app.invoke(
    {"count": 0, "result": ""},  # input state
    context=context,
)
print(output)
