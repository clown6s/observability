"""Elasticsearch 客户端（占位）。"""

from elasticsearch import Elasticsearch

from app.core.config import settings

es_client = Elasticsearch(settings.es_hosts, request_timeout=30)
