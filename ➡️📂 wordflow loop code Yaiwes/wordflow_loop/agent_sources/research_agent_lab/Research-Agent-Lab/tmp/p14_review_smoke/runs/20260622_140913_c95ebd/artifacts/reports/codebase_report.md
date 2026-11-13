# Codebase Report: Intent-LED-mul-agent

Repository: `D:\Codes\VS\Intent-LED-mul-agent`

## Integration Points
- Add optional per-agent intention/language features in VIRATDataset output.
- Fuse optional condition features in data_preprocess before initializer/denoiser calls.
- Inject condition features into LEDInitializer mean/variance/scale branches.
- Extend TransformerDenoisingModel context conditioning after initializer smoke tests.
- Gate every experiment behind cfg/virat flags to keep baseline configs reproducible.

## Suggested First Patch Files
- `cfg/virat/led_virat_debug.yml`
- `cfg/virat/led_virat.yml`
- `data/dataloader_virat.py`
- `trainer/train_led_trajectory_augment_input.py`
- `models/model_led_initializer.py`
- `work.md`

## Smoke Commands
- `cd /d D:/Codes/VS/Intent-LED-mul-agent && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 1 --info motion_condition`
- `cd /d D:/Codes/VS/Intent-LED-mul-agent && python main_led_nba.py --cfg led_virat_intent_debug --gpu 0 --train 0 --info motion_condition`

## File Summaries
### `cfg/virat/led_virat.yml`
- Role: Experiment configuration.
- Config keys: description, results_root_dir, dataset, data_root, scenes, num_agents, min_agents, train_stride, test_stride, num_workers, past_frames, future_frames, min_past_frames, min_future_frames, motion_dim, forecast_dim
- Patterns: initializer checkpoint, core fallback training, debug-mode control

### `cfg/virat/led_virat_debug.yml`
- Role: Experiment configuration.
- Config keys: description, results_root_dir, dataset, data_root, scenes, num_agents, min_agents, train_stride, test_stride, num_workers, past_frames, future_frames, min_past_frames, min_future_frames, motion_dim, forecast_dim
- Patterns: initializer checkpoint, core fallback training, debug-mode control

### `cfg/virat/led_virat_intent.yml`
- Role: Experiment configuration.
- Config keys: description, results_root_dir, dataset, data_root, scenes, num_agents, min_agents, train_stride, test_stride, num_workers, past_frames, future_frames, min_past_frames, min_future_frames, motion_dim, forecast_dim
- Patterns: initializer checkpoint, core fallback training, debug-mode control

### `cfg/virat/led_virat_intent_debug.yml`
- Role: Experiment configuration.
- Config keys: description, results_root_dir, dataset, data_root, scenes, num_agents, min_agents, train_stride, test_stride, num_workers, past_frames, future_frames, min_past_frames, min_future_frames, motion_dim, forecast_dim
- Patterns: initializer checkpoint, core fallback training, debug-mode control

### `data/dataloader_virat.py`
- Role: Dataset and batch collation.
- Classes: VIRATDataset
- Functions: _default_mid_root, _ensure_mid_environment_importable, _node_sort_key, __init__, _load_env, _valid_agents_at, _build_index, __len__, __getitem__, seq_collate
- Patterns: agent masking, history trajectory tensor, future trajectory tensor

### `main_led_nba.py`
- Role: CLI entry point for train/eval.
- Functions: parse_config, main

### `models/layers.py`
- Role: Project file.
- Classes: PositionalEncoding, ConcatSquashLinear, GAT, MLP, social_transformer, st_encoder
- Functions: __init__, forward, __init__, forward, batch_generate, __init__, forward, __init__, forward, __init__, forward, __init__, reset_parameters, forward

### `models/model_diffusion.py`
- Role: Transformer denoising model used by diffusion sampling.
- Classes: st_encoder, social_transformer, TransformerDenoisingModel
- Functions: __init__, reset_parameters, forward, __init__, forward, __init__, forward, generate_accelerate
- Patterns: denoiser

### `models/model_led_initializer.py`
- Role: Leapfrog initializer for multi-sample future trajectory proposals.
- Classes: LEDInitializer
- Functions: __init__, forward
- Patterns: initializer

### `README.md`
- Role: Project file.

### `trainer/train_led_trajectory_augment_input.py`
- Role: Training, denoising, evaluation, and metric loop.
- Classes: Trainer
- Functions: __init__, print_model_param, _load_or_train_core_model, noise_estimation_loss_masked, _pretrain_core_model, make_beta_schedule, extract, noise_estimation_loss, p_sample, p_sample_accelerate, p_sample_loop, p_sample_loop_mean, p_sample_loop_accelerate, fit, data_preprocess, build_motion_condition, _train_single_epoch, _test_single_epoch, prepare_seed, save_data, prepare_seed, test_single_model, prepare_seed
- Patterns: agent masking, history trajectory tensor, future trajectory tensor, initializer, denoiser, initializer checkpoint, core fallback training, debug-mode control

### `utils/config.py`
- Role: Project file.
- Classes: Config
- Functions: __init__, get_last_epoch, __getattribute__, __setattr__, get

### `utils/utils.py`
- Role: Project file.
- Classes: AverageMeter
- Functions: __init__, reset, update, isnparray, isinteger, isfloat, isscalar, islogical, isstring, islist, convert_secs2time, get_timestring, recreate_dirs, is_path_valid, is_path_creatable, is_path_exists, is_path_exists_or_creatable, isfile, isfolder, mkdir_if_missing, safe_list, safe_path, prepare_seed, initialize_weights
- Patterns: debug-mode control

### `work.md`
- Role: Project log and current baseline record.
- Patterns: history trajectory tensor, future trajectory tensor, initializer, initializer checkpoint, debug-mode control

## Risks
- Project copy is not a git repository; use backups or copied files for rollback.
- VIRAT data is loaded from ../MID-main, so dataloader changes should not mutate source pkl files.
- Denoiser context dimensions are hard-coded around 256/512; condition fusion must preserve tensor shapes.
- High exploration mode allows code edits after local report generation; keep smoke tests short.
