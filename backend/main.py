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

# Load environment variables from the correct location
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config, load_config
from backend.swarm.agent import Agent
from backend.swarm.swarm import Swarm
from backend.jira_integration import process_jira_subtasks  # Import the Jira integration function
import logging
import json
from functools import lru_cache, wraps
from slowapi import Limiter
from slowapi.util import get_remote_address

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Add a stream handler to also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

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
config = load_config("config.json")  # You can implement this function to load from a file

# Create agents based on configuration
agents = [
    Agent(
        name=agent_config.name,
        instructions=agent_config.instructions,
        tools=[config.tools[tool] for tool in agent_config.tools],
        model=config.openai_model
    )
    for agent_config in config.agents
]

# Create the swarm
swarm = Swarm(agents, config)

# Expose swarm creation function for testing
def create_swarm():
    return Swarm(agents, config)

class UserStory(BaseModel):
    content: str

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

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    logger.critical("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is not set")

async def optimize_story_logic(content: str):
    """
    Core logic for optimizing a user story.
    This function should be used by both API endpoints.
    """
    print(f"Starting optimization for story: {content[:50]}...")
    start_time = time.time()
    try:
        # Context Analysis Step
        context_analysis = await swarm.analyze_context(content)
        print(f"Context analysis: {context_analysis}")

        # Triage Step
        relevant_agents = await swarm.triage_user_story(content, context_analysis)
        print(f"Relevant agents: {', '.join(relevant_agents)}")

        result = await swarm.process_message(content, config.tools, context_analysis)
        end_time = time.time()
        print(f"Optimization completed in {end_time - start_time:.2f} seconds")
        print(f"Optimized story: {result[0][:50]}...")
        return result
    except Exception as e:
        print(f"Error during optimization: {str(e)}")
        raise

@app.post("/optimize_story", response_model=OptimizedUserStory)
@rate_limit("5/minute")
async def optimize_story(user_story: UserStory, request: Request):
    try:
        logger.info(f"Received request to optimize story: {user_story.content}")
        optimized, agent_interactions, performance_metrics = await optimize_story_logic(user_story.content)
        logger.info(f"Optimized story: {optimized}")
        logger.info(f"Performance metrics: {performance_metrics}")
        
        # Ensure agent_interactions include agent_name and decision
        for interaction in agent_interactions:
            if "role" in interaction and interaction["role"] == "assistant":
                interaction["agent_name"] = interaction.get("agent_name", "Unknown Agent")
                interaction["decision"] = interaction.get("decision", "No decision recorded")
        
        # Optionally adjust max_iterations or early_stopping_threshold based on performance_metrics
        if performance_metrics["quality_score"] < 0.6 and swarm.max_iterations < 10:
            swarm.update_max_iterations(swarm.max_iterations + 1)
            logger.info(f"Increased max iterations to {swarm.max_iterations}")
        elif performance_metrics["quality_score"] > 0.9 and swarm.max_iterations > 3:
            swarm.update_max_iterations(swarm.max_iterations - 1)
            logger.info(f"Decreased max iterations to {swarm.max_iterations}")
        
        # Log the final user story for easy access and integration
        logger.info(f"Final User Story for Jira Integration:\n{optimized}")
        
        return OptimizedUserStory(
            original=user_story.content,
            optimized=optimized,
            agent_interactions=agent_interactions,
            model=config.openai_model,
            performance_metrics=performance_metrics
        )
    except Exception as e:
        logger.error(f"Error occurred while optimizing story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while optimizing the story: {str(e)}")

# Implement background processing for multiple user stories
async def process_stories_background(stories: List[str], swarm: Swarm = swarm):
    global optimization_status
    optimization_status.total_stories = len(stories)
    optimization_status.processed_stories = 0
    optimization_status.status = "processing"
    
    print(f"Starting to process {len(stories)} stories")
    start_time = time.time()

    for i, story in enumerate(stories, 1):
        print(f"Processing story {i}/{len(stories)}")
        try:
            optimized, agent_interactions, performance_metrics = await optimize_story_logic(story)
            optimization_status.processed_stories += 1
            elapsed_time = time.time() - start_time
            print(f"Processed story {i}/{len(stories)} - Total stories: {optimization_status.processed_stories}/{optimization_status.total_stories}")
            print(f"Time elapsed: {elapsed_time:.2f} seconds")
            print(f"Average time per story: {elapsed_time / optimization_status.processed_stories:.2f} seconds")
            
            print(f"Story {i}:")
            print(f"  Original: {story[:50]}...")
            print(f"  Optimized: {optimized[:50]}...")
            print(f"  Agents involved: {', '.join(interaction['agent_name'] for interaction in agent_interactions if 'agent_name' in interaction)}")
            print(f"  Quality score: {performance_metrics['quality_score']:.2f}")
        except Exception as e:
            print(f"Error processing story {i}: {str(e)}")

    optimization_status.status = "completed"
    total_time = time.time() - start_time
    print(f"All stories processed in {total_time:.2f} seconds")
    print(f"Final average time per story: {total_time / len(stories):.2f} seconds")

@app.post("/process_all_stories")
@rate_limit("2/minute")
async def process_stories(background_tasks: BackgroundTasks, stories: List[str], request: Request):
    if optimization_status.status == "processing":
        logger.warning("Attempted to start optimization while another is in progress")
        raise HTTPException(status_code=400, detail="Optimization already in progress")
    
    logger.info(f"Starting background processing of {len(stories)} stories")
    background_tasks.add_task(process_stories_background, stories)
    return {"message": "Story optimization started in the background"}

@app.get("/optimization_status", response_model=OptimizationStatus)
async def get_optimization_status():
    logger.info(f"Current optimization status: {optimization_status}")
    return optimization_status

# New endpoint for processing Jira Sub-tasks
@app.post("/process_jira_subtasks")
@rate_limit("1/minute")
async def process_jira_subtasks_endpoint(background_tasks: BackgroundTasks, request: Request):
    if optimization_status.status == "processing":
        logger.warning("Attempted to start Jira optimization while another process is in progress")
        raise HTTPException(status_code=400, detail="Optimization already in progress")
    
    logger.info("Starting background processing of Jira Sub-tasks")
    background_tasks.add_task(process_jira_subtasks, optimize_story_logic)
    return {"message": "Jira Sub-task optimization started in the background"}

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
