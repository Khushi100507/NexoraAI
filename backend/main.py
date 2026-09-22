import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import pandas as pd

from analytics.engine import AnalyticsEngine
from agents.orchestrator import Orchestrator
from tools.chat import answer


# =========================================================
# BASE PATH
# =========================================================

BASE = Path(__file__).resolve().parents[1]


# =========================================================
# CORE SERVICES
# =========================================================

engine = AnalyticsEngine()

orchestrator = Orchestrator(
    engine
)


# =========================================================
# AUTONOMOUS MONITORING LOOP
# =========================================================

async def monitor_loop():

    while True:

        try:

            orchestrator.monitor()

        except Exception as exc:

            print(
                f"[NEXORAAI MONITOR ERROR] {exc}"
            )

        await asyncio.sleep(60)


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app):

    task = asyncio.create_task(
        monitor_loop()
    )

    yield

    task.cancel()

    try:

        await task

    except asyncio.CancelledError:

        pass


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="NEXORAAI",
    version="1.0.0",
    lifespan=lifespan
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):

    question: str


# =========================================================
# FRONTEND
# =========================================================

@app.get("/")
def home():

    return FileResponse(
        BASE / "frontend" / "index.html"
    )


@app.get("/app.js")
def js():

    return FileResponse(
        BASE / "frontend" / "app.js"
    )


@app.get("/styles.css")
def css():

    return FileResponse(
        BASE / "frontend" / "styles.css"
    )


# =========================================================
# HEALTH
# =========================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "product": "NEXORAAI"
    }


# =========================================================
# BUSINESS OVERVIEW
# =========================================================

@app.get("/api/overview")
def overview():

    engine.refresh()

    return engine.overview()


# =========================================================
# AVAILABLE TIME PERIODS
# =========================================================

@app.get("/api/periods")
def periods():

    engine.refresh()

    min_date = engine.time.min_date
    max_date = engine.time.max_date

    periods = []

    # -----------------------------------------------------
    # RELATIVE PERIODS
    # -----------------------------------------------------

    periods.extend([
        {
            "value": "this_month",
            "label": "This Month"
        },
        {
            "value": "last_month",
            "label": "Last Month"
        },
        {
            "value": "this_year",
            "label": "This Year"
        },
        {
            "value": "last_year",
            "label": "Last Year"
        }
    ])

    # -----------------------------------------------------
    # AVAILABLE MONTHS
    # -----------------------------------------------------

    month_start = pd.Timestamp(
        min_date.year,
        min_date.month,
        1
    )

    month_end = pd.Timestamp(
        max_date.year,
        max_date.month,
        1
    )

    current = month_start

    while current <= month_end:

        value = current.strftime(
            "%Y-%m"
        )

        label = current.strftime(
            "%B %Y"
        )

        periods.append({
            "value": value,
            "label": label
        })

        current = (
            current
            + pd.DateOffset(
                months=1
            )
        )

    # -----------------------------------------------------
    # AVAILABLE YEARS
    # -----------------------------------------------------

    for year in range(
        min_date.year,
        max_date.year + 1
    ):

        periods.append({
            "value": str(year),
            "label": str(year)
        })

    return {

        "min_date": str(
            min_date
        ),

        "max_date": str(
            max_date
        ),

        "periods": periods
    }


# =========================================================
# SALES PERFORMANCE
# =========================================================

@app.get("/api/sales")
def sales(

    period: str = Query(
        "this_month",
        description=(
            "Business period. "
            "Examples: this_month, last_month, "
            "2026-09, 2026."
        )
    )
):

    engine.refresh()

    try:

        return engine.sales_performance(
            period
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# =========================================================
# PERIOD SUMMARY
# =========================================================

@app.get("/api/sales/summary")
def sales_summary(

    period: str = Query(
        "this_month"
    )
):

    engine.refresh()

    try:

        return engine.period_summary(
            period
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# =========================================================
# PERIOD COMPARISON
# =========================================================

@app.get("/api/sales/compare")
def sales_compare(

    current: str = Query(...),

    previous: str = Query(...)
):

    engine.refresh()

    try:

        return engine.compare_periods(
            current,
            previous
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# =========================================================
# BUSINESS INSIGHTS
# =========================================================

@app.get("/api/insights")
def insights():

    engine.refresh()

    return engine.insights()


# =========================================================
# BUSINESS DIAGNOSIS
# =========================================================

@app.get("/api/diagnosis")
def diagnosis():

    engine.refresh()

    return engine.diagnosis()


# =========================================================
# AUTONOMOUS MONITORING
# =========================================================

@app.get("/api/monitor")
def monitor():

    orchestrator.monitor()

    return {
        "monitoring": True
    }


# =========================================================
# OPERATIONS
# =========================================================

@app.get("/api/operations")
def operations():

    return orchestrator.items()

# =========================================================
# ASK NEXORAAI
# =========================================================

@app.post("/api/chat")
def chat(
    req: ChatRequest
):

    engine.refresh()

    return {
        "answer": answer(
            req.question,
            engine.question_context()
        )
    }


# =========================================================
# APPROVE OPERATION
# =========================================================

@app.post(
    "/api/operations/{op_id}/approve"
)
def approve(op_id: int):

    result = orchestrator.status(
        op_id,
        "approved"
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Operation not found"
        )

    return result


# =========================================================
# REJECT OPERATION
# =========================================================

@app.post(
    "/api/operations/{op_id}/reject"
)
def reject(op_id: int):

    result = orchestrator.status(
        op_id,
        "rejected"
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Operation not found"
        )

    return result


# =========================================================
# EXECUTE OPERATION
# =========================================================

@app.post(
    "/api/operations/{op_id}/execute"
)
def execute(op_id: int):

    result = orchestrator.execute(
        op_id
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Operation not found"
        )

    return result


# =========================================================
# DATA UPLOAD
# =========================================================

@app.post(
    "/api/data/upload/{dataset}"
)
async def upload(
    dataset: str,
    file: UploadFile = File(...)
):

    allowed = {
        "sales",
        "orders",
        "customers",
        "products",
        "inventory",
        "finance",
        "marketing",
        "suppliers"
    }

    if dataset not in allowed:

        raise HTTPException(
            status_code=400,
            detail="Unsupported dataset"
        )

    target = (
        BASE
        / "data"
        / f"{dataset}.csv"
    )

    target.write_bytes(
        await file.read()
    )

    try:

        df = pd.read_csv(
            target
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV: {exc}"
        )

    engine.refresh()

    return {

        "success": True,

        "dataset": dataset,

        "filename": file.filename,

        "rows": len(df)
    }