import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from backend.main import app, swarm, config
from backend.swarm.swarm import Swarm
from backend.swarm.agent import Agent

client = TestClient(app)

# ... (keep all other test functions unchanged)

@pytest.mark.asyncio
async def test_rate_limiting():
    class MockLimiter:
        def __init__(self):
            self.call_count = 0

        def limit(self, limit_string):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    self.call_count += 1
                    print(f"Request {self.call_count} received")
                    if self.call_count <= 5:
                        result = await func(*args, **kwargs)
                        print(f"Request {self.call_count} succeeded")
                        return result
                    print(f"Request {self.call_count} rate limited")
                    raise HTTPException(status_code=429, detail="5 per 1 minute")
                return wrapper
            return decorator

    mock_limiter = MockLimiter()

    with patch('backend.main.limiter', mock_limiter):
        with patch('backend.main.optimize_story_cached', new_callable=AsyncMock) as mock_optimize:
            mock_optimize.return_value = "Mocked optimized story"
            
            # First 5 requests should succeed
            for i in range(5):
                response = client.post("/optimize_story", json={"content": "Test story"})
                print(f"Response {i+1} status code: {response.status_code}")
                assert response.status_code == 200, f"Request {i+1} should have succeeded"
                assert response.json() == {"original": "Test story", "optimized": "Mocked optimized story"}

            # 6th request should be rate limited
            response = client.post("/optimize_story", json={"content": "Test story"})
            print(f"Response 6 status code: {response.status_code}")
            assert response.status_code == 429, "The 6th request should be rate limited"
            assert response.json() == {"detail": "5 per 1 minute"}

    print(f"Total calls to rate limiter: {mock_limiter.call_count}")
