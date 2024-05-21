from fastapi import Request, status, Response
from fastapi.responses import JSONResponse
from ..exceptions.user_exceptions import UserAlreadyExists, UserNotFound
from ..exceptions.auth_exceptions import InvalidCredentials, NotEnoughPrivileges
from ..exceptions.commons import InvalidParameter
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        
        except NotEnoughPrivileges as e:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(e)})

        except UserNotFound as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

        except UserAlreadyExists as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

        except InvalidParameter as e:
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(e)})

        except InvalidCredentials as e:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(e)})

        except Exception as e:
            if hasattr(e, "status_code"):
                return await self.http_exception_handler(request, e)
            else:
                return await self.generic_exception_handler(request, e)


    async def http_exception_handler(self, request: Request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    async def generic_exception_handler(self, request: Request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {exc}"},
        )