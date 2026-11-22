初始结构由 `src/models/entities.py` 中 SQLAlchemy 元数据定义。小型单机演示首次启动时以 `create_all` 建表。保留持久卷升级时，需先为字段变更编写并验证迁移。
