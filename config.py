import logging
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

OVERLORD_SOCKET = Path("/run/spf/overlord.sock")


class Overlord:
    _data: dict[str, str] = {}
    _over_transport = httpx.AsyncHTTPTransport(uds=str(OVERLORD_SOCKET))

    @classmethod
    async def req_constants(cls) -> None:
        url = "http://overlord/config"
        try:
            async with httpx.AsyncClient(
                transport=cls._over_transport,
                timeout=5.0,
            ) as client:
                resp = await client.get(url)

            if resp.status_code != 200:
                log.warning(
                    f"Overlord returned {resp.status_code} for {url}",
                )
                cls._data = {}

            cls._data = resp.json()

        except httpx.ConnectError:
            log.warning(f"Overlord socket not available: {OVERLORD_SOCKET}")
            cls._data = {}

        except httpx.TimeoutException:
            log.warning(f"Overlord request timeout: {url}")
            cls._data = {}

        except Exception as exc:
            log.exception(f"Unexpected error while fetching {url}: {exc}")
            cls._data = {}

    @classmethod
    async def req_svc(cls, svc_name: str) -> httpx.AsyncClient | None:
        url = f"http://overlord/svc/{svc_name}"
        try:
            async with httpx.AsyncClient(
                transport=cls._over_transport,
                timeout=5.0,
            ) as client:
                resp = await client.get(url)

            if resp.status_code != 200:
                return None

            ans = resp.json()

            if not ans["is_usable"]:
                return None

            return httpx.AsyncClient(
                transport=httpx.AsyncHTTPTransport(uds=ans["sock"]),
                timeout=5.0,
            )

        except httpx.ConnectError:
            log.warning(
                f"Overlord socket not available: {OVERLORD_SOCKET}",
            )
            return None

        except httpx.TimeoutException:
            log.warning(f"Overlord request timeout: {url}")
            return None

        except Exception as exc:
            log.exception(f"Unexpected error while fetching {url}: {exc}")
            return None

    @classmethod
    def get_const(cls) -> dict[str, str]:
        return cls._data
