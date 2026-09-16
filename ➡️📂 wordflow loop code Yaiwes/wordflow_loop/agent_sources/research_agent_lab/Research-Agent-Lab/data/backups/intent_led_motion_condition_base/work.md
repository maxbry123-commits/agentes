# LED + VIRAT 工作日志

## 当前目标

用 LED 在 VIRAT 上跑通原协议 baseline，作为后续意图/约束模块的对照基线。

## 关键结论

- 当前 `LED-main` 是精简版官方代码包，缺少 README 中提到的 `data/` 目录、NBA `.npy` 数据和官方 checkpoint。
- VIRAT 数据沿用相邻项目 `../MID-main/processed_data_virat/` 中已处理好的 pkl：
  - `virat_s1_train/test.pkl`
  - `virat_s2_train/test.pkl`
  - `virat_s3_train/test.pkl`
- VIRAT 行人数量远少于 NBA 固定 11 人，通常为 1-2 人，因此 LED 数据输入按 `num_agents=2` 适配。
- 单人窗口使用 padding agent，但 padding 不参与 loss 和 ADE/FDE 指标。
- 不做 MID+VIRAT 的 8/12 对齐版；本阶段只保留 LED 原协议 10/20 baseline。

## 已完成

### 2026-06-15

- 新增 `data/dataloader_virat.py`
  - 从 `../MID-main/processed_data_virat/` 读取 VIRAT pkl。
  - 输出 LED trainer 需要的 `pre_motion_3D`、`fut_motion_3D`、mask 和元信息。
  - 支持 `num_agents=2`，padding agent 不计入有效样本。
- 修改 `trainer/train_led_trajectory_augment_input.py`
  - 根据 `dataset: virat` 切换 VIRAT dataloader。
  - 将原代码硬编码的 11 agents 改为配置化 `num_agents`。
  - loss / ADE / FDE 只统计真实 agent。
  - 若缺少 core denoising checkpoint，可先在当前数据集训练 core。
  - `test_single_model()` 支持配置里的 `pretrained_initializer_model`。
- 新增配置：
  - `cfg/virat/led_virat_debug.yml`：快速 smoke 测试。
  - `cfg/virat/led_virat.yml`：正式 LED 原协议 VIRAT baseline。
- 修复 `utils/utils.py`
  - `glob2` 缺失时 fallback 到 Python 标准库 `glob`。
- 已完成 smoke run：
  - config: `led_virat_debug`
  - output: `results/led_virat_debug/baseline/`
  - 目的：验证 core 预训练、initializer 训练、测试指标闭环。
- 已完成 v0 run：
  - config: 临时缩短版 `led_virat`
  - output: `results/led_virat/baseline/`
  - 说明：仅用于链路验证，不作为最终 baseline。

## 正式 baseline 协议

配置文件：`cfg/virat/led_virat.yml`

- dataset: `virat`
- scenes: `virat_s1`, `virat_s2`, `virat_s3`
- data_root: `../MID-main/processed_data_virat`
- num_agents: `2`
- past_frames: `10`
- future_frames: `20`
- diffusion steps: `100`
- k_pred: `20`
- train_batch_size: `10`
- test_batch_size: `500`
- num_epochs: `100`
- lr: `1e-3`
- lr scheduler: step, `decay_step=8`, `decay_gamma=0.5`
- traj_mean: `[0, 0]`
- traj_scale: `1`
- core checkpoint: `results/checkpoints/virat_core_denoising_model_e100.p`
- initializer checkpoint: `results/led_virat/baseline_original/models/model_0100.p`

## 下一步

1. 导出 baseline 数据：
   - history
   - future_gt
   - predictions
   - per-sample ADE/FDE
   - summary.json
   - samples.csv
2. 最终结果写回本文件，只保留关键指标和输出路径。

## 正式训练状态

### 2026-06-15 训练日志检查

- 目录：`results/led_virat/baseline_original/`
- core denoising 训练已完成 100 epoch，并保存：
  - `results/checkpoints/virat_core_denoising_model_e100.p`
- initializer 训练已完成 100 epoch，并保存：
  - `results/led_virat/baseline_original/models/model_0100.p`
- checkpoint 已完整保存 `model_0010.p` 到 `model_0100.p`。
- 日志没有 NaN / crash / loss 爆炸；epoch 50 后指标基本趋稳。

epoch 100 最终评估：
- ADE(1s) / FDE(1s): `0.0075 / 0.0054`
- ADE(2s) / FDE(2s): `0.0101 / 0.0095`
- ADE(3s) / FDE(3s): `0.0129 / 0.0139`
- ADE(4s) / FDE(4s): `0.0189 / 0.0249`

## 可视化

### 2026-06-16 单样本预测路径

- 脚本：`visualize_virat_prediction.py`
- 输出：`results/fig/led_virat_prediction_example.png`
- 样本：`virat_s1_test`, timestep `14329`, agent `30`
- 预测：20 条 LED 采样轨迹，红色为 best ADE 样本
- 指标：best ADE `0.031090`, best FDE `0.117497`
