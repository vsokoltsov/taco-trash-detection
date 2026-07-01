from fastapi import FastAPI

from trash_annotation.lifespan import lifespan
from trash_annotation.routes import router

app = FastAPI(lifespan=lifespan)
app.include_router(router)
