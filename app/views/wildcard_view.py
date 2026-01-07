# wildcard_view.py
import aiohttp_jinja2
from aiohttp import web
from .base import BaseView


class WildcardView(BaseView):
    @aiohttp_jinja2.template("404.html")  # This will render the 404 template
    async def wildcard(self, req: web.Request) -> web.Response:
        # Create response with 404 status
        response = aiohttp_jinja2.render_template("404.html", req, {
            "request_path": req.path,
            "method": req.method
        })
        response.set_status(404)
        return response
        
        # Alternative simpler approach:
        # return aiohttp_jinja2.render_template(
        #     "404.html", 
        #     req, 
        #     {"request_path": req.path},
        #     status=404
        # )
