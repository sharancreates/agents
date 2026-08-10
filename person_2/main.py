from fastapi import FastAPI
from person_2.api.routes import router as functionality_router

app = FastAPI(
    title="Person 2 Multi-Agent Evaluation Module",
    description="Automated Sandbox Code Execution and Performance Telemetry Profiler",
    version="1.0.0"
)

# Mount the evaluation routes package dynamically
app.include_router(functionality_router)

@app.get("/health", tags=["System Health"])
async def health_check():
    """Simple uptime checkpoint route."""
    return {"status": "HEALTHY", "service": "person_2_agents"}