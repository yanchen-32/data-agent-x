# DataAgentX Project Charter

## 1. Project Goal

DataAgentX 是一个面向企业数据异常调查与根因分析的、可验证、可评测、具备长期记忆能力的 AI Agent。

核心能力：

`Plan → Retrieve → Act → Remember → Verify`

项目目标不是构建通用聊天机器人，而是证明完整的大模型 Agent 工程化落地能力。

## 2. Core Scenario

核心业务场景：Data Investigation / Root-Cause Analysis。

典型问题：

> 最近一周西北地区退款率明显上涨，定位主要原因并给出证据，同时参考历史类似事件。

Agent 应能够：

1. 理解调查目标
2. 获取指标定义
3. 查询 Schema
4. 制定调查计划
5. 调用 SQL / Python / RAG / Memory
6. 验证证据
7. 必要时重新规划
8. 输出 Evidence-Grounded Report

## 3. Architecture Principles

- **Python**：负责 Agent Runtime、RAG、Memory、Evaluation、LLM。
- **Go**：负责 Gateway、SSE、并发、Timeout、Cancellation、Rate Limit、Graceful Shutdown。
- **Text-to-SQL**：属于 Must Have Tool，而不是项目主体。
- **Long-Term Memory**：属于 Agent 长期状态管理模块，而不是独立比赛项目。

## 4. Must Have

- Python Engineering
- Native Agent Runtime
- Tool System
- SQLTool
- Hybrid RAG + Reranker
- Data Investigation
- Evidence-Grounded Report
- Long-Term Memory Engine
- Evaluation
- Go Gateway
- Reliability
- Basic Observability
- Docker / CI
- Go Gateway Performance Experiment
- Final Benchmark

## 5. Should Have

- MCP Adapter
- Context Budget Manager
- Prometheus / Grafana
- Redis（存在明确需求时）
- Advanced Text-to-SQL Recovery
- OSS Contribution

## 6. Nice to Have

- Memory Forgetting
- Memory Consolidation / Compression
- Model Router
- Better Web UI

## 7. Explicit Non-Goals

当前不以以下内容为核心目标：

- Kubernetes
- Kafka
- Service Mesh
- 大规模 Multi-Agent
- 复杂前端
- 大规模模型训练
- 为增加技术栈而增加中间件

## 8. Long-Term Memory Must Have

1. Structured Memory Record
2. Memory Extraction
3. Memory Retrieval
4. Memory Write Policy
5. Temporal & Conflict Manager
6. Memory Evaluation

Memory 模块不与 KunMem、鲲鹏、昇腾、openEuler 或任何特定硬件平台绑定。

## 9. Evaluation Philosophy

功能完成不等于项目完成。主要模块必须通过真实 Benchmark 验证。

至少比较：

- Direct LLM
- Workflow
- Agent
- Agent + RAG
- Agent + RAG + Memory

禁止预设实验结果。

## 10. Go Gateway Experiment

必须比较：

```text
Python-only:
Client → FastAPI → Agent

Go Gateway:
Client → Go Gateway → FastAPI → Agent
```

指标包括：

- QPS
- P50 / P95 / P99
- CPU
- RSS Memory
- Error Rate
- Cancellation Resource Waste

Go 不要求必须优于 Python。目标是识别真实系统瓶颈。

## 11. Success Criteria

项目成功不是“功能很多”，而是：

- 能独立解释 Agent Runtime
- RAG 有真实评测结果
- Memory 有真实对照实验
- Root-Cause Benchmark 可复现
- Go Gateway 有性能实验
- Failure cases 有测试
- 系统可通过 Docker 复现
- README 可供其他人运行
- 能支撑 20～30 分钟技术面试深挖

## Change Policy

本文件应尽量少改。只有项目定位、核心边界或成功标准真正发生变化时才修改。
