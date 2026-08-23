# PulseBudget

**电池寿命的 Git diff。** PulseBudget 把电流分析仪导出的 CSV 轨迹变成可解释的固件功耗差异、
可审阅报告和可阻断 CI 的功耗预算门禁。

[English](README.md) · [输入与报告格式](docs/FORMAT.md) ·
[故障修复手册](docs/TROUBLESHOOTING.md) · [调研记录](docs/RESEARCH.md)

![PulseBudget 对比仓库内置的嵌入式设备电流轨迹](docs/demo/comparison.svg)

仓库内置示例检测到平均电流上升 **31.81%**，并把全部 `+0.04988 mA` 精确拆成：

| 原因 | 贡献 |
| --- | ---: |
| 空闲漂移 | +0.03014 mA |
| 脉冲幅度升高 | +0.00869 mA |
| 脉冲活动或时序变化 | +0.01106 mA |

三项之和必须等于真实测得的平均电流差；这不是凭规则随便贴标签。

## 它解决什么问题

固件改动可能通过所有功能测试，却悄悄缩短电池寿命。电流分析仪能画出波形，但代码审查时仍常常
只能对照两张截图或两个平均值。PulseBudget 直接读取已有 CSV，回答：

- 候选固件是否超过版本库中的功耗预算？
- 增量来自空闲电流、脉冲强度，还是脉冲活动/时序？
- CI 和人工审查能否查看同一份、可重复生成的证据？

运行时只依赖 Python 标准库，不需要账号、云上传、指定厂商硬件或专有工程格式。

## 快速开始

从 [最新 Release](https://github.com/KanadeK/pulsebudget/releases/latest) 下载
`pulsebudget-0.1.0.pyz` 和 `pulsebudget-0.1.0-examples.zip`，解压示例后执行：

```bash
python pulsebudget-0.1.0.pyz compare examples/baseline.csv examples/candidate.csv \
  --budget examples/budget.json \
  --output pulsebudget-report
```

Python 3.11 或更高版本即可，不需要安装软件包。预期输出：

```text
PASS: all applicable budget limits passed
```

输出目录包含机器可读的 `report.json`、适合贴进 PR 的 `report.md`，以及自包含的
`comparison.svg`。改用 `examples/budget-strict.json` 会触发 10% 回归上限，并以退出码 `1`
留下完整失败证据。

从源码运行：

```bash
git clone https://github.com/KanadeK/pulsebudget.git
cd pulsebudget
uv sync --all-extras --frozen
uv run pulsebudget compare examples/baseline.csv examples/candidate.csv \
  --budget examples/budget.json \
  --output pulsebudget-report
```

## 命令与退出码

```bash
pulsebudget analyze trace.csv --budget budget.json --output report
pulsebudget compare baseline.csv candidate.csv --budget budget.json --output report
```

厂商导出的表头和单位不同，不必先修改源文件：

```bash
pulsebudget analyze measurement.csv --budget budget.json --output report \
  --time-column "Timestamp (us)" --current-column "Current (uA)" \
  --time-unit us --current-unit ua
```

| 退出码 | 含义 |
| ---: | --- |
| `0` | 所有适用预算均通过。 |
| `1` | 输入有效、报告已生成，但至少一个预算失败。 |
| `2` | 命令、CSV、预算或输出位置无效。 |

## 输入与计算

默认 CSV 只有两列：

```csv
time,current
0,0.12
5.002,25
5.010,25
5.012,0.12
```

时间必须有限、非负、严格递增；电流必须有限且非负。默认单位是秒和毫安，也可明确指定
`s/ms/us` 与 `a/ma/ua`。

预算是严格 JSON。未知字段会直接报错，拼错的门限不会悄悄失效。支持平均电流、峰值、按时间
加权 p95、平均回归比例和最低估算续航。完整格式见 [docs/FORMAT.md](docs/FORMAT.md)。

计算约定：

- 用真实时间戳做梯形积分；
- p95 按分段线性信号所占时间计算，不按 CSV 行数计算；
- 脉冲边界是阈值的精确线性交点；
- 两条轨迹归一化到 `0..1` 进度后合并所有节点，再积分并完成三类精确归因；
- 续航只是透明的上界估算，不冒充电池化学模型。

## 接入 CI

```yaml
- name: Gate firmware power regression
  run: >-
    python -m pulsebudget compare
    power/baseline.csv power/candidate.csv
    --budget power/budget.json
    --output power/report
- name: Upload PulseBudget evidence
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: pulsebudget-report
    path: power/report/
```

退出码 `1`（真实预算回归）和 `2`（测量流水线或输入损坏）被刻意分开，CI 可以采取不同处理。

## 明确边界

v0.1.0 不负责硬件采集、阈值猜测、电池化学、语义事件对齐、去噪或多次实验的统计显著性。
输入应当是可比较、已经准备好的轨迹，并由项目显式定义预算。噪声较大的实验，应先生成聚合轨迹或
选择有代表性的采样。

[调研记录](docs/RESEARCH.md)列出了相邻项目和差异边界。项目针对的是具体未闭合工作流，但任何人
都无法保证 Star 数量。

## 验收与修复

```bash
uv sync --all-extras --frozen
uv run python scripts/release_check.py
```

这条命令会覆盖代码规范、严格类型、测试与覆盖率、真实示例的通过/失败路径、wheel/sdist、独立
`.pyz`、示例包和发布清单。如果失败，按
[故障修复手册](docs/TROUBLESHOOTING.md)定位后，重新执行同一条验收命令。

实现契约见 [docs/SPEC.md](docs/SPEC.md)，核心数值模型见
[ADR 0001](docs/decisions/0001-piecewise-linear-trace-model.md)。参与贡献前请阅读
[CONTRIBUTING.md](CONTRIBUTING.md)。项目使用 [MIT License](LICENSE)。
