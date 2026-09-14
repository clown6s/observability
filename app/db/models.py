"""数据库模型。"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from app.db.session import Base


class Category(Base):
    """商品三级分类。"""

    __tablename__ = "category"

    cat_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分类id")
    name = Column(String(50), nullable=True, comment="分类名称")
    parent_cid = Column(Integer, nullable=True, comment="父分类id")
    cat_level = Column(Integer, nullable=True, comment="层级")
    show_status = Column(Integer, nullable=True, comment="是否显示[1显示，2-不显示]")
    sort = Column(Integer, nullable=True, comment="排序")
    icon = Column(String(255), nullable=True, comment="图标地址")
    deleted_at = Column(DateTime, nullable=True, comment="逻辑删除字段")