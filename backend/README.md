# OpenAI Swarm-based User Story Optimizer

This project implements a FastAPI-based application that uses a swarm of AI agents to optimize user stories. The system leverages OpenAI's GPT models to analyze and improve user stories for software development projects.

## Features

- Optimize individual user stories
- Process multiple user stories in the background
- Check the status of optimization processes
- Configurable agents and tools
- Dynamic handoffs between agents
- Rate limiting (if slowapi is installed)
- Logging for better visibility into the optimization process
- Jira integration for optimizing Sub-task descriptions

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

The application now includes Jira integration for optimizing Sub-task descriptions. This feature allows you to automatically fetch Sub-tasks from your Jira project, optimize their descriptions using the swarm-based AI system, and update the optimized descriptions back in Jira.

To use this feature:

1. Ensure your Jira API credentials are correctly set in the `.env` file.
2. Use the `/process_jira_subtasks` endpoint to start the optimization process for all Sub-tasks in your Jira project.
3. The optimization process runs in the background, similar to the multiple story processing feature.
4. You can check the status of the optimization process using the `/optimization_status` endpoint.

Note: The Jira integration respects the same rate limiting rules as other endpoints to prevent overloading the Jira API or the OpenAI API.

## Example Usage

Here's a simple Python script demonstrating how to use the API, including the new Jira integration:

```python
import requests

BASE_URL = "http://localhost:8002"

# Optimize a single story
story = {"content": "As a user, I want to reset my password."}
response = requests.post(f"{BASE_URL}/optimize_story", json=story)
print(response.json())

# Process multiple stories
stories = ["Story 1", "Story 2", "Story 3"]
response = requests.post(f"{BASE_URL}/process_all_stories", json=stories)
print(response.json())

# Start Jira Sub-task optimization
response = requests.post(f"{BASE_URL}/process_jira_subtasks")
print(response.json())

# Check optimization status
response = requests.get(f"{BASE_URL}/optimization_status")
print(response.json())
```

## Running Tests

To run the tests, use the following command from the project root directory:

```
python -m pytest backend/tests
```

This will run all tests, including the new Jira integration tests.

## Swarm Structure

The application uses a swarm of specialized AI agents to optimize user stories. The agents and their tools are configurable, allowing for flexible and dynamic optimization processes.

## Error Handling and Troubleshooting

- If you encounter a "ModuleNotFoundError", ensure that you've installed all required packages and that you're running the application from the correct directory.
- If you get an "Invalid API Key" error, check that you've correctly set up your OpenAI API key in the `.env` file.
- For rate limiting issues, ensure that the `slowapi` package is installed if you want to use rate limiting features.
- If the optimization process seems slow, check your internet connection and the responsiveness of the OpenAI API.
- For Jira integration issues, verify that your Jira API credentials are correct and that you have the necessary permissions to access and modify Sub-tasks in your project.

## Contributing

Contributions are welcome! Here's how you can contribute to the project:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Write your code, following the project's coding standards (PEP 8 for Python)
4. Write or update tests for your changes
5. Run the test suite to ensure all tests pass
6. Submit a pull request with a clear description of your changes

Please ensure your code adheres to the following standards:
- Follow PEP 8 guidelines for Python code
- Write clear, descriptive commit messages
- Include docstrings for new functions and classes
- Update the README.md if you're adding or changing features

## Future Improvements

- Implement caching to avoid redundant API calls for similar user stories
- Add more detailed metrics collection for monitoring performance and usage
- Implement user authentication and authorization for the API
- Allow for dynamic configuration of the swarm structure and agent behaviors at runtime
- Extend Jira integration to handle other issue types and custom fields
- Implement a web interface for easier management and visualization of the optimization process

## License

This project is licensed under the MIT License.
