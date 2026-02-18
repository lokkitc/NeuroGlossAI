from __future__ import annotations

import contextvars


request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class RequestIdFilter:
    def filter(self, record) -> bool:
        record.request_id = request_id_ctx.get()
        return True
