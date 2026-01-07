import aiohttp_jinja2
from aiohttp import web
from .base import BaseView

class ReportView(BaseView):
    @aiohttp_jinja2.template("video_report.html")
    async def video_report(self, request):
        return {} 

class ContactView(BaseView):
    @aiohttp_jinja2.template("contact.html")
    async def contact_us(self, request):
        return {}

class AboutView(BaseView):
    @aiohttp_jinja2.template("about.html")
    async def about(self, request):
        return {} 

class DownloadPGView(BaseView):
    @aiohttp_jinja2.template("downloadPG.html")
    async def download_pg(self, request):
        return {}

