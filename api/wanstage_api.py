from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

app = FastAPI()


# ---- auto-added CORS & headers ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://exactly-walnut-southwest-equation.trycloudflare.com",
        "http://0.0.0.0:8502",
        "http://localhost:8502",
        "https://race-arthur-groundwater-ringtones.trycloudflare.com",
    ],
    allow_origin_regex=r"https://[a-z0-9-]+\.trycloudflare\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def add_security_headers(request, call_next):
    resp: Response = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return resp


app.add_middleware(BaseHTTPMiddleware, dispatch=add_security_headers)
# ---- /auto-added ----


@app.get("/")
async def root():
    return {"message": "WANSTAGE API root alive"}


@app.get("/health")
async def health():
    return {"status": "ok"}
