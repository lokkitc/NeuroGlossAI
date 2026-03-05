from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

                                         

def get_client_ip(request) -> str | None:
    if request is None:
        return None

    if bool(getattr(settings, "RATE_LIMIT_TRUST_PROXY", False)):
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            first = xff.split(",")[0].strip()
            if first:
                return first
        real_ip = request.headers.get("X-Real-Ip")
        if real_ip:
            real_ip = real_ip.strip()
            if real_ip:
                return real_ip

    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    if host:
        return str(host)
    return None


def _rate_limit_key_func(request):
    return get_client_ip(request) or get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key_func)
