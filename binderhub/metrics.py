from .base import BaseHandler, authenticated
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST


class MetricsHandler(BaseHandler):
    @authenticated
    async def get(self):
        self.set_header('Content-Type', CONTENT_TYPE_LATEST)
        self.write(generate_latest(REGISTRY))
