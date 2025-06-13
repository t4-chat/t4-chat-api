import os
from locust import HttpUser, between


class BaseUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:9001"
    
    # Mark as abstract to prevent direct instantiation
    abstract = True
    
    # Get auth token from environment or use default
    auth_token = os.environ.get("LOCUST_AUTH_TOKEN", "<token>")

    def on_start(self):
        # Set default headers for all requests
        self.client.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    def on_stop(self):
        pass
