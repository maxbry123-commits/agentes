from engine.operators.completions_operator import (
    CompletionsOperator,
    CompletionsOperatorConfig,
)
from engine.operators.completions_operator_tacc import (
    CompletionsOperatorTACC,
    CompletionsOperatorTACCConfig,
)
from engine.operators.concatenate_operator import (
    ConcatenateOperator,
    ConcatenateOperatorConfig,
)
from engine.operators.dclm_refinedweb_source_operator import (
    DCLMRefineWebSourceConfig,
    DCLMRefineWebSourceOperator,
)
from engine.operators.embedding_operator import (
    EmbeddingOperator,
    EmbeddingOperatorConfig,
)
from engine.operators.fasttext_operator import FastTextOperator, FastTextOperatorConfig
from engine.operators.function_operator import (
    AsyncFunctionOperator,
    AsyncFunctionOperatorConfig,
    CPUFunctionOperator,
    CPUFunctionOperatorConfig,
    FunctionOperator,
    FunctionOperatorConfig,
    GPUFunctionOperator,
    GPUFunctionOperatorConfig,
    GenericResourceFunctionOperator,
    GenericResourceFunctionOperatorConfig,
    HighMemoryFunctionOperator,
    HighMemoryFunctionOperatorConfig,
)
from engine.operators.hf_filter_operator import HFFilterOperator, HFFilterOperatorConfig
from engine.operators.hf_source_operator import HFSourceOperator, HFSourceOperatorConfig
from engine.operators.hf_upload_operator import HFUploadOperator, HFUploadOperatorConfig
from engine.operators.json_source_operator import (
    JSONSourceOperator,
    JSONSourceOperatorConfig,
    LocalJSONSourceConfig,
    LocalJSONSourceOperator,
)
from engine.operators.merge_operator import MergeOperator, MergeOperatorConfig
from engine.operators.mix_operator import MixOperator, MixOperatorConfig
from engine.operators.operator import register_operator
from engine.operators.shard_operator import ShardOperator, ShardOperatorConfig
from engine.operators.similarity_filtering_operator import (
    IndexFlatIPSimilarityFilteringOperator,
    IndexFlatIPSimilarityFilteringOperatorConfig,
    SimilarityFilteringOperator,
    SimilarityFilteringOperatorConfig,
)
from engine.operators.train_fasttext_operator import (
    TrainFastTextOperator,
    TrainFastTextOperatorConfig,
)
from engine.operators.truncate_operator import TruncateOperator, TruncateOperatorConfig

register_operator(FunctionOperatorConfig, FunctionOperator)
register_operator(HFFilterOperatorConfig, HFFilterOperator)
register_operator(CPUFunctionOperatorConfig, CPUFunctionOperator)
register_operator(MixOperatorConfig, MixOperator)
register_operator(HFSourceOperatorConfig, HFSourceOperator)
register_operator(JSONSourceOperatorConfig, JSONSourceOperator)
register_operator(FastTextOperatorConfig, FastTextOperator)
register_operator(DCLMRefineWebSourceConfig, DCLMRefineWebSourceOperator)
register_operator(TrainFastTextOperatorConfig, TrainFastTextOperator)
register_operator(FastTextOperatorConfig, FastTextOperator)
register_operator(DCLMRefineWebSourceConfig, DCLMRefineWebSourceOperator)
register_operator(CompletionsOperatorConfig, CompletionsOperator)
register_operator(AsyncFunctionOperatorConfig, AsyncFunctionOperator)
register_operator(GPUFunctionOperatorConfig, GPUFunctionOperator)
register_operator(
    GenericResourceFunctionOperatorConfig, GenericResourceFunctionOperator
)
register_operator(HighMemoryFunctionOperatorConfig, HighMemoryFunctionOperator)
register_operator(JSONSourceOperatorConfig, JSONSourceOperator)
register_operator(SimilarityFilteringOperatorConfig, SimilarityFilteringOperator)
register_operator(MergeOperatorConfig, MergeOperator)
register_operator(EmbeddingOperatorConfig, EmbeddingOperator)
register_operator(TruncateOperatorConfig, TruncateOperator)
register_operator(ConcatenateOperatorConfig, ConcatenateOperator)
register_operator(
    IndexFlatIPSimilarityFilteringOperatorConfig, IndexFlatIPSimilarityFilteringOperator
)
register_operator(ShardOperatorConfig, ShardOperator)
register_operator(HFUploadOperatorConfig, HFUploadOperator)
register_operator(CompletionsOperatorTACCConfig, CompletionsOperatorTACC)


__all__ = [
    "FunctionOperator",
    "FunctionOperatorConfig",
    "LightReduceOperator",
    "LightReduceOperatorConfig",
    "MixOperator",
    "MixOperatorConfig",
    "HFSourceOperator",
    "HFSourceOperatorConfig",
    "DAGOperator",
    "DAGOperatorConfig",
    "DCLMRefineWebSourceConfig",
    "DCLMRefineWebSourceOperator",
    "FastTextOperator",
    "FastTextOperatorConfig",
    "CompletionsOperator",
    "AsyncFunction",
    "AsyncFunctionOperatorConfig",
    "JSONSourceOperator",
    "JSONSourceOperatorConfig",
    "LocalJSONSourceConfig",
    "LocalJSONSourceOperator",
    "TruncateOperator",
    "TruncateOperatorConfig",
    "ConcatenateOperator",
    "ConcatenateOperatorConfig",
    "IndexFlatIPSimilarityFilteringOperator",
    "IndexFlatIPSimilarityFilteringOperatorConfig",
    "ShardOperator",
    "ShardOperatorConfig",
]
