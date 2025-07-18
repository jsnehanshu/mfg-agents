# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from google.adk.agents import Agent, LlmAgent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from dotenv import load_dotenv
from .prompts import return_instructions_root

from datetime import date

from google.genai import types

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import load_artifacts

from .sub_agents import db_agent, rag_agent
from .sub_agents.bigquery.tools import (
    get_database_settings as get_bq_database_settings,
)
from .prompts import return_instructions_root
from .tools import call_db_agent

load_dotenv()


def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent."""

    # setting up database settings in session.state
    if "database_settings" not in callback_context.state:
        db_settings = dict()
        db_settings["use_database"] = "BigQuery"
        callback_context.state["all_db_settings"] = db_settings

    # setting up schema in instruction
    if callback_context.state["all_db_settings"]["use_database"] == "BigQuery":
        callback_context.state["database_settings"] = get_bq_database_settings()
        schema = callback_context.state["database_settings"]["bq_ddl_schema"]

        callback_context._invocation_context.agent.instruction = (
            return_instructions_root()
            + f"""

    --------- The BigQuery schema of the relevant data with a few sample rows. ---------
    {schema}

    """
        )

coordinator = LlmAgent(
    name="MDECoordinator",
    model="gemini-2.0-flash",
    # instruction="Route user requests: For MDE FAQs related questions use ask_rag_agent, bq_reader_agent for BQ table related questions",
    instruction= return_instructions_root(),
    description="Main MDE router.",
    # allow_transfer=True is often implicit with sub_agents in AutoFlow
    sub_agents=[rag_agent, db_agent],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)

root_agent = coordinator

# =================



# def setup_before_agent_call(callback_context: CallbackContext):
#     """Setup the agent."""

#     # setting up database settings in session.state
#     if "database_settings" not in callback_context.state:
#         db_settings = dict()
#         db_settings["use_database"] = "BigQuery"
#         callback_context.state["all_db_settings"] = db_settings

#     # setting up schema in instruction
#     if callback_context.state["all_db_settings"]["use_database"] == "BigQuery":
#         callback_context.state["database_settings"] = get_bq_database_settings()
#         schema = callback_context.state["database_settings"]["bq_ddl_schema"]

#         callback_context._invocation_context.agent.instruction = (
#             return_instructions_root()
#             + f"""

#     --------- The BigQuery schema of the relevant data with a few sample rows. ---------
#     {schema}

#     """
#         )


# root_agent = Agent(
#     model=os.getenv("ROOT_AGENT_MODEL"),
#     name="db_agent",
#     instruction=return_instructions_root(),
#     global_instruction=(
#         f"""
#         You are a Data Agent capable of reading data from Bigquery.
#         """
#     ),
#     sub_agents=[db_agent],
#     tools=[
#         call_db_agent,
#         load_artifacts,
#     ],
#     before_agent_callback=setup_before_agent_call,
#     generate_content_config=types.GenerateContentConfig(temperature=0.01),
# )