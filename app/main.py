from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import json
import traceback
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from internal.logger.logger import setup_logger
from internal.api.endpoints import router as api_router


app = FastAPI()
logger = setup_logger()


app.include_router(api_router)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = None

    async def sanitize_body(body: bytes) -> dict:
        try:
            data = json.loads(body)
            for key in ["password", "token", "secret"]:
                if key in data:
                    data[key] = "***"
            return data
        except:
            return {}

    try:
        body = await request.body()
        cleaned_body = await sanitize_body(body)

        logger.info(
            "Request received",
            extra={
                "method": request.method,
                "path": request.url.path,
                "params": dict(request.query_params),
                "body": cleaned_body,
            }
        )

        response = await call_next(request)

    except Exception as exc:
        logger.critical(
            "Unhandled exception",
            exc_info=True,
            extra={"traceback": traceback.format_exc()}
        )
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    process_time = round((time.time() - start_time) * 1000, 2)

    response_data = {
        "status_code": response.status_code,
        "process_time_ms": process_time,
        "client_ip": request.client.host if request.client else None
    }

    if 400 <= response.status_code < 600:
        logger.error("Request failed", extra=response_data)
    else:
        logger.info("Request succeeded", extra=response_data)

    return response

@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    logger.error(
        "HTTP error",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "body": exc.body.decode() if hasattr(exc, "body") else None
        }
    )
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.critical(
        "Critical error",
        exc_info=True,
        extra={"traceback": traceback.format_exc()}
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )