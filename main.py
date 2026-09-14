from fastapi import Depends, FastAPI, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.core.logging import LOGGING_CONFIG, get_logger, request_logging_middleware, setup_logging
from app.core.tracing import setup_tracing
from app.db.models import Category
from app.db.session import get_db

setup_logging()

app = FastAPI()
app.middleware("http")(request_logging_middleware)
setup_tracing(app)

logger = get_logger("main")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/metrics")
async def metrics():
    """Prometheus 抓取端点（监控范围=应用）。"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/category")
def list_categories(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """分页查询分类列表（过滤逻辑删除的记录）。"""
    query = db.query(Category).filter(Category.deleted_at.is_(None))

    total = query.count()
    items = (
        query.order_by(Category.cat_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "cat_id": c.cat_id,
                "name": c.name,
                "parent_cid": c.parent_cid,
                "cat_level": c.cat_level,
                "show_status": c.show_status,
                "sort": c.sort,
                "icon": c.icon,
            }
            for c in items
        ],
    }


if __name__ == "__main__":
    import uvicorn

    # log_config 让 uvicorn(含 reload 主进程) 的启动日志也走结构化 JSON；
    # access_log=False 关闭 uvicorn 自带访问日志，由中间件统一打 JSON（且已排除 /metrics）
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        access_log=False,
        log_config=LOGGING_CONFIG,
    )
