import contextlib

from fastapi import FastAPI

from discord_bot.bot_obj import start, stop
from router.overlord_api import router as overlord_api_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await start()
        yield

    finally:
        await stop()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


app.include_router(overlord_api_router)
