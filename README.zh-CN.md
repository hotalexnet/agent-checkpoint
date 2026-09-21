# agent-checkpoint

[![许可证：MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![运行环境：Python 3](https://img.shields.io/badge/runtime-python3-blue.svg)](https://www.python.org/)
[![版本：0.4.0](https://img.shields.io/badge/version-0.4.0-2ea44f.svg)](VERSION)

[English](./README.md) | **中文**

面向编码 Agent 的仓库内连续性工具。它把目标、决策、涉及文件、验证结果和
下一步写入 `.agents/checkpoints/`，这样即使会话中断、切换模型或更换机器，
也能继续同一条工作主线。

Checkpoint 使用共享的 Markdown 格式，可供 Codex/OpenAI CLI、Claude Code、
opencode 以及其他能读取 Markdown 的 Agent 使用。

## 演示

![repo-checkpoint 和 repo-resume 的终端演示](./assets/demo.gif)

基本流程很简单：会话结束时保存交接信息；下次开始时，先读取交接信息，再继续
处理代码。

## 快速开始

前置要求：Python 3、Git 和 Bash。

```bash
git clone https://github.com/hotalexnet/agent-checkpoint.git
cd agent-checkpoint
bash install-repo-skills.sh
```

在任意 Git 仓库根目录执行：

```bash
# 会话结束：生成交接模板，并把 TODO 填成真实状态。
python3 ~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py \
  --title "chat-routing-root-cause" --agent codex

# 下次开始：恢复当前工作主线。
python3 ~/.agents/skills/repo-resume/scripts/resume_snapshot.py
```

## 安装了什么

安装脚本会把两个独立 skill 放到 `~/.agents/skills/`：

- `repo-checkpoint`：在 `.agents/checkpoints/` 下创建 Markdown 交接文档。
- `repo-resume`：读取当前交接文档、Git 状态、分支和最近提交。

即使没有 Agent runtime，也可以直接运行这两个脚本。

## 常用命令

以下命令都应在目标仓库根目录执行。

为便于阅读，表格省略了 `python3 ~/.agents/skills/.../scripts/` 前缀；实际复制
到终端时，请参考下面的完整示例。

| 需求 | 命令 |
| --- | --- |
| 创建带时间戳的 checkpoint | `save_checkpoint.py --title "work"` |
| 更新当前主线 | `save_checkpoint.py --current --title "active-lane"` |
| 让 checkpoint 永不过期 | `save_checkpoint.py --expires-in 0` |
| 恢复当前主线 | `resume_snapshot.py` |
| 列出 checkpoint 和状态 | `resume_snapshot.py list` |
| 检查结构和元数据 | `resume_snapshot.py validate` |
| 同时拒绝未完成的 `TODO` | `resume_snapshot.py validate --strict` |
| 保留最新五个快照 | `resume_snapshot.py prune 5` |

例如：

```bash
CHECKPOINT=~/.agents/skills/repo-checkpoint/scripts/save_checkpoint.py
RESUME=~/.agents/skills/repo-resume/scripts/resume_snapshot.py

python3 "$CHECKPOINT" --current --title "fix-login-flow" --agent codex
python3 "$RESUME" validate
python3 "$RESUME" list
```

生成的文件只是交接模板。把所有 `TODO` 换成这轮真实信息后，再交给下一个
Agent 或下次会话使用。

## 0.4.0 的主要功能

- **当前主线：** `--current` 会原子地更新
  `.agents/checkpoints/current.md`；恢复时优先读取它。
- **过期检测：** 新 checkpoint 默认 30 天后过期；使用 `--expires-in 0`
  可关闭过期时间。
- **Git 关联：** 记录创建时的分支和 base commit，并提示分支不匹配或提交不存在。
- **敏感信息脱敏：** 自动生成的字段在写入前会处理常见密码、Token、API Key、
  Bearer 凭据、私钥和带认证信息的 URL。手动填写的内容仍需自行检查。
- **checkpoint 校验：** `validate` 检查 frontmatter、固定章节、过期时间、凭据和
  base commit；`--strict` 还会拒绝 `TODO`。
- **安全写入：** 先写入临时文件，再原子替换目标文件，避免半写入。

没有新元数据的旧版时间戳 checkpoint 仍然可以读取，并会显示为 `legacy`。

## checkpoint 保存什么

每个 checkpoint 包含以下固定章节：

```text
Agent Handoff       谁可以恢复，以及如何恢复
Session Goal        需要完成什么
Current State       当前已经确认的状态
Key Chat Context    用户目标和约束
Files In Play       需要优先关注的文件和路径
Verification        已经执行过的测试和检查
Next Step           下一步可执行动作
Resume Recipe       标准恢复命令
Git Snapshot        工作区和最近提交
```

这些文件就是普通 Markdown，可以像其他项目文件一样查看、编辑、提交、忽略、
复制或归档。

## 安装和升级

安装到自定义目录：

```bash
bash install-repo-skills.sh --target /path/to/skills
```

从本地克隆目录升级：

```bash
bash upgrade-repo-skills.sh
```

直接从 GitHub 升级：

```bash
bash <(curl -fsSL \
  https://raw.githubusercontent.com/hotalexnet/agent-checkpoint/main/upgrade-repo-skills.sh)
```

测试当前 checkout 时可以使用 `--no-pull`；使用 `--target DIR` 可以指定其他
安装目录。安装脚本会先备份已有的 skill 目录，再进行替换。

## 跨 Agent 和多机器使用

交接格式不绑定某个工具，典型流程如下：

1. Agent A 运行 `save_checkpoint.py`，并填写交接内容。
2. 根据隐私需要，提交 checkpoint、复制到其他机器，或只保留在本地。
3. Agent B 在同一个仓库中运行 `resume_snapshot.py`。

在另一台机器上，可以重新 clone 本项目并执行安装脚本，也可以把
`repo-checkpoint/` 和 `repo-resume/` 目录复制到对应的 skill 目录。

## 隐私和 Git 建议

Checkpoint 可能包含项目名称、路径、任务细节和 Git 输出。程序会脱敏常见的
凭据格式，但任何基于规则的扫描器都不能保证识别所有秘密。提交前请人工检查。

如果不希望把个人交接记录提交到 Git，可以加入：

```gitignore
.agents/checkpoints/
```

如果需要团队共享，就像普通 Markdown 文件一样提交 checkpoint。

## 限制

- 恢复质量取决于 checkpoint 是否写得具体。
- 工具不会自动总结整轮会话。
- 没有填写完的 `TODO` 只是模板，不是完整交接文档。
- 项目面向 Git 仓库，需要 Python 3 和 Git。

## 开发和测试

在项目根目录执行：

```bash
pytest -q
bash -n install-repo-skills.sh upgrade-repo-skills.sh
python3 -m compileall -q repo-checkpoint repo-resume tests
git diff --check
```

## 项目结构

```text
agent-checkpoint/
├── install-repo-skills.sh
├── upgrade-repo-skills.sh
├── repo-checkpoint/
│   ├── SKILL.md
│   └── scripts/
│       ├── redact.py
│       └── save_checkpoint.py
├── repo-resume/
│   ├── SKILL.md
│   └── scripts/
│       ├── redact.py
│       └── resume_snapshot.py
├── tests/
├── assets/demo.gif
├── CHANGELOG.md
└── VERSION
```

## 许可证

[MIT License](LICENSE)
