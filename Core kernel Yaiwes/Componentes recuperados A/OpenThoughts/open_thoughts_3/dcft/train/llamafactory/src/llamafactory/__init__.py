import torch.serialization

# This helped but other imports break it
# if not torch.cuda.is_available() or torch.cuda.device_count() == 0:
#     print("skipping deepspeed imports due to 'RuntimeError: 0 active drivers ([]). There should only be one.'")
# else:

from deepspeed.runtime.zero.config import ZeroStageEnum
from deepspeed.runtime.fp16.loss_scaler import LossScaler
from deepspeed.runtime.zero.stage_1_and_2 import DeepSpeedZeroOptimizer
from deepspeed.runtime.zero.stage3 import DeepSpeedZeroOptimizer_Stage3

torch.serialization.add_safe_globals([
    ZeroStageEnum,
    LossScaler,
    DeepSpeedZeroOptimizer,
    DeepSpeedZeroOptimizer_Stage3
])

