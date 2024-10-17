from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
from dotenv import load_dotenv
import asyncio
import time

# Load environment variables
load_dotenv()

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config, load_config
from backend.swarm.agent import Agent
from backend.swarm.swarm import Swarm, Response
from backend.jira_integration import (
    fetch_epics, fetch_stories, fetch_subtasks, update_subtask,
    JiraIntegrationError
)
import logging
import json
from functools import lru_cache, wraps
from slowapi import Limiter
from slowapi.util import get_remote_address

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

def rate_limit(limit_string):
    def decorator(func):
        @limiter.limit(limit_string)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Load configuration
config = load_config("config.json")

# Define tools as named functions
def transfer_to_technical_requirements():
    """Transfer to the Technical Requirements Agent."""
    return "HANDOFF:Technical Requirements Agent"

def transfer_to_ux():
    """Transfer to the User Experience Agent."""
    return "HANDOFF:User Experience Agent"

def transfer_to_qa():
    """Transfer to the Quality Assurance Agent."""
    return "HANDOFF:Quality Assurance Agent"

def transfer_to_stakeholder_liaison():
    """Transfer to the Stakeholder Liaison Agent."""
    return "HANDOFF:Stakeholder Liaison Agent"

def transfer_to_master():
    """Transfer back to the Master Agent."""
    return "HANDOFF:Master Agent"

# Create a tools map
tools_map = {
    "transfer_to_technical_requirements": transfer_to_technical_requirements,
    "transfer_to_ux": transfer_to_ux,
    "transfer_to_qa": transfer_to_qa,
    "transfer_to_stakeholder_liaison": transfer_to_stakeholder_liaison,
    "transfer_to_master": transfer_to_master,
}

# Create agents based on configuration
agents = [
    Agent(
        name=agent_config.name,
        instructions=agent_config.instructions,
        tools=[tools_map[tool] for tool in agent_config.tools if tool in tools_map],
        model=config.openai_model
    )
    for agent_config in config.agents
]

# Create the swarm
swarm = Swarm(agents)

class UserStory(BaseModel):
    content: str
    epic_context: Optional[str] = None
    story_context: Optional[str] = None

class OptimizedUserStory(BaseModel):
    original: str
    optimized: str
    agent_interactions: List[dict]
    model: str
    performance_metrics: Dict[str, Any]

class OptimizationStatus(BaseModel):
    total_stories: int
    processed_stories: int
    status: str

optimization_status = OptimizationStatus(total_stories=0, processed_stories=0, status="idle")
stop_optimization = False

def optimize_story_logic(content: str, epic_context: Optional[str] = None, story_context: Optional[str] = None):
    """
    Core logic for optimizing a user story.
    This function should be used by both API endpoints.
    """
    async def optimize():
        logger.info(f"Starting optimization for story: {content[:50] if isinstance(content, str) else 'None'}...")
        start_time = time.time()
        try:
            # Context Analysis Step
            context_analysis = await swarm.analyze_context(content, epic_context, story_context)
            logger.info(f"Context analysis: {context_analysis[:100] if isinstance(context_analysis, str) else 'None'}...")

            result = await swarm.process_message(content, context_analysis)
            end_time = time.time()
            logger.info(f"Optimization completed in {end_time - start_time:.2f} seconds")
            logger.info(f"Optimized story: {result.optimized[:50] if isinstance(result.optimized, str) else 'None'}...")
            return result
        except Exception as e:
            logger.error(f"Error during optimization: {str(e)}")
            raise
    return optimize

@app.post("/optimize_story", response_model=OptimizedUserStory)
@rate_limit("5/minute")
async def optimize_story(user_story: UserStory, request: Request):
    try:
        logger.info(f"Received request to optimize story: {user_story.content}")
        optimize_func = optimize_story_logic(user_story.content, user_story.epic_context, user_story.story_context)
        result = await optimize_func()
        logger.info(f"Optimized story: {result.optimized}")
        logger.info(f"Performance metrics: {result.performance_metrics}")
        
        return OptimizedUserStory(
            original=user_story.content,
            optimized=result.optimized,
            agent_interactions=result.agent_interactions,
            model=config.openai_model,
            performance_metrics=result.performance_metrics
        )
    except Exception as e:
        logger.error(f"Error occurred while optimizing story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while optimizing the story: {str(e)}")

@app.post("/optimize_jira_stories")
@rate_limit("1/minute")
async def optimize_jira_stories(background_tasks: BackgroundTasks, request: Request):
    global stop_optimization
    stop_optimization = False

    async def process_jira_stories():
        global optimization_status, stop_optimization
        optimization_status.status = "processing"
        
        try:
            epics = fetch_epics()
            optimization_status.total_stories = sum(len(fetch_subtasks(epic['key'])) for epic in epics)
            optimization_status.processed_stories = 0
            
            logger.info(f"Starting optimization of {optimization_status.total_stories} Jira stories")
            
            for epic in epics:
                if stop_optimization:
                    logger.info("Optimization process stopped by user")
                    break

                epic_key = epic['key']
                epic_description = epic['fields'].get('description', '')
                logger.info(f"Processing epic: {epic_key} - {epic['fields'].get('summary', 'No summary')}")
                
                stories = fetch_stories(epic_key)
                
                for story in stories:
                    if stop_optimization:
                        logger.info("Optimization process stopped by user")
                        break

                    story_key = story['key']
                    story_description = story['fields'].get('description', '')
                    logger.info(f"Processing story: {story_key} - {story['fields'].get('summary', 'No summary')}")
                    
                    subtasks = fetch_subtasks(story_key)
                    
                    for subtask in subtasks:
                        if stop_optimization:
                            logger.info("Optimization process stopped by user")
                            break

                        subtask_key = subtask['key']
                        subtask_description = subtask['fields'].get('description', '')
                        
                        logger.info(f"Optimizing subtask: {subtask_key} - {subtask['fields'].get('summary', 'No summary')}")
                        
                        optimize_func = optimize_story_logic(subtask_description, epic_description, story_description)
                        result = await optimize_func()
                        
                        update_subtask(subtask_key, result.optimized)
                        
                        optimization_status.processed_stories += 1
                        logger.info(f"Processed {optimization_status.processed_stories}/{optimization_status.total_stories} subtasks")
            
            if not stop_optimization:
                optimization_status.status = "completed"
                logger.info("Jira story optimization completed")
            else:
                optimization_status.status = "stopped"
        except JiraIntegrationError as e:
            logger.error(f"Jira integration error: {str(e)}")
            optimization_status.status = "failed"
        except Exception as e:
            logger.error(f"Unexpected error during Jira story optimization: {str(e)}", exc_info=True)
            optimization_status.status = "failed"

    background_tasks.add_task(process_jira_stories)
    return {"message": "Jira story optimization started in the background"}

@app.post("/stop_optimization")
async def stop_optimization_process():
    global stop_optimization
    stop_optimization = True
    return {"message": "Optimization process stop signal sent"}

@app.get("/optimization_status", response_model=OptimizationStatus)
async def get_optimization_status():
    logger.info(f"Current optimization status: {optimization_status}")
    return optimization_status

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the application")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
