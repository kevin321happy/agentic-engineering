# 项目迭代交接

本项目使用 NoteTool 维护当前里程碑、验收条件、验证结果、阻塞和下一步。项目路线以 `README.zh-CN.md` 为准，已完成的工作以实际提交和测试结果为准。写入、合并和发布仍按各自的授权流程处理。

开始一轮实质迭代前，先读 `${XDG_STATE_HOME:-$HOME/.local/state}/agentic-engineering/notetool/RESUME.md`，再核对当前分支、提交和相关实现。该目录尚未配置时，从仓库和路线图恢复上下文。

每轮收尾时，用 `note` 记录实际完成项和验证结果，用 `blocker` 记录需要接力的阻塞，再用 `checkpoint` 更新下一步并运行 `validate`。阶段验收完成后，用 `goal` 和 `phase` 更新里程碑。

在仓库根目录执行以下命令可查看当前阶段并重新生成续跑摘要。脚本默认来自同级的 `agent-hub`，其他目录布局可以设置 `AGENT_HUB_ROOT`。

```sh
note_tool_script="${AGENT_HUB_ROOT:-../agent-hub}/pipeline/e2e-assets/long-lang-ui/notetool.py"
note_tool_root="${XDG_STATE_HOME:-$HOME/.local/state}/agentic-engineering/notetool"
python3 "$note_tool_script" --root "$note_tool_root" phase show
python3 "$note_tool_script" --root "$note_tool_root" resume
```
