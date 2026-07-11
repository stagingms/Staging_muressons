import os
import asyncio
from main import lifespan, app
from admin_shared import _facilitator_registry
import database as db

async def test():
    # Force in-memory db
    os.environ['USE_MEMORY_DB'] = 'true'
    print("Entering lifespan...")
    async with lifespan(app):
        print("Inside lifespan context manager.")
        # Check sessions
        sessions = await db.fetch_all_sessions()
        print(f"Total sessions: {len(sessions)}")
        for s in sessions:
            print(f"Session: {s.get('session_id')}, Facilitator: {s.get('facilitator_id')}, Name: {s.get('cohort_name')}")
    print("Exited lifespan.")

if __name__ == "__main__":
    asyncio.run(test())
