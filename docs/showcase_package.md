# 技术展示材料包

这个目录用于集中说明项目的功能、架构、演示方式和技术实现，方便快速了解项目完整性。

## 项目展示材料

- `README.md`：项目首页说明，包含功能、启动方式、截图和 API 概览。
- `docs/architecture.md`：系统架构说明。
- `docs/architecture_diagram.md`：Mermaid 架构图和时序图。
- `docs/screenshots/`：功能截图。

## 技术说明材料

- `docs/project_summary.md`：项目定位、技术要点和可展示能力。
- `docs/technical_walkthrough.md`：项目讲解、实现思路和扩展方向。
- `docs/demo_script.md`：功能演示脚本。
- `docs/final_checklist.md`：功能与工程检查清单。

## 推荐展示标题

PromptOps 评测与 Prompt 优化平台

## 一句话说明

基于 FastAPI + SQLite 实现的 PromptOps 评测平台，支持 Prompt 版本管理、测试集管理、批量运行、自动评分、人工复核、失败案例分析、版本对比和成本耗时统计，并支持无 API Key 的 Mock 演示模式。

## 推荐讲解方式

这个项目可以从“Prompt 也需要工程化管理”切入。先说明普通 AI Demo 只展示一次输出，而 PromptOps 更关注稳定性、可评测性和持续优化。再按页面流程展示 Prompt 版本、测试集、批量运行、评分、失败分析和版本对比，最后说明 Mock 模式如何保证项目可复现，以及未来如何接入真实模型供应商。
