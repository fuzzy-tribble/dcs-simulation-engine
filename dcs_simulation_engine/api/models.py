"""Pydantic models (request/response schemas) for the API.

Defines the schema used by FastAPI to validate requests and shape
responses. These models also drive the generated OpenAPI spec.

Notes/Assumptions:
    - Keep API contracts stable; changes affect clients and OpenAPI docs.
    - Prefer explicit fields and examples to improve docs quality.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoadSimulationRequest(BaseModel):
    """Request body to load a simulation from a YAML definition.

    Attributes:
        simulation_path (str): Path to the YAML file describing the simulation.
    """

    simulation_path: str = Field(..., example="./sims/demo.yaml")


class LoadSimulationResponse(BaseModel):
    """Response body after loading a simulation.

    Attributes:
        sim_id (str): Unique ID of the simulation in the registry.
        graph_name (Optional[str]): Name of the compiled simulation graph, if available.
        simulation_name (Optional[str]): Human-friendly simulation name.
        characters (List[Dict[str, Any]]): Summary of characters.
    """

    sim_id: str
    graph_name: Optional[str] = None
    simulation_name: Optional[str] = None
    characters: List[Dict[str, Any]] = []


class CompileResponse(BaseModel):
    """Response after compiling a simulation graph.

    Attributes:
        compiled (bool): True if compilation succeeded.
    """

    compiled: bool = True


class StepRequest(BaseModel):
    """Request to advance the simulation one step.

    Attributes:
        user_input (Optional[str]): Optional user input to feed into this step.
    """

    user_input: Optional[str] = Field(
        None, description="Optional user input for this step"
    )


class Message(BaseModel):
    """Normalized message in the simulation transcript.

    Attributes:
        role (str): Role of the message author (e.g., 'system' or character UID).
        content (str): Message content text.
    """

    role: str
    content: str


class StepResponse(BaseModel):
    """Response after advancing the simulation one step.

    Attributes:
        messages (List[Message]): The most recent messages from the state/result.
        state (Dict[str, Any]): The current simulation state.
    """

    messages: List[Message] = []
    state: Dict[str, Any] = {}


class PlayRequest(BaseModel):
    """Request to run `play()` with a finite list of inputs.

    Attributes:
        inputs (List[str]): List of inputs to feed sequentially.
        max_steps (Optional[int]): Optional safety cap for maximum steps.
    """

    inputs: List[str] = Field(..., description="Finite list of inputs for play()")
    max_steps: Optional[int] = Field(
        None, description="Optional safety cap for maximum steps"
    )


class PlayResponse(BaseModel):
    """Response containing the final state after `play()`.

    Attributes:
        final_state (Dict[str, Any]): Final simulation state returned by `play()`.
    """

    final_state: Dict[str, Any]


class StateResponse(BaseModel):
    """Response with current simulation state and timestamps.

    Attributes:
        state (Dict[str, Any]): Current simulation state.
        start_timestamp (Optional[str]): Start timestamp (YYYYmmdd-HHMMSS) if available.
        end_timestamp (Optional[str]): End timestamp (YYYYmmdd-HHMMSS) if available.
    """

    state: Dict[str, Any]
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None


class SaveRequest(BaseModel):
    """Request to trigger saving/persisting outputs.

    Attributes:
        output_dir (Optional[str]): Optional directory hint (currently unused).
    """

    output_dir: Optional[str] = None


class SaveResponse(BaseModel):
    """Response containing file paths of saved outputs.

    Attributes:
        files (List[str]): A list of file paths produced by the simulation.
    """

    files: List[str] = []
