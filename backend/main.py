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
from backend.swarm.tools import (
    look_up_item, execute_refund,
    transfer_to_technical_requirements, transfer_to_ux,
    transfer_to_qa, transfer_to_stakeholder_liaison, transfer_to_master
)
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

# Populate tools in config / tools mapping
config.tools = {
    "look_up_item": look_up_item,
    "execute_refund": execute_refund,
    "transfer_to_technical_requirements": transfer_to_technical_requirements,
    "transfer_to_ux": transfer_to_ux,
    "transfer_to_qa": transfer_to_qa,
    "transfer_to_stakeholder_liaison": transfer_to_stakeholder_liaison,
    "transfer_to_master": transfer_to_master,
}

# Create agents based on configuration
agents = [
    Agent(
        name="Master Agent",
        instructions="You are the Master Agent responsible for coordinating the optimization of user stories. Your role is to analyze the initial user story, decide which specialist agents to involve, and synthesize their inputs into a final, optimized user story. Use your judgment to determine which agents are necessary for each story, and don't hesitate to involve multiple agents if needed. Your goal is to produce a comprehensive, well-rounded user story that covers technical, UX, and business aspects as appropriate. When synthesizing the final user story, ensure it follows the format 'As a user, I want... so that...' followed by a prioritized list of acceptance criteria.",
        tools=[config.tools[tool] for tool in config.tools if tool.startswith("transfer_to_")],
        model=config.openai_model
    ),
    Agent(
        name="Technical Requirements Agent",
        instructions="You are the Technical Requirements Agent. Your role is to analyze user stories from a technical perspective and break them down into specific technical requirements.",
        tools=[config.tools["transfer_to_master"]],
        model=config.openai_model
    ),
    Agent(
        name="User Experience Agent",
        instructions="You are the UX Agent. Your role is to optimize user stories by considering the user experience perspective. Focus on usability, accessibility, and user interface design considerations.",
        tools=[config.tools["transfer_to_master"]],
        model=config.openai_model
    ),
    Agent(
        name="Quality Assurance Agent",
        instructions="You are the QA Agent. Your role is to review and refine user stories to ensure they are testable and meet quality standards. Focus on defining acceptance criteria and potential edge cases.",
        tools=[config.tools["transfer_to_master"]],
        model=config.openai_model
    ),
    Agent(
        name="Stakeholder Liaison Agent",
        instructions="You are the Stakeholder Liaison Agent. Your role is to review the optimized user story and ensure it aligns with business goals and user needs. Provide specific business-related acceptance criteria and suggest any necessary adjustments to meet stakeholder expectations.",
        tools=[config.tools["transfer_to_master"]],
        model=config.openai_model
    )
]

# Create the swarm
swarm = Swarm(agents)

# Expose swarm creation function for testing
def create_swarm():
    return Swarm(agents)

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

def optimize_story_logic(content: str):
    """
    Core logic for optimizing a user story.
    This function should be used by both API endpoints.
    """
    async def optimize():
        print(f"Starting optimization for story: {content[:50]}...")
        start_time = time.time()
        try:
            # Context Analysis Step
            context_analysis = await swarm.analyze_context(content)
            print(f"Context analysis: {context_analysis}")

            result = await swarm.process_message(content, config.tools, context_analysis)
            end_time = time.time()
            print(f"Optimization completed in {end_time - start_time:.2f} seconds")
            print(f"Optimized story: {result[0][:50]}...")
            return result
        except Exception as e:
            print(f"Error during optimization: {str(e)}")
            raise
    return optimize

@app.post("/optimize_story", response_model=OptimizedUserStory)
@rate_limit("5/minute")
async def optimize_story(user_story: UserStory, request: Request):
    try:
        logger.info(f"Received request to optimize story: {user_story.content}")
        optimize_func = optimize_story_logic(user_story.content)
        optimized, agent_interactions, performance_metrics = await optimize_func()
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
        optimize_func = optimize_story_logic(story)
        try:
            optimized, agent_interactions, performance_metrics = await optimize_func()
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
