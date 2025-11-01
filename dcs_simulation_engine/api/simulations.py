"""Simulation-related API routes.

This router exposes endpoints to load, compile, step through, play, inspect,
save, and delete simulations. It normalizes messages for consistent responses.

Notes/Assumptions:
    - `SimulationManager.step()` returns a dict that may include "messages".
    - `SimulationManager.play()` returns a final state; messages reside in sim.state.
    - For one-off user input with step(): we simulate a single-turn play() call
      if `user_input` is provided (adjust if your engine supports direct input).
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from dcs_simulation_engine.api.deps import get_manager
from dcs_simulation_engine.api.models import (
    CompileResponse,
    LoadSimulationRequest,
    LoadSimulationResponse,
    Message,
    PlayRequest,
    PlayResponse,
    SaveRequest,
    SaveResponse,
    StateResponse,
    StepRequest,
    StepResponse,
)
from dcs_simulation_engine.api.services.registry import SimRegistry, get_registry

router = APIRouter()


@router.post(
    "/simulations/load",
    response_model=LoadSimulationResponse,
    summary="Load a simulation from YAML",
)
def load_simulation(
    payload: LoadSimulationRequest, registry: SimRegistry = Depends(get_registry)
) -> LoadSimulationResponse:
    """Create and register a simulation instance.

    Args:
        payload (LoadSimulationRequest): Path to the YAML descriptor.
        registry (SimRegistry): In-memory registry dependency.

    Returns:
        LoadSimulationResponse: IDs and summary info (graph, name, characters).

    Raises:
        HTTPException: If loading fails (bad file, parse error, etc.).
    """
    try:
        sim_id, sim = registry.create_from_yaml(payload.simulation_path)
    except Exception as e:
        logger.exception("Failed to load simulation")
        raise HTTPException(status_code=400, detail=str(e))

    # Mirror some CLI outputs for convenience in clients.
    char_data: List[Dict[str, Any]] = []
    for ch in getattr(sim, "characters", []):
        char_data.append(
            {
                "uid": getattr(ch, "uid", None),
                "short_description": getattr(ch, "short_description", None),
                "abilities": getattr(ch, "abilities", None),
            }
        )

    return LoadSimulationResponse(
        sim_id=sim_id,
        graph_name=getattr(sim.sim_graph, "name", None),
        simulation_name=getattr(sim, "name", None),
        characters=char_data,
    )


@router.post(
    "/simulations/{sim_id}/compile",
    response_model=CompileResponse,
    summary="Compile the simulation graph",
)
def compile_simulation(sim_id: str, sim=Depends(get_manager)) -> CompileResponse:
    """Compile the simulation graph for the given simulation.

    Args:
        sim_id (str): ID of the simulation to compile.
        sim (SimulationManager): Resolved simulation instance.

    Returns:
        CompileResponse: Compilation status.

    Raises:
        HTTPException: If compilation fails due to invalid graph, etc.
    """
    try:
        sim.sim_graph.compile()
        return CompileResponse(compiled=True)
    except Exception as e:
        logger.exception("Compile failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/simulations/{sim_id}/step",
    response_model=StepResponse,
    summary="Advance one step; optionally pass user input",
)
def step(sim_id: str, body: StepRequest, sim=Depends(get_manager)) -> StepResponse:
    """Advance the simulation one step.

    If `user_input` is provided, this function simulates a single-turn `play()`
    by providing exactly one input and limiting steps to 1 (see Note below).

    Args:
        sim_id (str): ID of the simulation.
        body (StepRequest): Optional user input to include.
        sim (SimulationManager): Resolved simulation instance.

    Returns:
        StepResponse: Normalized messages and the latest state snapshot.

    Raises:
        HTTPException: If stepping fails for any reason.

    Notes:
        - Assumption: Your engine does not take direct input in `step()`.
          If it *does*, replace the one-off `play()` behavior with native input.
    """
    try:
        if body.user_input:
            # One-off input via play() with a single step cap.
            provided = [body.user_input]
            it = iter(provided)

            def one_off_input() -> str:
                try:
                    return next(it)
                except StopIteration:
                    return ""

            sim.play(input_provider=one_off_input, max_steps=1)
            state = getattr(sim, "state", {}) or {}
            msgs = state.get("messages", [])
        else:
            res = sim.step()
            state = getattr(sim, "state", {}) or {}
            msgs = res.get("messages", state.get("messages", []))

        norm = [
            Message(
                role=getattr(m, "role", "system"),
                content=getattr(m, "content", str(m)),
            )
            for m in msgs
        ]
        return StepResponse(messages=norm, state=state)
    except Exception as e:
        logger.exception("Step failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/simulations/{sim_id}/play",
    response_model=PlayResponse,
    summary="Run play() with a finite list of inputs",
)
def play(sim_id: str, body: PlayRequest, sim=Depends(get_manager)) -> PlayResponse:
    """Run the simulation's `play()` loop with provided inputs.

    Args:
        sim_id (str): ID of the simulation.
        body (PlayRequest): A finite list of inputs and an optional step cap.
        sim (SimulationManager): Resolved simulation instance.

    Returns:
        PlayResponse: The final state returned by `play()`.

    Raises:
        HTTPException: If `play()` fails.
    """
    try:
        inputs = iter(body.inputs)

        def provider() -> str:
            try:
                return next(inputs)
            except StopIteration:
                # Return empty to let engine conclude gracefully if it supports it.
                return ""

        final_state = sim.play(input_provider=provider, max_steps=body.max_steps)
        return PlayResponse(final_state=final_state)
    except Exception as e:
        logger.exception("Play failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/simulations/{sim_id}/state",
    response_model=StateResponse,
    summary="Get current simulation state",
)
def get_state(sim_id: str, sim=Depends(get_manager)) -> StateResponse:
    """Fetch the current simulation state and timestamps.

    Args:
        sim_id (str): ID of the simulation.
        sim (SimulationManager): Resolved simulation instance.

    Returns:
        StateResponse: Current state plus optional start/end timestamps.
    """
    st = getattr(sim, "state", {}) or {}
    start_ts = getattr(sim, "start_ts", None)
    end_ts = getattr(sim, "end_ts", None)
    return StateResponse(
        state=st,
        start_timestamp=start_ts.strftime("%Y%m%d-%H%M%S") if start_ts else None,
        end_timestamp=end_ts.strftime("%Y%m%d-%H%M%S") if end_ts else None,
    )


@router.post(
    "/simulations/{sim_id}/save",
    response_model=SaveResponse,
    summary="Persist any outputs; returns file paths if available",
)
def save_outputs(sim_id: str, _: SaveRequest, sim=Depends(get_manager)) -> SaveResponse:
    """Return any file paths that the simulation produced.

    Args:
        sim_id (str): ID of the simulation.
        _ (SaveRequest): Placeholder for future options.
        sim (SimulationManager): Resolved simulation instance.

    Returns:
        SaveResponse: File paths discovered in the sim state.

    Notes:
        - Currently surfaces `sim.state['output_path']` if present.
        - Extend to trigger materialization/export if your engine supports it.
    """
    st = getattr(sim, "state", {}) or {}
    files: List[str] = []
    if "output_path" in st and st["output_path"]:
        files.append(st["output_path"])
    return SaveResponse(files=files)


@router.delete(
    "/simulations/{sim_id}",
    status_code=204,
    summary="Dispose a simulation from the registry",
)
def delete_simulation(
    sim_id: str, registry: SimRegistry = Depends(get_registry)
) -> None:
    """Remove a simulation from the in-memory registry.

    Args:
        sim_id (str): ID of the simulation to remove.
        registry (SimRegistry): Registry dependency.
    """
    registry.remove(sim_id)
    return
