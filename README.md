# 禾埠木作 · 工坊课程联报核查

禾埠木作由 6 位运营人员为 3 家木工体验场馆排周末班。运营每周从线下表单与场馆预约表整理已确认报名。单独计次会把同一报名的多个勾选重复算进分母，取消占位会抬高联报，整体热门场馆也会把跨场馆构成差误当成课程关联。本项目把报名台账、分场馆列联表和排课签核接起来，支持导出复核凭据给场馆店长。

| 角色 | 常用页面 | 权限与动作 |
|---|---|---|
| 课程分析员 `analyst` | 课程与名额、场馆报名、联报核查 | 录入课程和报名，锁定快照并运算，查看和下载结果 |
| 运营负责人 `manager` | 排课建议 | 分析员权限，另可签核和查询操作审计 |
| 场馆观察员 `viewer` | 四个模块 | 查阅目录、报名与计算证据，下载 CSV |

## 周五工作剧本

1. 09:10 查对本周的 `11月场馆报名汇总.xlsx`，确认木雕浅刻 `WOOD-11` 每场 22 人，木片彩漆 `LACQ-24` 每场 20 人。模拟数据预置在程序中。
2. 09:25 在课程与名额核对榫卯入门 `JOIN-06` 及研磨封蜡 `SAND-18` 的课程编号。
3. 09:45 在场馆报名按河湾老仓过滤，核对 100 份确认报名及 1 份已取消报名。
4. 10:00 录入槐里快闪补单，独立保留取消记录，以场馆和报名编号追溯源文件。
5. 10:25 在联报核查锁定木雕和彩漆的报名快照，每馆至少 12 份有效报名。槐里快闪的样本量未达门槛。
6. 10:30 比对同口径合并优势比 1.0905 和分场馆调整优势比 0.4113，检查方向反转。
7. 11:00 运营负责人进入排课建议，签署「按场馆单独试排」。
8. 11:05 观察员下载已签核的 CSV 以便安排周末教室和讲师。

## 启动

```bash
cp .env.example .env
docker compose up --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://localhost:18276`。FastAPI 文档位于 `http://localhost:19276/docs`，PostgreSQL 映射端口为 `17776`。示例邮箱为 `analyst@hemu.demo`、`manager@hemu.demo` 和 `viewer@hemu.demo`，密码均为 `Woodwork2026!`。

| 服务 | 技术与作用 |
|---|---|
| frontend | Nginx 1.27，原生 HTML/CSS/JS，`/api` 反代 |
| backend | Python 3.11、FastAPI、SQLAlchemy、JWT |
| worker | Python SQL 持久队列和 Redis 唤醒，计算后归档 JSON 至共享卷 |
| db | PostgreSQL 16，保存目录、报名、复核单和操作审计 |
| redis | Redis 7，唤醒计算并支撑健康探针 |

`FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 可覆盖本地映射。`SEED_DEMO` 控制初始化模拟数据。`JWT_SECRET` 与 `DB_PASSWORD` 可以通过 `.env` 覆盖。`frontend/src/pages` 是业务页面，`backend/src/services/association.py` 实现公式，`backend/migrations` 解释首次建表策略。调试后端可沿用容器的 Python 环境执行 `docker compose exec -T backend python -m compileall src`。`docker compose down` 保留数据卷。

## 计算口径

使用确认报名的自然键去重，按场馆拆 a（均报）、b（仅首课）、c（仅次课）、d（均未报）。同口径合并比是 `Σa × Σd / (Σb × Σc)`，Mantel–Haenszel 调整比是 `Σ(a×d/n) / Σ(b×c/n)`。不足最小样本量和某门课程没有比较边际的场馆仍列证据，计算时剔除。分母为零时显示「未定义」。两种比方向相反时提示分馆审阅。使用确定性模拟台账，每次提交保存独立快照，后续新增报名不改变旧单。场馆内混杂、同一申请人多单及体验前后顺序需要业务方另行核查。当前报告给出点估计和分层诊断，未计算区间或强制检验共同比假设。

补单（`POST /api/enrollments/{code}/supplement`）可改勾选、取消报名或转馆，按报名编号与版本对账：版本不高于台账的乱序旧记录返回 409，不覆盖现有记录。同一课程组合与门槛下再次复核时，按发起时锁定的报名版本只重算受影响场馆，版本未变的场馆沿用上一份完整复核的证据行；场馆进出门槛时，合并比与调整比始终按合并证据同步重算。并发补单不阻塞发起复核，联报核查页在新单算完前展示上一份完整结果；较早发起的复核晚算完也不会盖过更新的结果。失败的复核单可重试（`POST /api/analyses/{id}/retry`），复用原单与原快照，不新增复核。

共享枚举定义于 `backend/src/constants/enums.py` 和 `frontend/src/constants/enums.js`。角色出现在登录、前端会话与后端授权。核查状态出现在 worker、签核服务和排课建议页。报名状态出现在输入校验、台账页与分析口径。

MIT License，见 `LICENSE`。
