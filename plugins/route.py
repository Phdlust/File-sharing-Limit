# https://t.me/Ultroid_Official/524




from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("ultroidxTeam")




# https://t.me/Ultroid_Official/524