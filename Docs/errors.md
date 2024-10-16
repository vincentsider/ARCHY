# Errors Log

This document is used to log encountered issues and their solutions throughout the development process.

## Error Entry Template

- **Date**:
- **Module/Component**:
- **Error Description**:
- **Cause**:
- **Solution**:

## Logged Errors

### Error: ModuleNotFoundError: No module named 'jira'

- **Date**:
- **Module/Component**: `backend/main.py`
- **Error Description**: Encountered `ModuleNotFoundError: No module named 'jira'` when running the application.
- **Cause**: The `jira` Python package is not installed in the environment.
- **Solution**: Install the required dependencies by running `pip install -r requirements.txt` in the `backend` directory.

### Error: Address already in use

- **Date**:
- **Module/Component**: Backend server startup
- **Error Description**: `ERROR: [Errno 48] Address already in use`
- **Cause**: Another process is already using the default port (8000).
- **Solution**: Start the server on a different port by specifying the port number in the command, e.g., `uvicorn main:app --reload --port 8001`.
