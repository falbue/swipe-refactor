from fastapi import FastAPI
from api import repositories
import uvicorn

app = FastAPI(title="Swipe Refactor", version="test")

app.include_router(repositories.router, prefix="/repositories", tags=["repos"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
