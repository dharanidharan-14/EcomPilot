import asyncio
import sys
import uvicorn

if __name__ == "__main__":
    if sys.platform == 'win32':
        # Explicitly set the policy before importing main or running uvicorn
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run on port 8002 to avoid persistent conflicts on 8000/8001
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=False, loop="asyncio")
