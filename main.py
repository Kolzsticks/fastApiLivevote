from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import time
import asyncio

app = FastAPI()

# Allow CORS for frontend (adjust origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (* for testing, restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

votes = {"Alice": 1, "Bob": 8, "Charlie": 12}

# Create an event that signals when votes are updated
vote_update_event = asyncio.Event()

@app.get("/live-results")
async def live_results():
    async def event_stream():
        last_sent_data = None
        while True:
            await vote_update_event.wait()  # Wait until an update occurs

            data = json.dumps(votes)
            if data != last_sent_data:  # Avoid sending duplicate data
                yield f"data: {data}\n\n"
                last_sent_data = data

            vote_update_event.clear()  # Reset the event to wait for new updates

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/vote/{candidate}")
async def vote(candidate: str):
    if candidate in votes:
        votes[candidate] += 1
    else:
        votes[candidate] = 1

    vote_update_event.set()  # Notify SSE clients about the change
    return {"message": f"Vote added for {candidate}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
