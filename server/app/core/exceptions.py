from fastapi import HTTPException, status

from app.schemas.common import MessageParam


def error_detail(code: str, message: str = "", **params: MessageParam) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "params": {key: value for key, value in params.items() if value is not None},
    }


def bad_request(code: str, message: str = "", **params: MessageParam) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail(code, message, **params))


def unauthorized(code: str = "error.authRequired", message: str = "Authentication required", **params: MessageParam) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_detail(code, message, **params))


def forbidden(code: str = "error.forbidden", message: str = "Forbidden", **params: MessageParam) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_detail(code, message, **params))


def not_found(code: str = "error.notFound", message: str = "Not found", **params: MessageParam) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail(code, message, **params))


def service_unavailable(code: str = "error.serviceUnavailable", message: str = "Service unavailable", **params: MessageParam) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_detail(code, message, **params))
