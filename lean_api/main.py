"""
Lean 4 Verification Microservice
=================================
FastAPI service that verifies Lean 4 code using a local Lean + Mathlib
installation.  Deployed separately (Railway / Render / Fly.io) so that
the Streamlit front-end can call it as a fallback when Lean is not
installed on the UI server (e.g. Streamlit Cloud).

Endpoints
---------
POST /verify   – verify a Lean 4 snippet
GET  /health   – liveness probe
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the Lean project that has Mathlib as a dependency
LEAN_PROJECT = Path(__file__).parent / "lean_project"
LAKE_BIN = os.environ.get("LAKE_BIN", "lake")

app = FastAPI(title="Lean Verification API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    code: str
    timeout: int = 60  # seconds


class VerifyResponse(BaseModel):
    stdout: str
    stderr: str
    returncode: int


@app.get("/health")
async def health():
    return {"status": "ok", "lean_project": str(LEAN_PROJECT)}


@app.post("/verify", response_model=VerifyResponse)
async def verify(req: VerifyRequest):
    if not LEAN_PROJECT.exists():
        raise HTTPException(status_code=503, detail="Lean project not found")

    # Write code to a temp file inside the Lean project directory so that
    # `lake env lean` can resolve imports against the project's Mathlib.
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".lean",
        dir=LEAN_PROJECT,
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(req.code)
        tmp = Path(f.name)

    try:
        proc = await asyncio.create_subprocess_exec(
            LAKE_BIN, "env", "lean", str(tmp), "--json",
            cwd=LEAN_PROJECT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=req.timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            return VerifyResponse(
                stdout="",
                stderr=f"Timeout after {req.timeout}s",
                returncode=1,
            )

        return VerifyResponse(
            stdout=stdout_b.decode("utf-8", errors="replace"),
            stderr=stderr_b.decode("utf-8", errors="replace"),
            returncode=proc.returncode or 0,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="lake binary not found")
    finally:
        tmp.unlink(missing_ok=True)
