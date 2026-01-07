import aiohttp_jinja2
from aiohttp import web
from .base import BaseView

class DownloadPGView(BaseView):
    @aiohttp_jinja2.template("downloadPG.html")
    async def download_pg(self, request):
        return {}
