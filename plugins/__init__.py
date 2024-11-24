# https://t.me/Ultroid_Official/524





from aiohttp import web
from .route import routes


async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app





# https://t.me/Ultroid_Official/524