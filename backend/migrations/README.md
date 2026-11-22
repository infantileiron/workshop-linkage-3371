初始结构由 `src/models/entities.py` 中 SQLAlchemy 元数据定义。小型单机演示首次启动时以 `create_all` 建表。保留持久卷升级时，需先为字段变更编写并验证迁移。

## 002 补单版本与增量复核

`src/main.py` 启动时对已有库执行幂等迁移（新库由 `create_all` 一步建齐）：

- `enrollments.version integer not null default 1`：补单按报名编号与版本对账，旧版本不得覆盖。
- `linkage_reviews.base_id integer`：同课程组合与门槛下指向上一份完整复核，供增量重算沿用证据。
