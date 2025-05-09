"""This module contains FastAPI routers for chatur endpoints."""

# Standard Library
import os

# Third Party Library
import logfire

from fastapi import APIRouter, Depends
from fastapi.requests import Request

# Package Library
from chaturai.chatur.schemas import ChaturFlowResults, ChaturQueryUnion
from chaturai.config import Settings
from chaturai.graphs.chatur import chatur
from chaturai.utils.chat import AsyncChatSessionManager, get_chat_session_manager

TAG_METADATA = {
    "description": "_Requires API key._ Chatur automation flow",
    "name": "Chatur",
}
router = APIRouter(tags=[TAG_METADATA["name"]])

GOOGLE_CREDENTIALS_FP = os.getenv("PATHS_GOOGLE_CREDENTIALS")
TEXT_GENERATION_GEMINI = Settings.TEXT_GENERATION_GEMINI


@router.post("/chatur-flow", response_model=ChaturFlowResults)
@logfire.instrument("Running Chatur flow endpoint...")
async def chatur_flow(
    chatur_query: ChaturQueryUnion,
    request: Request,
    csm: AsyncChatSessionManager = Depends(get_chat_session_manager),
    generate_graph_diagrams: bool = False,
    reset_chat_and_graph_state: bool = False,
) -> ChaturFlowResults:
    """Chatur flow.

    Parameters
    ----------
    \n\tchatur_query
    \t\tThe query object.
    \n\trequest
    \t\tThe FastAPI request object.
    \n\tcsm
    \t\tAn async chat session manager that manages the chat sessions for each user.
    \n\tgenerate_graph_diagrams
    \t\tSpecifies whether to generate graph diagrams for the endpoint.
    \n\treset_chat_and_graph_state
    \t\tSpecifies whether to reset the chat session and the graph state for the user.
    \t\tThis can be used to clear the chat history and graph state, effectively
    \t\tstarting a completely new session. This is useful for testing or debugging
    \t\tpurposes.

    Returns
    -------
    \n\tChaturFlowResults
    \t\tThe Chatur response.
    """

    return await chatur(
        chatur_query=chatur_query,
        csm=csm,
        generate_graph_diagrams=generate_graph_diagrams,
        redis_client=request.app.state.redis,
        reset_chat_and_graph_state=reset_chat_and_graph_state,
    )
