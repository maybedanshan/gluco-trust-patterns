# GlucoTrust project brief

Repository: https://github.com/maybedanshan/gluco-trust

## Research question

Does the placement of missing observations change time-weighted glucose-report metrics at the same missing-data budget?

## Implemented evidence

The local v0.1 prototype includes a reproducible missingness engine, dataset adapters, an offline explorer and generated reports. CGMacros primary experiments include 44 eligible participants and paired device windows; ShanghaiT2DM contributes a separate 100-participant analysis. PhysioCGM exports support an exploratory timestamp-gap audit. Full counts, definitions and source versions are in the [results report](RESULTS.md).

At a requested 20% deletion budget, continuous-block removal produced larger descriptive TIR mean absolute error than random deletion in the primary CGMacros and Shanghai configurations. This observation is specific to the selected records and analysis; it is not a clinical threshold or a claim of statistical significance.

## Why the implementation is assessable

- Time weights are fixed before deletion, so remaining readings do not inherit missing intervals.
- TIR changes use percentage points; requested point budgets and actual missing time are recorded separately.
- Participants, simulation seeds and overlapping windows are distinguished.
- Source versions, download verification boundaries and software/data licenses are documented.
- A no-download synthetic workflow allows reviewers to inspect the method without handling raw participant records.

## Limits and next question

The first [GlucoPatterns benchmark](GLUCOPATTERNS_RESULTS.md) is now implemented locally under a [fixed protocol](GLUCOPATTERNS_PROTOCOL.md). It separates unseen-person evaluation from limited-history adaptation. The older application wording below should be updated before reuse: a first retrospective meal benchmark has been completed, while prospective/native-sample and external meal validation remain future work.

The post-v0.1 extension now implements [participant-paired comparisons and bootstrap intervals](PAIRED_RESULTS.md). The original application wording below predates that extension: participant-level uncertainty analysis can now be described as implemented locally, while meal prediction remains planned.

CGMacros released curves contain interpolation features. Current results measure additional missingness after processing and cannot identify original dropout causes. Complete-window selection also limits generalization. Meal prediction and the effect of missing personal history on personalization remain planned work, described in the [roadmap](RESEARCH_ROADMAP.md).

## Application use / 申请材料使用说明

可使用的项目描述：

> GlucoTrust 项目研究连续血糖记录中不同缺失模式对报告指标的影响。当前原型实现了时间加权指标、可复现缺失实验和交互展示，并在 CGMacros 与 ShanghaiT2DM 上进行了描述性比较。数据审查发现 CGMacros 发布曲线具有插值特征，因此结论限定为处理后记录的额外缺失效应。下一步计划开展参与者层面的不确定性分析，并检验少量个人历史能否改善餐后预测。

这段文字描述项目成果，不自动证明任何个人独立完成全部工作。申请人应补充真实承担的研究设计、编码、数据核查与结果解释工作，并按申请方要求披露 AI 辅助。不要将计划写成完成的成果，也不要把目前的本地候选版本写成已公开发表或经过同行评审的研究。
