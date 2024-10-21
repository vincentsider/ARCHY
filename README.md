# OpenAI Swarm-based User Story Optimizer

This project implements a FastAPI-based application that uses a swarm of AI agents to optimize user stories. The system leverages OpenAI's GPT models to analyze and improve user stories for software development projects.

## Features

- Optimize individual user stories
- Process multiple user stories in the background
- Check the status of optimization processes
- Configurable agents and tools
- Dynamic handoffs between agents
- Rate limiting
- Logging for better visibility into the optimization process
- Jira integration for optimizing Sub-task descriptions

## Swarm Logic Overview

The core of this application is the swarm logic, which orchestrates multiple AI agents to collaboratively optimize user stories. Here's a brief overview of how it works:

1. **Initialization**: The swarm is set up with multiple specialized agents (e.g., Technical Requirements, User Experience, Quality Assurance).

2. **Context Analysis**: When a user story is received, the Master Agent analyzes its context to understand the main intent.

3. **Triage**: The system determines which specialist agents are most relevant for the given user story.

4. **Collaborative Processing**: Relevant agents process the story, providing their specialized input. This is not strictly sequential; agents can interact, consult each other, and hand off tasks as needed.

5. **Feedback Loop**: The system generates a summary, assesses its quality, and may request clarifications from agents if needed.

6. **Final Output**: An optimized user story is produced, incorporating insights from all relevant agents.

For a more detailed explanation of the swarm logic, refer to the `swarm_manual.md` file in the `backend` directory.

## Setup

1. Clone the repository
2. Navigate to the `backend` directory
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Set up your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Set up your Jira API credentials in the `.env` file:
   ```
   JIRA_HOST=your_jira_host
   JIRA_EMAIL=your_jira_email
   JIRA_API_TOKEN=your_jira_api_token
   PROJECT_KEY=your_jira_project_key
   ```

## Configuration

The application is highly configurable. You can modify the `config.py` file to change:

- The OpenAI model used
- The number and types of agents
- The tools available to each agent

To use a custom configuration, create a JSON file with your desired settings and update the `load_config` function in `config.py` to load your custom configuration.

## Running the Application

To start the server, run the following command from the `backend` directory:

```
uvicorn main:app --reload --port 8002
```

The API will be available at `http://localhost:8002`.

## API Endpoints

### 1. Optimize a Single User Story

**Endpoint:** `POST /optimize_story`

**Request Body:**
```json
{
  "content": "As a user, I want to log in to the system so that I can access my account."
}
```

**Response:**
```json
{
  "original": "As a user, I want to log in to the system so that I can access my account.",
  "optimized": "... optimized story content ...",
  "agent_interactions": [...],
  "model": "gpt-3.5-turbo",
  "performance_metrics": {...}
}
```

### 2. Process Multiple User Stories

**Endpoint:** `POST /process_all_stories`

**Request Body:**
```json
[
  "Story 1",
  "Story 2",
  "Story 3"
]
```

**Response:**
```json
{
  "message": "Story optimization started in the background"
}
```

### 3. Check Optimization Status

**Endpoint:** `GET /optimization_status`

**Response:**
```json
{
  "total_stories": 3,
  "processed_stories": 3,
  "status": "completed"
}
```

### 4. Process Jira Sub-tasks

**Endpoint:** `POST /process_jira_subtasks`

**Response:**
```json
{
  "message": "Jira Sub-task optimization started in the background"
}
```

## Jira Integration

The application includes Jira integration for optimizing Sub-task descriptions. This feature allows you to automatically fetch Sub-tasks from your Jira project, optimize their descriptions using the swarm-based AI system, and update the optimized descriptions back in Jira.

To use this feature:

1. Ensure your Jira API credentials are correctly set in the `.env` file.
2. Use the `/process_jira_subtasks` endpoint to start the optimization process for all Sub-tasks in your Jira project.
3. The optimization process runs in the background, similar to the multiple story processing feature.
4. You can check the status of the optimization process using the `/optimization_status` endpoint.

## Running Tests

To run the tests, use the following command from the project root directory:

```
python -m pytest backend/tests
```

This will run all tests, including the Jira integration tests.

## Error Handling and Troubleshooting

- If you encounter a "ModuleNotFoundError", ensure that you've installed all required packages and that you're running the application from the correct directory.
- If you get an "Invalid API Key" error, check that you've correctly set up your OpenAI API key in the `.env` file.
- For rate limiting issues, ensure that the `slowapi` package is installed.
- If the optimization process seems slow, check your internet connection and the responsiveness of the OpenAI API.
- For Jira integration issues, verify that your Jira API credentials are correct and that you have the necessary permissions to access and modify Sub-tasks in your project.



## Future Improvements

- Implement caching to avoid redundant API calls for similar user stories
- Add more detailed metrics collection for monitoring performance and usage
- Implement user authentication and authorization for the API
- Allow for dynamic configuration of the swarm structure and agent behaviors at runtime
- Extend Jira integration to handle other issue types and custom fields
- Implement a web interface for easier management and visualization of the optimization process
- and more !


