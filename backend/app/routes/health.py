from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.web3_client import get_web3

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> JSONResponse:
    body: dict[str, object] = {}
    healthy = True

    try:
        db.execute(text("SELECT 1"))
        body["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        healthy = False
        body["db"] = f"error: {exc.__class__.__name__}: {exc}"

    try:
        body["rpc_block_number"] = int(get_web3().eth.block_number)
    except Exception as exc:  # noqa: BLE001
        healthy = False
        body["rpc_block_number"] = None
        body["rpc_error"] = f"{exc.__class__.__name__}: {exc}"

    return JSONResponse(content=body, status_code=200 if healthy else 503)
