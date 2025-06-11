import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette_context import context


class TransactionIDMiddleware(BaseHTTPMiddleware):


    async def dispatch(self, request, call_next):
        transaction_id = str(uuid.uuid4()).replace("-", "")[:8]

        context.transaction_id = transaction_id
        response = await call_next(request)

        response.headers["X-Transaction-ID"] = transaction_id

        return response