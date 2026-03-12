from functools import lru_cache

from .config import Settings, get_settings
from .service import GraphService


@lru_cache
def get_graph_service() -> GraphService:
    return GraphService()


def get_app_settings() -> Settings:
    return get_settings()
