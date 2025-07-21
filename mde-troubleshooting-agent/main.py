import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ADK Runner and Session Imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

# Import your agent from your package
from mde_troubleshooting_agent.agent import root_agent as agent

# --- Initialize the ADK Runner and Session Service ---
session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="mde_troubleshooting_app",
    session_service=session_service,
)
# ---------------------------------------------------

# Initialize the FastAPI app
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the API request model
class TroubleshootRequest(BaseModel):
    alertId: str
    query: str | None = None

# Define the API endpoint as a proper async function
@app.post("/troubleshoot")
async def troubleshoot_alert(request: TroubleshootRequest):
    if not agent:
        return {"response": "Agent not loaded. Please check the backend logs for errors."}

    print(f"Received request for alert: {request.alertId}, query: {request.query}")
    
    session_id = request.alertId
    user_id = f"user_{session_id}"

    try:
        # Correctly check for and create the session if it doesn't exist
        try:
            await session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
        except ValueError:
            await session_service.create_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)

        if not request.query:
            prompt = f"Provide an initial analysis and recommended actions for the alert with ID: {request.alertId}"
        else:
            prompt = f"Regarding the alert '{request.alertId}', the user is asking: {request.query}"

        content = types.Content(role='user', parts=[types.Part(text=prompt)])

        # --- THE FIX: Use runner.run_async() and process the event stream ---
        final_response = "Agent did not produce a final response."
        
        # We now iterate through the asynchronous generator provided by run_async
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                final_response = event.content.parts[0].text
                break # Exit the loop once we have the final answer
        
        return {"response": final_response}
        # --------------------------------------------------------------------

    except Exception as e:
        print(f"Error invoking agent runner: {e}")
        return {"response": f"Sorry, a critical error occurred: {e}"}