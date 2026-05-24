from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)

STATUS_CODE_TO_ERROR_CODE: dict[int, str] = {
    400: "INVALID_REQUEST",
    404: "PROJECT_NOT_FOUND",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "MODEL_UNAVAILABLE",
    503: "SERVICE_UNAVAILABLE",
    504: "GENERATION_TIMEOUT",
}


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "detail": self.detail,
            }
        }


class ProjectNotFoundError(AppException):
    def __init__(self, project_id: str) -> None:
        super().__init__(
            code="PROJECT_NOT_FOUND",
            message=f"项目 '{project_id}' 不存在",
            status_code=404,
            detail={"project_id": project_id},
        )


class ModelUnavailableError(AppException):
    def __init__(
        self,
        tried_models: list[str] | None = None,
        last_error: str | None = None,
    ) -> None:
        super().__init__(
            code="MODEL_UNAVAILABLE",
            message="所有指定的源模型均不可用，请检查配置或稍后重试",
            status_code=502,
            detail={
                "tried_models": tried_models or [],
                "last_error": last_error or "",
            },
        )


class GenerationTimeoutError(AppException):
    def __init__(self, timeout_seconds: int, model: str | None = None) -> None:
        super().__init__(
            code="GENERATION_TIMEOUT",
            message=f"生成超时（{timeout_seconds}s）",
            status_code=504,
            detail={
                "timeout_seconds": timeout_seconds,
                "model": model or "",
            },
        )


class ServiceUnavailableError(AppException):
    def __init__(self, service: str, reason: str | None = None) -> None:
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"服务 '{service}' 不可用",
            status_code=503,
            detail={
                "service": service,
                "reason": reason or "",
            },
        )


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "detail": detail or {},
            }
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException: code=%s message=%s detail=%s",
        exc.code,
        exc.message,
        exc.detail,
    )
    return _build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
    )


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    errors = exc.errors()
    detail = {"validation_errors": errors}
    logger.warning("ValidationError: %s", errors)
    return _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="请求参数校验失败",
        detail=detail,
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return _build_error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="服务内部错误",
        detail={},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
