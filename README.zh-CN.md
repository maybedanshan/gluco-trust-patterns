# GlucoTrust

**当前研究版本 v0.2.0：** Python 3.12 安装 `requirements-repro.txt` 后，运行 `python reproduce.py full` 完整复现所有模块；缺少原始数据时显式添加 `--download`。旧版 ZIP 保留。

**最新共同实验：** [选参模型的历史缺失与误差分解](docs/SELECTED_HISTORY_RESULTS.md) · [交互研究页面](docs/demo/research.html)。复用旧模型的缺失掩码和测试餐次，分别报告可用餐次减少与保留餐次特征损坏的诊断性贡献；历史标签仍完整。运行 `python reproduce.py selected-history` 后用 `python reproduce.py dashboard` 更新展示。

**新增模型核查：** [训练参与者内部选参与个人历史均值基线](docs/MODEL_COMPARISON_RESULTS.md)。运行 `python reproduce.py compare`；外层测试参与者不参与选参。第一版固定参数结果与缺失实验保持原样。

**两个模块的共同实验：** [历史输入缺失与个体化预测](docs/HISTORY_MISSINGNESS_RESULTS.md)已完成。固定历史标签与后期测试餐次，仅损坏历史餐前 CGM 输入；运行 `python reproduce.py history` 可复现。夜间缺失必须结合实际餐前输入覆盖率解释。

**GlucoPatterns 首次实验：** [实验协议](docs/GLUCOPATTERNS_PROTOCOL.md)与[餐次审查／模型比较报告](docs/GLUCOPATTERNS_RESULTS.md)已完成。安装 `requirements-patterns.txt` 后运行 `python reproduce.py patterns`。这是处理后曲线上的回顾性基准，不能视为已验证的实时预测能力。

**新增研究分析：** [参与者配对比较与置信区间](docs/PAIRED_RESULTS.md)已完成。运行 `python reproduce.py paired` 可从现有实验结果复现；以参与者为单位进行 10,000 次 bootstrap，不把随机种子当成独立样本。这是查看 v0.1 结果后的探索性扩展，尚未发布为 v0.2。

**v0.1 发布入口：** [英文 README](README.md) · [交互图表](docs/demo/index.html) · [英文结果报告](docs/RESULTS.md) · [数据许可](docs/DATA_LICENSES.md)。

无需数据即可运行 `python reproduce.py demo`；已有本地数据时运行 `python reproduce.py all`，随后用 `python reproduce.py release` 生成发布包。下载数据须显式加 `--download`，详细环境说明见 [复现指南](docs/REPRODUCIBILITY.md)。餐后预测保留为下一阶段。

一个研究连续血糖数据缺失如何改变报告指标的可复现实验原型。

**状态：CGMacros 缺失与稳健性实验、ShanghaiT2DM 外部验证、PhysioCGM 时间缺口审查已运行。** 不用于诊断或治疗决策。CGMacros CSV 已经过一分钟处理且含插值特征，当前实验只研究发布曲线的额外缺失，不代表原始设备掉线。

研究问题：在相同删点比例下，随机缺失、单段连续断连和特定时段缺失，是否产生不同的平均血糖与范围内时间偏差？

## 快速运行

Python 3.10+，无第三方依赖。在仓库目录运行：

```sh
python -m unittest discover -s tests -v
python glucotrust.py
```

打开 `outputs/demo/index.html` 查看可筛选的离线演示；`report.md` 为汇总报告，`results.json` 保存逐参与者、比例、模式、种子的结果、删除位置、输入与代码哈希。默认 6 个合成参与者、7 天、3 个比例、3 种模式、10 个种子，共 540 次实验。重复执行会覆盖同一输出目录，请用 `--out` 区分实验。

## 方法边界

