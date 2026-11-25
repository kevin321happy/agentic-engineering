# M1.1 人工审批与恢复执行计划

**目标**　重启后恢复待审批规格。规格修订后重新审批。补丁执行授权绑定当前获批版本和具体补丁，并且只能消费一次。

**架构**　保留现有 `Spec`、JSON Schema 和 `GateLedger` 的接口，在独立的 `ApprovalStore` 中持久化规格快照、审批记录和授权记录。三个步骤都以可运行的验收测试收尾。实际工作区写入、调用者身份认证和离线回放按后续里程碑接入。

**技术栈**　Python 3.11+、Pydantic 2、标准库 `sqlite3`、pytest。现有依赖和 lockfile 足够。NoteTool 跟踪此次交付的进度和证据。

## 基线与范围

- `feat/core-protocol` 本地基线是 `b9c1456`。2026-11-25 实测 Pytest 12 项通过，Ruff 和 mypy 通过。
- [`Spec`](../../../src/agentic_engineering/core/models.py#L13) 有 `draft` 和 `approved` 字段值。新增存储接口只接受 `draft`，并根据独立审批记录推导已提交版本的审批状态。已发布的 `Spec` 模型和 Schema 继续接受既有数据。
- [`GateLedger`](../../../src/agentic_engineering/runtime/ledger.py#L12) 仍按运行保存并恢复门禁决定。审批表可以与账本共用一个 SQLite 文件，使用独立表，兼容现有数据库。
- [`路线图`](../../../README.zh-CN.md#L38) 把工作区写权限拦截和离线回放列在 M1.2。M1.1 的审批与授权由人工入口显式触发，存储层记录调用方明确传入的操作者。此里程碑验收的是版本与授权状态，不涉及实际文件写入。

## 1. 提交规格版本并跨进程恢复

**文件**　新增 `src/agentic_engineering/core/approval.py`、`src/agentic_engineering/runtime/approval.py` 和 `tests/unit/core/test_approval.py`。

- [ ] 先写 `test_pending_revision_survives_restart`。父进程提交 `run-a` 的 `sp-list@1`，子进程打开同一临时数据库，读出相同引用、规格正文和 `pending` 状态。用 `run-b` 和另一个 `spec_id` 验证隔离。另测两个写入者基于同一旧版本提交时，至多一个可提交成功。
- [ ] 新增冻结的数据模型 `SpecRevisionRef(run_id, spec_id, revision)` 和 `SpecRevision(ref, spec, status)`。复用 `Identifier` 与 `Spec` 的校验。`revision` 为正整数，规格快照一经提交便固定。先跑定向测试，确认缺少接口或持久化行为时失败。
- [ ] 实现以下存储接口。`expected_revision=0` 表示首次提交。后续提交使用已读取的最新版本号。在同一 `BEGIN IMMEDIATE` 事务中检查版本号并插入下一版本。版本冲突抛出 `ValueError`，重试前先读取最新状态。`restore_pending` 只在当前版本待审批时返回该版本。

```python
submit_revision(run_id: str, spec: Spec, *, expected_revision: int) -> SpecRevision
get_revision(ref: SpecRevisionRef) -> SpecRevision | None
restore_pending(run_id: str, spec_id: str) -> SpecRevision | None
```

- [ ] 用 `spec_revisions` 保存快照，以 `(run_id, spec_id, revision)` 为主键。运行 `uv run --locked pytest -q tests/unit/core/test_approval.py`，确认第一组新用例通过。

## 2. 记录人工审批并隔离新旧版本

**文件**　修改上述两个 `approval.py` 和 `test_approval.py`。

- [ ] 先写 `test_changed_spec_requires_fresh_approval`。批准列表空态 v1，提交增加重试按钮和验收条款的 v2。进程重启后，v2 仍为 `pending`，v1 的审批人和审批时间仍可查。对 v1 提交迟到的审批会报版本冲突，v2 直到被单独审批才变为 `approved`。先跑定向测试，确认现有实现缺少审批行为时失败。
- [ ] 新增 `SpecApproval(ref, approved_by, approved_at)` 和 `spec_approvals` 表。每个版本最多一条审批，用外键关联规格快照。审批时间由存储层以 UTC 生成。给 `SpecRevision` 增加 `approval: SpecApproval | None`，查询时从审批记录推导 `pending` 或 `approved`。重复审批当前版本返回原记录，保留最初的审批人和时间。

```python
approve_revision(ref: SpecRevisionRef, *, approved_by: str) -> SpecApproval
```

- [ ] 测试传入 `Spec(status="approved")` 会被提交接口拒绝，`GateLedger` 中现有的 `GO` 也不会生成 `SpecApproval`。运行 `uv run --locked pytest -q tests/unit/core/test_approval.py tests/unit/core/test_models.py`，确认新用例和原 Schema 契约都通过。

## 3. 签发并原子消费一次性授权

**文件**　修改上述两个 `approval.py` 和 `test_approval.py`。

- [ ] 先写授权测试。覆盖待审批时拒绝签发、补丁摘要或版本不符时拒绝消费、旧授权在新版本提交后失效、重试签发获得原授权、重启后仍知道已消费，以及两个独立连接竞争时恰好一个消费成功。断言失败的消费不会用掉原授权。先跑定向测试，确认现有实现缺少授权行为时失败。
- [ ] 新增 `PatchGrant(grant_id, ref, patch_sha256, authorized_by, issued_at, consumed_at)` 和 `patch_grants` 表。用 `uuid4().hex` 生成授权记录 ID。`patch_sha256` 使用补丁原始字节计算并校验格式。签发时要求引用是当前且已经人工批准的版本。数据库以 `(run_id, spec_id, revision, patch_sha256)` 限制同一授权对象只有一条记录，重复调用返回原记录，即使已经消费。

```python
issue_grant(ref: SpecRevisionRef, *, patch_sha256: str, authorized_by: str) -> PatchGrant
consume_grant(grant_id: str, *, ref: SpecRevisionRef, patch_sha256: str) -> bool
```

- [ ] 消费时在同一写事务确认引用仍是最新且已获批的版本，再按授权 ID、版本和补丁摘要执行带 `consumed_at IS NULL` 条件的 `UPDATE`。只有更新一行才返回 `True`。数据库故障向调用方报告，事务回滚。M1.2 的执行器负责对实际执行的补丁字节计算摘要，并处理消费后的应用失败。
- [ ] 运行 `uv run --locked pytest -q tests/unit/core/test_approval.py tests/unit/core/test_checkpoint.py tests/unit/core/test_ledger.py`。再用旧 `GateLedger` 创建数据库，接入审批表后确认原门禁历史可继续读取。

## 完成验收与交接

- [ ] 审阅实际 Diff，核对三项验收与测试的对应关系。检查并发消费、迟到审批和数据库兼容用例。
- [ ] 在代码与验收全部通过后，更新中英文 README 的当前能力及路线图，说明本里程碑的实现边界。
- [ ] 从仓库根目录运行以下检查。三条命令都通过，且上述三项验收都有实测证据后，才把 M1.1 标为完成。

```sh
uv run --locked pytest -q
uv run --locked ruff check .
uv run --locked mypy src
```

- [ ] 通过 NoteTool 记录测试结果、实际提交基线及未解决事项，更新 `checkpoint` 并运行 `validate`。将 M1.2 的工作区写入约束和回放列为下一轮任务。
