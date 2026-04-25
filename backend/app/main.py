from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth_router, users_router, admin_router, proxy_router, jobs_router, ai_router
from app.models.base import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerOpsV2 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(proxy_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "CareerOpsV2"}
