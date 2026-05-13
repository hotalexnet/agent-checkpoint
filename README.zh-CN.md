# repo-continuity-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[**English**](./README.md) | **中文**

面向编码 agent 的仓库内连续性技能。这两个 skill 用来把当前工作进度直接
保存到仓库里，并在下次重开会话时快速恢复，不依赖脆弱的外部聊天上下文。

## 它能做什么

- **repo-checkpoint** —— 在 `.agents/checkpoints/` 下写入带时间戳的
  Markdown 交接文档，内容包括会话目标、当前状态、关键聊天上下文、涉及文件、
  验证状态、下一步和 git 快照。
- **repo-resume** —— 基于最新 checkpoint、当前 git 分支、工作区状态和
  最近提交，快速恢复当前主线。

**为什么需要它：** 大多数 agent 都能重新读代码，但真正容易丢的是“人类
上下文”—— 用户真实目标、已经试过什么、哪些约束不能破、接下来最该做什么。

## 特性

- 进度直接保存在仓库内的 `.agents/checkpoints/`
- 恢复时优先走最新交接文档，而不是重新大范围扫仓库
- 同时保存代码状态和用户/项目上下文
- 适合跨机器复用，只要仓库和 skill 目录都在即可
- 不需要数据库、后台服务或云端依赖
- 只依赖 `python3` 和 `git`

## 安装

### 前置要求

- `python3`
- `git`
- 一个会从 `~/.agents/skills` 或等价 vendored 路径加载 skill 的 agent 运行环境

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
git clone https://github.com/hotalexnet/repo-continuity-skills.git
cd repo-continuity-skills
bash install-repo-skills.sh
```

### 方式 3：直接拷贝 skill 目录

```bash
mkdir -p ~/.agents/skills
cp -R repo-checkpoint ~/.agents/skills/
cp -R repo-resume ~/.agents/skills/
```

## 使用方式

### repo-checkpoint

适合这些场景：

- “保存进度”
- “打个 checkpoint”
- “把当前这条 lane 记下来”
- “关之前把关键上下文落一下”

在目标仓库根目录手动执行：

```bash
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py --title "my-work"
```

### repo-resume

适合这些场景：

- “恢复上次进度”
- “继续刚才那条主线”
- “把当前 lane 找回来”
- “我上次在这里做到哪了”

在目标仓库根目录手动执行：

```bash
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

## 推荐工作流

### 1. 结束前

执行或触发 `repo-checkpoint`。

### 2. 下次重开时

执行或触发 `repo-resume`。

### 3. 保证 checkpoint 可执行

一个好的 checkpoint，应该能让下一轮会话快速回答这些问题：

- 我们到底要完成什么？
- 现在已经确认了什么？
- 哪些东西绝对不能破？
- 先看哪些文件最有效？
- 下一步应该做什么？

## 输出示例

典型的 checkpoint 文件会长这样：

```text
.agents/checkpoints/2026-05-12-ship-docs.md
.agents/checkpoints/2026-05-13-chat-routing-fix.md
```

具体文件名由 checkpoint 脚本自动生成。

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
读取最新 checkpoint + 当前 git 状态 + 活跃文件
    ↓
以最小冷启动成本继续原来的主线
```

## 多机器使用

这个仓库天然适合跨机器复用。

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

## 项目结构

```text
repo-continuity-skills/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── install-repo-skills.sh
├── dist/
│   └── repo-skills-bundle.tar.gz
├── repo-checkpoint/
│   ├── SKILL.md
│   └── scripts/
│       └── save_checkpoint.py
└── repo-resume/
    ├── SKILL.md
    └── scripts/
        └── resume_snapshot.py
```

## 许可证

[MIT License](LICENSE)

## 致谢

- 长程编码会话中沉淀出来的 repo-local continuity 工作流
- Git，让分支状态和工作区状态可以被稳定地记录和恢复

---

⚠️ **说明：** 这两个 skill 的价值，很大程度取决于 checkpoint 写得是否
具体。文件、约束、验证状态和下一步越明确，恢复速度就越快。
