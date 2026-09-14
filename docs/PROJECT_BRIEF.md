# GlucoTrust project brief

Repository: https://github.com/maybedanshan/gluco-trust-patterns

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

The [selected-model joint experiment](SELECTED_HISTORY_RESULTS.md) now repeats the exact v1 masks and fixed later meals with the inner-selected model. At 20% block deletion, remaining personalization benefit is 2.250 mg/dL [1.105, 3.507]; total degradation cost is 0.195 [0.032, 0.364]. Under the specified diagnostic order, availability cost is 0.193 and retained-feature cost is 0.002 mg/dL. This is not causal attribution. The [interactive research explorer](demo/research.html) shows model comparisons and these paired intervals together.

The [selected-model joint experiment](SELECTED_HISTORY_RESULTS.md) now repeats the exact v1 masks and fixed later meals with the inner-selected model. At 20% block deletion, remaining personalization benefit is 2.250 mg/dL [1.105, 3.507]; total degradation cost is 0.195 [0.032, 0.364]. Under the specified diagnostic order, availability cost is 0.193 and retained-feature cost is 0.002 mg/dL. This is not causal attribution. The [interactive research explorer](demo/research.html) shows model comparisons and these paired intervals together.

A separate [model comparison](MODEL_COMPARISON_RESULTS.md) now selects ridge penalties inside training-participant folds and adds a history-only mean baseline. With ten early meals, selected-model personalization has MAE 19.075 mg/dL versus 21.521 for the selected pooled model and 21.651 for the history-only mean, on the same later meals. The earlier joint missingness results below still refer to the fixed-penalty v1 model; they are not updated estimates for this selected model.

The first [GlucoPatterns benchmark](GLUCOPATTERNS_RESULTS.md) is implemented under a [fixed protocol](GLUCOPATTERNS_PROTOCOL.md). It separates unseen-person evaluation from limited-history adaptation. The [joint experiment](HISTORY_MISSINGNESS_RESULTS.md) then degrades historical premeal inputs while holding adaptation labels and later test meals fixed: 44 participants, 739 later meals and 5,280 simulation runs.

The post-v0.1 extension also implements [participant-paired comparisons and bootstrap intervals](PAIRED_RESULTS.md). In the joint experiment, 20% block deletion increased personalized MAE by 0.205 mg/dL, with a pointwise 95% interval of [0.046, 0.367]. Personalization still improved over the pooled model by 1.568 mg/dL [0.459, 2.796]. These effects are conditional on this model, selected history and adaptation policy.

CGMacros released curves contain interpolation features. Current results measure additional missingness after processing and cannot identify original dropout causes or establish prospective forecasting performance. Complete-window selection also limits generalization. Night deletion affects little of this model's premeal input, so its small effect is not general evidence of robustness. Historical label degradation, external meal validation and native-sample prospective evaluation remain future work in the [roadmap](RESEARCH_ROADMAP.md).

## Application use / 申请材料使用说明

可使用的项目描述：

> GlucoTrust 项目研究连续血糖数据质量如何影响报告指标与个体化分析。当前原型实现了时间加权缺失实验、参与者配对置信区间和餐后响应预测比较，并通过固定后期测试餐次的共同实验，考察历史输入缺失后个体化优势的变化。数据审查发现 CGMacros 发布曲线具有插值特征，因此结论限定于处理后记录的回顾性分析。后续将重点验证历史标签缺失的影响，以及在外部和原生采样数据上的可复现性。

这段文字描述项目成果，不自动证明任何个人独立完成全部工作。申请人应补充真实承担的研究设计、编码、数据核查与结果解释工作，并按申请方要求披露 AI 辅助。不要将计划写成完成的成果，也不要把目前的本地候选版本写成已公开发表或经过同行评审的研究。
