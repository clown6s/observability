"""应用配置：从环境变量读取 MySQL / Elasticsearch 连接参数（占位）。"""

import os
from urllib.parse import quote_plus


class Settings:
    # MySQL
    mysql_host: str = os.getenv("MYSQL_HOST", "10.211.55.5")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "nfg!om,j^6453decqx!109")
    mysql_db: str = os.getenv("MYSQL_DB", "test")

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{quote_plus(self.mysql_password)}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    # Elasticsearch
    es_hosts: str = os.getenv("ES_HOSTS", "http://127.0.0.1:9200")


settings = Settings()