- 默认范围为 70–180 mg/dL（含边界），参考 [国际 TIR 共识](https://pmc.ncbi.nlm.nih.gov/articles/PMC6973648/)。仅固定实验定义，不代表所有人群的临床目标。
- 平均血糖与 TIR 均按时间加权。原始读数 i 的支持时间为 `min(t[i+1]-t[i], cap)`，默认 cap 为 5 分钟；末尾读数权重为零。删除后保留原始权重，不跨断连插值、不扩大相邻读数的支持时间。
- 这是左端常值、有限支持的估计约定，不是共识规定的唯一算法。应按设备采样间隔设置 cap，并开展敏感性分析。
- 参考值来自原始数据的可观测支持；已有缺失不视为已知真值，原始长间隔中超过 cap 的时间不进入分母。
- 删除比例按有时间支持的读数个数定义，四舍五入后记录实际比例。**不规则采样下，相同删点比例不等于相同缺失时间比例。** 输出同时记录两者；真实数据主实验应使用规则采样的合格窗口，或扩展时间预算匹配后再声称同等时间缺失。
- `random`：不放回随机删点；`block`：随机起点的一段连续读数；`night`：每天 00:00–06:00 内随机删点，属于时段限制模式，并非每夜完整断连。夜间容量不足时直接报错。
- 时段按输入时间戳所表示的本地小时解释；同一参与者必须使用一致时区、严格递增且无重复的时间戳。跨夏令时应先在上游统一时间处理。
- 偏差为删除后减参考值。TIR 误差用**百分点**，平均血糖误差用 mg/dL。报告先跨种子再跨参与者汇总绝对误差，保留所有有符号误差以审查抵消与种子稳定性。
- 多个种子不是独立参与者；当前报告不做显著性推断。合成曲线只有演示用途。

## CGMacros 真实发布数据

```sh
python fetch_cgmacros.py
python run_cgmacros.py
```

下载器从 PhysioNet 固定版本通过 HTTP Range 仅取 45 份参与者 CSV，不下载餐食照片。已下载文件通过 CRC 检查后可复用；如服务器不支持 Range，可完整下载官方 ZIP，再使用 `python fetch_cgmacros.py --zip /path/to/archive.zip`。逐文件校验值保存在 `data/local/cgmacros/raw/manifest.json`。Range 模式仅验证成员 CRC 并记录 SHA256，不声称验证整个官方 ZIP 的 SHA256。

运行器检查源文件 SHA256，筛选双设备共同完整的最早 24 小时，使用同一窗与同一删除掩码。生成：

- `outputs/cgmacros/report.md`：双设备缺失实验、跨种子稳定性与描述性一致性报告。
- `outputs/cgmacros/dexcom/index.html` 和 `libre/index.html`：逐参与者交互结果。
- `data/local/cgmacros/prepared/audit.json`：每人筛选结果、采样间隔分布、排除原因与设备比较。

这里每点支持 **1 分钟**，而非设备原生的 5/15 分钟，因输入是发布后的一分钟曲线。不能通过抽取每第 5/15 行宣称恢复了原始测量。时间戳按天脱敏平移，保留同一序列相对间隔，不用于真实日历分析。更多数据版本、许可与研究边界见 [数据说明](docs/DATASETS.md)。

## 稳健性、外部验证和餐次审查

```sh
python audit_cgmacros.py
python -m pip install -r requirements-data.txt
python inspect_sources.py
python fetch_external.py
python shanghai.py
python audit_physio.py
python -m unittest discover -s tests -v
```

核心与 CGMacros 实验无需第三方依赖；上海 XLS/XLSX 读取需要可选依赖。`inspect_sources.py` 保存官方元数据，DiaData 查询失败不影响其他数据；后续下载器固定检查上海 `20425518.v5`、PhysioCGM `28136294.v1`。

- `outputs/cgmacros_audit/report.md`：24/48/72 小时、最早/最晚窗口，共 47,520 次敏感性实验；45 人的逐人餐次盘点（1,706 条记录，1,385 条候选餐）。
- `outputs/shanghai_v5/report.md`：109 份工作簿归组为 100 人，共 9,000 次缺失实验。采用用户指定 `20425518.v5 (2022-09-24)`，并非另一个 `21600933.v5`。
- `outputs/physiocgm/report.md`：10 人原始 CGM 导出中的 317 个候选时间缺口；导出跨度约 18–90 天，不等同论文多模态的 24 小时窗口。

这些运行次数不是独立样本量。缺失效应的数值随窗口选择和长度变化；PhysioCGM 论文仅推测连接丢失，当前不能将候选时间缺口解释为已验证的掉线机制。餐后预测尚未训练。

## 文献

1. Das et al. (2025). *CGMacros: a pilot scientific dataset for personalized nutrition and diet monitoring*. Scientific Data 12, 1557. [DOI: 10.1038/s41597-025-05851-7](https://doi.org/10.1038/s41597-025-05851-7)。[数据 DOI](https://doi.org/10.13026/3z8q-x658)。
2. Zhao et al. (2023). *Chinese diabetes datasets for data-driven machine learning*. Scientific Data 10, 35. [DOI: 10.1038/s41597-023-01940-7](https://doi.org/10.1038/s41597-023-01940-7)。[数据 collection](https://doi.org/10.6084/m9.figshare.c.6310860)。
3. Prioleau, Lu & Cui (2025). *Glucose-ML: A collection of longitudinal diabetes datasets for development of robust AI solutions*. [arXiv:2507.14077v1](https://arxiv.org/abs/2507.14077v1)。用于跨数据集评估的背景讨论；不作为缺失效应的直接证据，未核实 NeurIPS 正式发表记录。

## 接入自己的数据

输入 JSON 按参与者分组，单位必须为 mg/dL：

```json
{"participant-001": [
  {"timestamp": "2025-01-01T00:00:00", "glucose_mg_dl": 105},
  {"timestamp": "2025-01-01T00:05:00", "glucose_mg_dl": 112},
  {"timestamp": "2025-01-01T00:10:00", "glucose_mg_dl": 110}
]}
```

```sh
python glucotrust.py --input data/local/cohort.json --out outputs/cohort --support-cap-minutes 5
```

不在 Git 中提交个人健康数据。公开数据必须先记录来源、版本、许可、下载方式、单位、时区、采样间隔、参与者与窗口筛选流程；“能下载”不意味着允许再分发。

## 路线图

1. GlucoTrust：先完成 CGMacros 发布曲线试验，再接入 ShanghaiT2DM 验证；另找可识别原生测量的数据检验掉线后重新处理的影响。扩展窗口长度和筛选规则敏感性，避免仅凭一个完整日推广到十天随访。
2. GlucoPatterns：比较训练集平均餐后反应、餐食/餐前统一模型、加入早期个人历史的方案。分别评估从未见过的参与者和有历史的参与者；按参与者划分外层评估、按时间截断个人历史，所有预处理仅拟合训练集。
3. 联合实验：固定预测目标和测试集，仅改变个人早期历史的缺失比例与模式，比较个体化相对统一模型的增益是否保留。前两个模块验证完成后再实现。

按血糖高低删点仅可作为另外标记的压力测试，不解释为真实掉线机制。阴性结果也应如实报告。

## 贡献与许可

欢迎围绕数据适配、时间权重验证、实验设计提交 issue/PR。请附复现命令、数据许可说明和必要测试。代码采用 MIT 许可；外部数据不包含在此许可内。

## 作者

**单嘉诚（Jiacheng Shan）** — [@maybedanshan](https://github.com/maybedanshan)

数据科学与大数据方向本科研究项目。仅用于学术演示，不用于临床诊断、治疗决策或饮食用药建议。
