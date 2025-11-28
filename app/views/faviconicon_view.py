import random
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web
from pathlib import Path
from .base import BaseView


class FaviconIconView(BaseView):
    async def faviconicon(self, req: web.Request) -> web.Response:
        favicon_path = Path(__file__).resolve().parent.parent / "static" / "img" / "favicon.ico"
        text = "T"
        if not favicon_path.exists():
            W, H = (360, 360)
            color = tuple((random.randint(0, 255) for _ in range(3)))
            im = Image.new("RGB", (W, H), color)
            draw = ImageDraw.Draw(im)
            font = ImageFont.truetype("arial.ttf", 100)

            # Use getbbox() to calculate text size
            bbox = font.getbbox(text)
            w, h = bbox[2], bbox[3]

            # Center the text
            draw.text(((W - w) / 2, (H - h) / 2), text, fill="white", font=font)
            im.save(favicon_path, "JPEG")

        with open(favicon_path, "rb") as fp:
            body = fp.read()

        return web.Response(
            status=200,
            body=body,
            headers={
                "Content-Type": "image/jpeg",
                "Content-Disposition": 'inline; filename="favicon.ico"',
            },
        )
