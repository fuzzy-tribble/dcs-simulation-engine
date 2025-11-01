from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from loguru import logger

NPC_MAX_RETRIES = 2  # keep or tweak
REQUIRED_FIX_TOKEN = "[fixed]"  # npc must include this to pass


def short_state(s: Dict[str, Any]) -> Dict[str, Any]:
    """Trim noisy fields for logging."""
    s = dict(s)
    msgs = s.get("messages")
    if isinstance(msgs, list):
        s["messages"] = [
            f"[{i}] {m[:80]}{'…' if len(m)>80 else ''}" for i, m in enumerate(msgs[-3:])
        ]
        s["messages_len"] = len(msgs)
    # avoid dumping huge npc_line text
    if "npc_line" in s and isinstance(s["npc_line"], str):
        s["npc_line"] = s["npc_line"][:120] + ("…" if len(s["npc_line"]) > 120 else "")
    return s


def log_node_io(name: str, before: Dict[str, Any], after: Dict[str, Any]):
    logger.debug(f"[NODE] {name} IN  => {short_state(before)}\n")
    logger.debug(f"[NODE] {name} OUT => {short_state(after)}\n")


def log_route(name: str, state: Dict[str, Any], dest: str):
    logger.debug(f"[ROUTE] {name} => {dest} | state: {short_state(state)}\n")


# ---------- Checkpointer ----------
def get_checkpointer():
    try:
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    except Exception:
        try:
            from langgraph.checkpoint.memory import InMemorySaver

            return InMemorySaver()
        except Exception:
            logger.warning("[CHECKPOINTER] Falling back to ephemeral (no persistence).")
            return None


CHECKPOINTER = get_checkpointer()


# ---------- State ----------
class GameState(TypedDict, total=False):
    messages: List[str]
    pc_retries: int
    npc_retries: int
    pc_valid: bool
    npc_valid: bool
    retry_actor: Optional[Literal["human", "agent"]]
    retry_reason: Optional[str]
    guidance: Optional[str]
    npc_line: Optional[str]
    end_game: bool
    end_game_reason: Optional[str]


# ---------- Game logic stubs ----------
def validate_pc(msg: str) -> tuple[bool, str]:
    ok = "attack" not in msg.lower()
    return ok, "" if ok else "PC action violates the 'no unprovoked attack' rule."


def scene_agent(messages: List[str], guidance: Optional[str]) -> str:
    # If guidance exists, agent "fixes" the reply by adding REQUIRED_FIX_TOKEN
    fix = f" {REQUIRED_FIX_TOKEN}" if guidance else ""
    tip = f" (incorporate: {guidance})" if guidance else ""
    return f"NPC (guard): 'State your business at the gate.'{tip}{fix}"


def validate_npc(text: str) -> tuple[bool, str]:
    # Fail until the agent includes REQUIRED_FIX_TOKEN in its reply
    ok = REQUIRED_FIX_TOKEN in text
    return ok, (
        "" if ok else f"NPC reply must include {REQUIRED_FIX_TOKEN} after feedback."
    )


# ---------- Nodes ----------
def pc_checkpoint(s: GameState) -> GameState:
    _in = deepcopy(s)
    valid, reason = validate_pc(s["messages"][-1])
    out: GameState
    if valid:
        out = {"pc_valid": True, "retry_actor": None, "retry_reason": None}
    else:
        out = {
            "pc_valid": False,
            "pc_retries": s.get("pc_retries", 0) + 1,
            "retry_actor": "human",
            "retry_reason": reason,
        }
    log_node_io("pc_checkpoint", _in, out)
    return out


def advance_scene(s: GameState) -> GameState:
    _in = deepcopy(s)
    npc = scene_agent(s["messages"], s.get("guidance"))
    out = {"messages": s["messages"] + [npc], "guidance": None, "npc_line": npc}
    log_node_io("advance_scene", _in, out)
    return out


def npc_checkpoint(s: GameState) -> GameState:
    _in = deepcopy(s)
    valid, reason = validate_npc(s.get("npc_line") or "")
    out: GameState
    if valid:
        out = {"npc_valid": True, "retry_actor": None, "retry_reason": None}
    else:
        out = {
            "npc_valid": False,
            "npc_retries": s.get("npc_retries", 0) + 1,
            "retry_actor": "agent",
            "retry_reason": reason,
        }
    log_node_io("npc_checkpoint", _in, out)
    return out


