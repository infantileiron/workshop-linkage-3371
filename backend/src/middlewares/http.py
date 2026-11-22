import logging
from time import perf_counter
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger('uvicorn.error')


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = uuid4().hex[:14]
        start = perf_counter()
        response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.request_id
        log.info('%s %s %s %.1fms [%s]', request.method, request.url.path, response.status_code,
                 (perf_counter() - start) * 1000, request.state.request_id)
        return response


class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception:
            log.exception('Request failed [%s]', getattr(request.state, 'request_id', 'unknown'))
            return JSONResponse({'detail': '处理失败，请重试'}, status_code=500)
