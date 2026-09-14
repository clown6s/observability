# LGTM 监控栈（Loki + Grafana + Tempo + Prometheus）+ FastAPI 应用

Loki（日志）+ Prometheus（指标）+ Tempo（链路追踪）+ Grafana（看板），并把 FastAPI 应用一起编排进栈。

## 启动

```bash
cd deploy/lgtm
docker compose up -d --build   # --build 首次需构建应用镜像
```

## 端口

| 服务 | 地址 | 默认账密 |
|---|---|---|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Loki | http://localhost:3100 | - |
| Tempo | http://localhost:3200（OTLP 4317/4318） | - |
| FastAPI 应用 | http://localhost:8000 | - |

Grafana 已自动配置 Loki / Prometheus / Tempo 数据源（`grafana/provisioning/`）。

## 服务清单

| 服务 | 镜像 | 作用 |
|---|---|---|
| `loki` | grafana/loki:3.5.0 | 日志存储（单实例 + 文件存储） |
| `promtail` | grafana/promtail:3.5.0 | 采集所有 docker 容器日志（`docker_sd` 自动发现），直推 Loki |
| `prometheus` | prom/prometheus:v3.5.0 | 抓取应用 `/metrics` 指标 |
| `tempo` | grafana/tempo:2.8.2 | 链路追踪存储（OTLP 接入） |
| `grafana` | grafana/grafana:12.1.1 | 看板 + 数据源 |
| `fastapi-app` | build: ../../Dockerfile | 你的 FastAPI 应用 |

## 各服务说明

- **应用镜像**：`Dockerfile` 在项目根，多阶段构建，容器内 `uvicorn` 运行（无 reload）。
- **日志采集**：promtail 通过 docker socket 自动发现所有容器，应用 stdout 的 JSON 日志按
  `container=fastapi-app` 标签收进 Loki，无需改应用代码。
- **指标抓取**：应用已暴露 `/metrics`（`prometheus_client`），prometheus 按 `fastapi-app:8000` 抓取。
- **链路追踪**：Tempo 暴露 OTLP gRPC(4317)/HTTP(4318)。应用已接入 OpenTelemetry：
  FastAPI 自动埋点（`excluded_urls="/metrics"`），trace 经 `tempo:4317` 推送，
  并把 `trace_id`/`span_id` 注入结构化日志，实现日志↔追踪联动。
- **MySQL**：应用容器通过环境变量连宿主机 `10.211.55.5:3306`（bridge 网络直接可达该 IP）。

## 在 Grafana 里看

- **日志**：Explorer → 选 Loki 数据源 → `{container="fastapi-app"}`
- **指标**：Explorer → 选 Prometheus → 查询如 `python_gc_objects_collected` / `process_cpu_seconds_total`
- **追踪**：Explorer → 选 Tempo 按 trace_id 查；日志里的 `trace_id` 可直接跳转溯源

## 环境变量覆盖

MySQL / ES 连接参数可在 `fastapi-app` 的 `environment` 里覆盖（见 compose），
默认与 `app/core/config.py` 一致。

## 注意

- 构建用 `docker compose up -d --build`；仅改代码不重建时会用旧镜像，需显式 `--build`。
- 宿主机跑（非容器）的方式已被容器化取代；如需裸进程方案见 git 历史。
