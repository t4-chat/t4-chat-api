# agg-ai-api

## Run application
```text
uvicorn main:app --reload --port 9001
```

## Test SSE endpoint
```text
curl -X POST "http://localhost:8000/api/chats/messages" -H "Content-Type: application/json" -d '{"message": "Hello, how are you?"}'
```



