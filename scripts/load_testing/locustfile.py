"""
Locust load testing configuration for the API.
Run with: locust -f scripts/load_testing/locustfile.py
"""
import random
import sseclient
from typing import List, Optional

from scripts.load_testing.base import BaseUser
from locust import task

class ChatApiUser(BaseUser):
    """
    User that tests chat API endpoints.
    Note: ChatTasks must be first in inheritance for @task decorators to work.
    """
    
    def on_start(self):
        super().on_start()
        self.chat_ids: List[str] = []
        self.current_chat_id = None
        self.create_new_chat()
    
    def on_stop(self):
        for chat_id in self.chat_ids:
            self.client.delete(f"/api/chats/{chat_id}")
        super().on_stop()
        
    def create_new_chat(self) -> Optional[str]:
        with self.client.post("/api/chats", name="Create Chat", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                chat_id = data.get("id")
                if chat_id:
                    self.chat_ids.append(chat_id)
                    self.current_chat_id = chat_id
                    return chat_id
            return None

    @task(1)
    def get_all_chats(self):
        self.client.get("/api/chats/", name="Get All Chats")

    @task(2)
    def send_message(self):
        if not self.current_chat_id:
            self.create_new_chat()

        if self.current_chat_id:
            payload = {
                "chat_id": self.current_chat_id,
                "model_id": 1,
                "messages": [{"role": "user", "content": f"Test message {random.randint(1, 1000)}"}],
                "options": {},
            }
            
            # Don't use catch_response in the initial request
            response = self.client.post(
                "/api/chats/conversation", 
                json=payload, 
                name="Send Message", 
                stream=True, 
                catch_response=False
            )
            
            if response.status_code == 200:
                try:
                    # Use SSEClient to parse the stream properly
                    client = sseclient.SSEClient(response)
                    
                    # Process each complete SSE message
                    for event in client.events():
                        if 'error' in event.data.lower():
                            # Use a new locust request for the error case
                            with self.client.request("GET", "/placeholder", name="SSE Message Error", catch_response=True) as caught:
                                caught.failure("Error in SSE message: " + event.data[:100])
                            return
                    
                    # If we got here, all messages were processed successfully
                    with self.client.request("GET", "/placeholder", name="SSE Stream Success", catch_response=True) as caught:
                        caught.success()
                        
                except Exception as e:
                    # Report streaming errors
                    with self.client.request("GET", "/placeholder", name="SSE Stream Error", catch_response=True) as caught:
                        caught.failure(f"Error processing SSE stream: {str(e)}")
            else:
                # Initial response error
                with self.client.request("GET", "/placeholder", name="SSE Initial Response", catch_response=True) as caught:
                    caught.failure(f"Failed with status code: {response.status_code}")
                    
class UtilizationApiUser(BaseUser):
    """
    User that tests utilization API endpoints.
    """
    
    @task(1)
    def get_all_utilization(self):
        self.client.get("/api/utilization/", name="Get All Utilization")
        
    @task(2)
    def get_limits(self):
        self.client.get("/api/utilization/limits", name="Get Limits")

class AiModelApiUser(BaseUser):
    """
    User that tests ai model API endpoints.
    """
    
    @task(1)
    def get_all_ai_models(self):
        self.client.get("/api/ai-models", name="Get All Ai Models")

class AiProviderApiUser(BaseUser):
    """
    User that tests ai provider API endpoints.
    """
    
    @task(1)
    def get_all_ai_providers(self):
        self.client.get("/api/ai-providers", name="Get All Ai Providers")

class GetAllChatsApiUser(BaseUser):
    """
    User that tests get all chats API endpoints.
    """
    
    @task(1)
    def get_all_chats(self):
        self.client.get("/api/chats", name="Get All Chats")

class CreateChatApiUser(BaseUser):
    """
    User that tests create chat API endpoints.
    """
    
    @task(1)
    def create_chat(self):
        self.client.post("/api/chats", name="Create Chat")
