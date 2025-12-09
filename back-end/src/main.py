from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.toolsets.routes import toolset_router
from src.modules.agents.routes import agent_router
from src.modules.knowledge_base.routes import knowledge_base_router
from src.modules.chat.routes import chat_router
from src.modules.copilot.routes import models_router

app = FastAPI(title="PUC-Rio Final Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(toolset_router)
app.include_router(agent_router)
app.include_router(knowledge_base_router)
app.include_router(chat_router)
app.include_router(models_router)

