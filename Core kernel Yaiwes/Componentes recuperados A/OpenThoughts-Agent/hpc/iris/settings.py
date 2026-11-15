"""Shared constants for OT-Agent Iris launchers."""

DEFAULT_TASK_IMAGE = "ghcr.io/open-thoughts/openthoughts-agent:tpu"
DEFAULT_CLUSTER_CONFIG = "lib/iris/config/marin.yaml"
DEFAULT_GPU_TASK_IMAGE = "ghcr.io/open-thoughts/openthoughts-agent:gpu-8x"
DEFAULT_GPU_CLUSTER_CONFIG = "lib/iris/config/cw-us-east-02a.yaml"
DEFAULT_PRIORITY = "interactive"

# Ephemeral per-VM disk. marin TPU (v5p/v6e) workers cap at 100GB — requesting more queues forever
# on an autoscaler that can't provision a larger-disk worker. CoreWeave GPU nodes have large local
# disk, so a GPU job downloading big model weights (e.g. GLM-5.2 AWQ ~180GB) MUST get more than 100GB
# or kubelet evicts the pod for exceeding its ephemeral-storage limit mid-download.
DEFAULT_DISK = "100GB"
DEFAULT_GPU_DISK = "512GB"