def retry(s: GameState) -> GameState:
    _in = deepcopy(s)
    who, why = s.get("retry_actor"), s.get("retry_reason")
    if who == "human":
        payload = {
            "type": "retry_needed",
            "reason": why,
            "prompt": "Revise your action:",
        }
        logger.debug(f"[INTERRUPT] retry(human) => {payload}\n")
        revised = interrupt(payload)
        out = {"messages": s["messages"] + [revised]}
    elif who == "agent":
        out = {"guidance": f"Fix this: {why}"}
    else:
        out = {}
    log_node_io("retry", _in, out)
    return out


def end_game(s: GameState) -> GameState:
    _in = deepcopy(s)
    reason = s.get("retry_reason") or s.get("end_game_reason") or "Reached max retries."
    out = {"end_game": True, "end_game_reason": reason}
    log_node_io("end_game", _in, out)
    return out


# ---------- Routers ----------
def route_from_pc(s: GameState) -> Literal["advance_scene", "retry", "end_game"]:
    if s.get("pc_valid"):
        dest = "advance_scene"
    else:
        dest = "retry" if s.get("pc_retries", 0) < 3 else "end_game"
    log_route("route_from_pc", s, dest)
    return dest


def route_from_retry(s: GameState) -> Literal["pc_checkpoint", "advance_scene"]:
    dest = "pc_checkpoint" if s.get("retry_actor") == "human" else "advance_scene"
    log_route("route_from_retry", s, dest)
    return dest


def route_from_npc(s: GameState) -> Literal["END", "retry", "end_game"]:
    if s.get("npc_valid"):
        dest = "END"
    else:
        dest = "retry" if s.get("npc_retries", 0) < 2 else "end_game"
    log_route("route_from_npc", s, dest)
    return dest


# ---------- Build graph ----------
builder = StateGraph(GameState)
for n, fn in [
    ("pc_checkpoint", pc_checkpoint),
    ("advance_scene", advance_scene),
    ("npc_checkpoint", npc_checkpoint),
    ("retry", retry),
    ("end_game", end_game),
]:
    builder.add_node(n, fn)

builder.add_edge(START, "pc_checkpoint")
builder.add_conditional_edges(
    "pc_checkpoint",
    route_from_pc,
    {
        "advance_scene": "advance_scene",
        "retry": "retry",
        "end_game": "end_game",
    },
)
builder.add_edge("advance_scene", "npc_checkpoint")
builder.add_conditional_edges(
    "npc_checkpoint",
    route_from_npc,
    {
        "END": END,
        "retry": "retry",
        "end_game": "end_game",
    },
)
builder.add_conditional_edges(
    "retry",
    route_from_retry,
    {
        "pc_checkpoint": "pc_checkpoint",
        "advance_scene": "advance_scene",
    },
)
builder.add_edge("end_game", END)

graph = builder.compile(checkpointer=CHECKPOINTER)
logger.debug(
    "[GRAPH] Compiled with checkpointer: {}\n".format(
        type(CHECKPOINTER).__name__ if CHECKPOINTER else "None"
    )
)
# print the dict output of the graph for debugging
cfg = graph.get_graph()
logger.debug(f"[GRAPH] Definition: {cfg}\n")

# ---------- CLI using invoke() + clear interrupt prompt ----------
if __name__ == "__main__":
    THREAD_ID = f"game-{uuid4()}"
    CONFIG = {"configurable": {"thread_id": THREAD_ID}}
    logger.debug(f"[SESSION] thread_id={THREAD_ID}\n")

    print(
        "Enter your first action (e.g., 'I attack the guard' or 'I greet the guard'):"
    )
    state: GameState = {"messages": [input("> ").strip()]}

    while True:
        out: GameState = graph.invoke(state, config=CONFIG)
        logger.debug(f"[INVOKE] output state => {short_state(out)}\n")

        # 1) INTERRUPT: payloads live in out["__interrupt__"]
        intrs = out.get("__interrupt__") or []
        if intrs:
            # usually one interrupt; grab its value dict
            payload = getattr(intrs[0], "value", None) if intrs else None
            print("\n-- CHECKPOINT FAILED --")
            if isinstance(payload, dict) and payload.get("reason"):
                print("Reason:", payload["reason"])
            print((payload or {}).get("prompt", "Revise your action:"))
            reply = input("> ").strip()

            # Resume at the same node: pass only the user's new message
            state = {"messages": [reply]}
            continue

        # 2) Terminal failure
        if out.get("end_game"):
            print("\n-- GAME OVER --")
            print("Reason:", out.get("end_game_reason"))
            break

        # 3) Success path (NPC reply came back from advance_scene)
        npc = out.get("npc_line")
        if npc:
            print("\n" + npc)
            break

        # 4) Fallback (shouldn't happen; keeps loop safe)
        print("\n(Reached END, but no NPC line found.)")
        break
