import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def client_address(request: Request) -> str:
    # Hors de Vercel, ces en-têtes viendraient du client et pourraient être falsifiés.
    if os.environ.get("VERCEL"):
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_address, default_limits=["60/minute"])
