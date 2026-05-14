# agent-checkpoint

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Runtime: Python 3](https://img.shields.io/badge/runtime-python3-blue.svg)](https://www.python.org/)
[![State: Repo Local](https://img.shields.io/badge/state-repo--local-2ea44f.svg)](#工作原理)
[**English**](./README.md) | **中文**

面向编码 agent 的仓库内连续性技能。

这两个 skill 专门解决一个高频问题：会话断了、模型切了、机器换了，但你又
不想重新花半小时把上下文捋一遍。它们会把真实工作主线直接落进仓库里，并在
下次重开时快速恢复。

## 演示

![repo-checkpoint 和 repo-resume 的终端演示](./assets/demo.gif)

## 它能做什么

- **repo-checkpoint** —— 在 `.agents/checkpoints/` 下写入带时间戳的
  Markdown 交接文档，内容包括会话目标、当前状态、关键聊天上下文、涉及文件、
  验证状态、下一步和 git 快照。
- **repo-resume** —— 基于最新 checkpoint、当前分支、工作区状态和最近提交，
  快速恢复当前主线。

**为什么需要它：** 大多数 agent 都能重新读代码，但真正容易丢的是“人类
上下文”—— 用户真实目标、已经试过什么、哪些约束不能破、接下来最该做什么。

## 为什么它有价值

- **进度保存在仓库里，不保存在会话里** —— 浏览器重开、模型切换、shell 断开、
  换电脑，这些都不会让交接信息消失。
- **纯 Markdown，无锁定** —— 普通编辑器能看，git 能跟踪，团队也能直接读。
- **恢复路径很短** —— 不用大范围重新扫仓库，先回到最近一次明确主线。
- **保存的不只是代码状态** —— 目标、约束、排除路线、验证状态和下一步都会写明。
- **没有 agent runtime 也能用** —— 两个脚本都可以直接手动执行。

## 最适合的场景

- 长时间调试、排障、重构
- 做到一半被打断，下一轮要立刻续上
- 本地、远程机器、另一台电脑之间来回切
- “代码我能看懂，但我不知道当时为什么这么做”的项目

## 1 分钟上手

```bash
git clone https://github.com/hotalexnet/agent-checkpoint.git
cd agent-checkpoint
bash install-repo-skills.sh
```

然后去目标仓库根目录执行：

```bash
# 结束前：先生成骨架，再把 TODO 填完整
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py \
  --title "chat-routing-root-cause"

# 下次重开：直接恢复最近主线
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

## 使用流程示意

```text
会话 A：
- 正在排查一个路由问题
- 开着多个文件
- 已经排除过一条错误方向
        ↓
repo-checkpoint
        ↓
.agents/checkpoints/20260513-114233-chat-routing-root-cause.md
        ↓
后续会话 B 在同机或另一台机器上启动
        ↓
repo-resume
        ↓
最新 checkpoint + 当前分支 + 工作区 + 最近提交
        ↓
直接从真实下一步继续，而不是重新猜当时的意图
```

## 会保存哪些信息

每个 checkpoint 固定包含这些一级章节：

- `Session Goal`
- `Current State`
- `Key Chat Context`
- `Files In Play`
- `Verification`
- `Next Step`
- `Resume Recipe`
- `Git Snapshot`

这就是它和“只看代码恢复上下文”之间的本质差异：它保存的是围绕代码的决策
状态，而不只是代码本身。

## Checkpoint 内容示例

```md
## Session Goal
- 修掉 chat fallback 污染，避免未命中问题继续吐出过期 onboarding 引导文案。

## Current State
- 路由修复已在本地落地。
- 本地 smoke test 已通过。
- 预发环境行为还需要单独验证。

## Key Chat Context
- 用户要的是根因级清理，不是补几个关键词。
- 旧版 onboarding 文案不能再泄漏到正常聊天回复。
- 先不扩展到换模型问题。

## Files In Play
- src/chat/router.py
- src/prompts/chat_prompt.py
- tests/test_chat_router.py

## Next Step
1. 对当前部署链路做复现。
2. 用 3 个代表性问题验证 fallback 选择。
3. 确认坏路径消失后再提交。
```

## 安装

### 前置要求

- `python3`
- `git`
- 一个会从 `~/.agents/skills` 加载 skill，或支持 vendored skill 路径的 agent 运行环境

### 方式 1：执行安装脚本

```bash
bash install-repo-skills.sh
```

默认安装目录：

```bash
~/.agents/skills
```

自定义安装目录：

```bash
bash install-repo-skills.sh --target /path/to/skills
```

### 方式 2：克隆仓库

```bash
git clone https://github.com/hotalexnet/agent-checkpoint.git
cd agent-checkpoint
bash install-repo-skills.sh
```

### 方式 3：直接拷贝 skill 目录

```bash
mkdir -p ~/.agents/skills
cp -R repo-checkpoint ~/.agents/skills/
cp -R repo-resume ~/.agents/skills/
```

## 使用方式

| 触发语或需求 | 动作 |
|--------------|------|
| “保存进度” / “打个 checkpoint” | 运行 `repo-checkpoint` |
| “继续刚才那条主线” / “我上次在这里做到哪了” | 运行 `repo-resume` |
| “列出所有 checkpoint” | 运行 `repo-resume list` |
| “清理旧 checkpoint” | 运行 `repo-resume prune 5` |

在目标仓库根目录手动执行：

```bash
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "my-work"
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py list
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py prune 5
```

## 推荐工作流

### 1. 结束前

先跑 `repo-checkpoint`，然后把所有 `TODO` 替换成这轮真实状态。

### 2. 下次重开时

先跑 `repo-resume`，再决定要不要大范围看仓库。

### 3. 保证 checkpoint 可执行

一个好的 checkpoint，应该让下一轮快速回答这些问题：

- 我们到底要完成什么？
- 现在已经确认了什么？
- 哪些东西绝对不能破？
- 先看哪些文件最有效？
- 下一步应该做什么？

## 为什么 repo-local 比外部聊天记忆更稳

- 外部会话记忆常常不可用、残缺，或者和某个工具强绑定
- 仓库内交接文档会跟着代码一起走
- 团队成员和未来的自己都能直接查看，不依赖特殊平台
- 你可以像管理普通文件一样管理这些 checkpoint：提交、忽略、归档、拷贝

## 工作原理

```text
当前编码会话
    ↓
repo-checkpoint
    ↓
在 .agents/checkpoints/ 下写入带时间戳的交接文档
    ↓
后续新会话启动
    ↓
repo-resume
    ↓
读取最新 checkpoint + 当前 git 状态
    ↓
以最小冷启动成本继续原来的主线
```

## 兼容性

- 任何 git 仓库
- 本地机器或远程服务器
- 支持跨机器复用
- 即使 agent runtime 不自动加载 skill，也可以直接手动跑脚本

## 多机器使用

你可以：

- 在另一台机器上 clone 本仓库再执行安装脚本，或者
- 直接把 `repo-checkpoint/` 和 `repo-resume/` 拷到那台机器的
  `~/.agents/skills/`

## 更新方式

如果已经安装过旧版本，重新执行：

```bash
bash install-repo-skills.sh
```

安装脚本会覆盖：

- `~/.agents/skills/repo-checkpoint`
- `~/.agents/skills/repo-resume`

## 边界和限制

- 恢复质量取决于 checkpoint 质量。
- 这个骨架是刻意保持简单的，它不会替你自动总结整轮会话。
- 如果 `TODO` 没填，下一轮仍然要靠人自己补意图。

## .gitignore 建议

Checkpoint 保存在 `.agents/checkpoints/` 下。你可以选择提交到 git（方便团队成员互相恢复上下文），也可以选择 gitignore（当个人笔记用）：

```gitignore
# 方式 A：忽略所有 checkpoint
.agents/checkpoints/

# 方式 B：提交到 git — 不需要加任何 .gitignore 规则
```

## 项目结构

```text
agent-checkpoint/
├── README.md
├── README.zh-CN.md
├── CHANGELOG.md
├── VERSION
├── LICENSE
├── assets/
│   └── demo.gif
├── install-repo-skills.sh
├── dist/
│   └── repo-skills-bundle.tar.gz
├── repo-checkpoint/
│   ├── SKILL.md
│   └── scripts/
│       └── save_checkpoint.py
├── repo-resume/
│   ├── SKILL.md
│   └── scripts/
│       └── resume_snapshot.py
├── tests/
│   ├── conftest.py
│   ├── test_checkpoint.py
│   └── test_resume.py
└── scripts/
    └── generate_demo_gif.py
```

## 许可证

[MIT License](LICENSE)

## 致谢

- 长程编码会话中沉淀出来的 repo-local continuity 工作流
- Git，让分支状态和工作区状态可以被稳定地记录和恢复

---

⚠️ **说明：** 文件、约束、验证状态和下一步写得越具体，恢复速度就越快，
这个 skill 的价值也就越高。
