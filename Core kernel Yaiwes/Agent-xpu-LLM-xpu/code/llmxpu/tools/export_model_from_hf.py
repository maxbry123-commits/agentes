"""
Adapted from llama2.c/export.py

This script has functions and utilties for model export.
Basically, we have a bunch of versions of the model, and we
want to export them to .bin files to be read from and inferenced in C.

Among the "input" versions of PyTorch files/models:
- Official Llama 2 weights released by Meta
- Huggingface weights available on the hub
- llama2.c (this repo) trained models

Among the "output" versions of .bin files:
- Half/full precision fp16/fp32 weights (default fp32 since fp16 is not supported in C)
- Q8_0 quantized weights (w8a16, w8a32)

This script aspires to provide all of these conversions.
"""

import os
import struct
import argparse
from tqdm import tqdm
import numpy as np
import torch
from torch import nn
from enum import Enum
import llmxpu.models.llama2 as llama2
import llmxpu.models.llama3 as llama3


# Model types
class ModelType(Enum):
    Llama2 = 0
    Llama3 = 1


# -----------------------------------------------------------------------------
# common utilities


def create_int4_array(values: np.ndarray) -> np.ndarray:
    # Pack two INT4 values into one INT8
    assert len(values.shape) == 1
    result = np.zeros(len(values) // 2, dtype=np.int8)
    result[: len(values) // 2] = (values[::2] &
                                  0xF) | ((values[1::2] & 0xF) << 4)
    if len(values) % 2 != 0:
        result[-1] = values[-1] & 0xF
    return result


def serialize_fp32(file, tensor):
    """writes one fp32 tensor to file that is open in wb mode"""
    d = tensor.detach().cpu().view(-1).to(torch.float32).numpy()
    b = struct.pack(f"{len(d)}f", *d)
    file.write(b)


def serialize_fp16(file, tensor):
    """writes one fp16 tensor to file that is open in wb mode"""
    d = tensor.detach().cpu().view(-1).to(torch.float16).numpy()
    b = struct.pack(f"{len(d)}e", *d)
    file.write(b)


def serialize_int8(file, tensor):
    """writes one int8 tensor to file that is open in wb mode"""
    d = tensor.detach().cpu().view(-1).numpy().astype(np.int8)
    b = struct.pack(f"{len(d)}b", *d)
    file.write(b)


def serialize_int4(file, tensor):
    """writes one int4 tensor to file that is open in wb mode"""
    int4_vals = tensor.detach().cpu().view(-1).numpy().astype(np.int8)
    int4_vals = np.clip(int4_vals, -7, 7)
    d = create_int4_array(int4_vals)
    b = struct.pack(f"{len(d)}b", *d)
    file.write(b)


def quantize_q80(w, group_size):
    """
    takes a tensor and returns the Q8_0 quantized version
    i.e. symmetric quantization into int8, range [-127,127]
    """
    if group_size == -1:
        assert len(w.shape) == 2
        group_size = w.shape[1]
    elif group_size == -2:
        group_size = w.numel()  # product of all dimensions in the tensor shape
    else:
        assert w.numel() % group_size == 0

    ori_shape = w.shape
    w = w.float()  # convert to float32
    w = w.reshape(-1, group_size)
    # find the max in each group
    wmax = torch.abs(w).max(dim=1).values
    # calculate the scaling factor such that float = quant * scale
    scale = wmax / 127.0
    # scale into range [-127, 127]
    quant = w / scale[:, None]
    # round to nearest integer
    int8val = torch.round(quant).to(torch.int8)
    # dequantize by rescaling
    fp32val = (int8val.float() * scale[:, None]).view(-1)
    fp32valr = fp32val.reshape(-1, group_size)
    # calculate the max error in each group
    err = torch.abs(fp32valr - w).max(dim=1).values
    # find the max error across all groups
    maxerr = err.max().item()
    return int8val, scale, maxerr


def quantize_q40(w, group_size):
    """
    Deprecated: use quantize_q80 instead
    takes a tensor and returns the Q4_0 quantized version
    i.e. symmetric quantization into int4, range [-8,7]
    """
    raise DeprecationWarning("Use INT8 quantization instead")
    assert w.numel() % group_size == 0
    ori_shape = w.shape
    w = w.float()  # convert to float32
    w = w.reshape(-1, group_size)
    # find the max in each group
    wmax = torch.abs(w).max(dim=1).values
    # calculate the scaling factor such that float = quant * scale
    scale = wmax / 7.0
    # scale into range [-7, 7]
    quant = w / scale[:, None]
    # round to nearest integer
    int4val = torch.round(quant)
    # dequantize by rescaling
    fp32val = (int4val.float() * scale[:, None]).view(-1)
    fp32valr = fp32val.reshape(-1, group_size)
    # calculate the max error in each group
    err = torch.abs(fp32valr - w).max(dim=1).values
    # find the max error across all groups
    maxerr = err.max().item()
    return int4val, scale, maxerr


def print_hex_value(tensor, i, j=0):
    if len(tensor.shape) == 1:
        val_fp32 = tensor[i].to(torch.float32).item()
        val_fp16 = tensor[i].to(torch.float16).item()
    else:
        val_fp32 = tensor[i, j].to(torch.float32).item()
        val_fp16 = tensor[i, j].to(torch.float16).item()
    print(
        struct.pack("!f", val_fp32).hex(), struct.pack("!e", val_fp16).hex()
    )  # big endian


# -----------------------------------------------------------------------------
# Export functions


def fp_export(model, filepath, model_type: ModelType, dtype="fp32"):
    """
    Export the model weights in full float32/float16 .bin file to be read from C.
    """
    if dtype == "fp32":
        version = 0
    elif dtype == "fp16":
        version = 1
    else:
        raise ValueError(f"unknown dtype {dtype}")

    out_file = open(filepath, "wb")
    # first write out the header. the header will be 256 bytes
    # 1) write magic, which will be uint32 of "hllm" in ASCII
    out_file.write(struct.pack("I", 0x686C6C6D))
    # 2) write model id, which will be int
    out_file.write(struct.pack("i", model_type.value))
    # 3) write dtype version, which will be int
    out_file.write(struct.pack("i", version))
    # 4) write the params, which will be 8 ints
    p = model.params
    hidden_dim = model.layers[0].feed_forward.w1.weight.shape[0]
    n_kv_heads = p.n_heads if p.n_kv_heads is None else p.n_kv_heads
    header = struct.pack(
        "iiiiiiii",
        p.dim,
        hidden_dim,
        p.n_layers,
        p.n_heads,
        n_kv_heads,
        p.vocab_size,
        p.max_seq_len,
        0,  # group_size is not used in fp32/fp16
    )
    out_file.write(header)
    pad = 256 - out_file.tell()  # pad rest with zeros; tell returns current pos
    assert pad >= 0
    out_file.write(b"\0" * pad)

    # now let's write out all the params
    weights = [model.tok_embeddings.weight]
    for layer in model.layers:
        weights.extend(
            [
                layer.attention_norm.weight,
                layer.attention.wq.weight,
                layer.attention.wk.weight,
                layer.attention.wv.weight,
                layer.attention.wo.weight,
                layer.ffn_norm.weight,
                layer.feed_forward.w1.weight,
                layer.feed_forward.w2.weight,
                layer.feed_forward.w3.weight,
            ]
        )
    weights.append(model.norm.weight)
    weights.append(model.output.weight)
    # freqs_cis precompute
    if hasattr(model, "freqs_cis"):
        if model.freqs_cis.dtype == torch.complex64:
            weights.append(torch.view_as_real(model.freqs_cis))
        else:
            weights.append(model.freqs_cis)
    else:
        raise ValueError("Model does not have freqs_cis")

    if dtype == "fp32":
        for w in tqdm(weights, desc="Serializing and writing weights (fp32)"):
            serialize_fp32(out_file, w)
    elif dtype == "fp16":
        for w in tqdm(weights, desc="Serializing weights (fp16)"):
            serialize_fp16(out_file, w)
    # write to binary file
    out_file.close()
    print(f"Wrote {filepath}")


def int_export(
    model, filepath, model_type: ModelType, group_size=64, quant_type="w8a32"
):
    """
    Export the model weights in Q8_0/Q4_0 into .bin file to be read from C.
    That is:
    - quantize all weights to symmetric int8/int4, in range [-127, 127] / [-8, 7]
    - all other tensors (the rmsnorm params) are kept and exported in fp32/fp16
    - quantization is done in groups of group_size to reduce the effects of any outliers
    """
    if quant_type == "w8a32":
        version = 2
        serialize_else = serialize_fp32
    elif quant_type == "w8a16":
        version = 3
        serialize_else = serialize_fp16
    elif quant_type == "w4a32":
        version = 4
        serialize_else = serialize_fp32
    elif quant_type == "w4a16":
        version = 5
        serialize_else = serialize_fp16
    else:
        raise ValueError(f"Unknown quantization type {quant_type}")

    # let's first do some validation for this export type
    if group_size > 0:
        while model.params.dim % group_size != 0:
            group_size //= 2
            print(f"BACKOFF: reducing group size to {group_size} to fit hidden_dim")

    # (if_quant_int8, tensor_name, tensor) pairs
    weights = [(False, "model.tok_embedding", model.tok_embeddings.weight)]
    for i, layer in enumerate(model.layers, start=1):
        weights.extend(
            [
                (False, f"layer{i}.attention_norm",
                 layer.attention_norm.weight),
                (True, f"layer{i}.attention.wq", layer.attention.wq.weight),
                (True, f"layer{i}.attention.wk", layer.attention.wk.weight),
                (True, f"layer{i}.attention.wv", layer.attention.wv.weight),
                (True, f"layer{i}.attention.wo", layer.attention.wo.weight),
                (False, f"layer{i}.ffn_norm", layer.ffn_norm.weight),
                (True, f"layer{i}.feed_forward.w1",
                 layer.feed_forward.w1.weight),
                (True, f"layer{i}.feed_forward.w2",
                 layer.feed_forward.w2.weight),
                (True, f"layer{i}.feed_forward.w3",
                 layer.feed_forward.w3.weight),
            ]
        )
    weights.append((False, "model.norm", model.norm.weight))
    weights.append((True, "model.output", model.output.weight))
    if hasattr(model, "freqs_cis"):
        if model.freqs_cis.dtype == torch.complex64:
            weights.append((False, "model.freqs_cis",
                           torch.view_as_real(model.freqs_cis)))
        else:
            weights.append((False, "model.freqs_cis", model.freqs_cis))
    else:
        raise ValueError("Model does not have freqs_cis")

    out_file = open(filepath, "wb")
    # first write out the header. the header will be 256 bytes
    # 1) write magic, which will be uint32 of "hllm" in ASCII
    out_file.write(struct.pack("I", 0x686C6C6D))
    # 2) write model id, which will be int
    out_file.write(struct.pack("i", model_type.value))
    # 3) write dtype version, which will be int
    out_file.write(struct.pack("i", version))
    # 3) write the params, which will be 8 ints
    p = model.params
    hidden_dim = model.layers[0].feed_forward.w1.weight.shape[0]
    n_kv_heads = p.n_heads if p.n_kv_heads is None else p.n_kv_heads
    header = struct.pack(
        "iiiiiiii",
        p.dim,
        hidden_dim,
        p.n_layers,
        p.n_heads,
        n_kv_heads,
        p.vocab_size,
        p.max_seq_len,
        group_size,
    )
    out_file.write(header)
    pad = 256 - out_file.tell()  # pad rest with zeros; tell returns current pos
    assert pad >= 0
    out_file.write(b"\0" * pad)

    ew = []
    for if_quant, name, w in tqdm(
        weights, desc=f"Serializing and writing weights ({quant_type})"
    ):
        if if_quant:
            if quant_type in ["w8a32", "w8a16"]:
                q, s, err = quantize_q80(w, group_size)
                serialize_int8(out_file, q)  # save the tensor in int8
                serialize_fp32(out_file, s)  # save scale factors (fp32)
                ew.append((err, name))
                # print(f"Quantize {name} {tuple(w.shape)} to Q8_0 with max error {err}")
            else:
                # Not supported layer quantization for int4
                assert (group_size != -2)
                q, s, err = quantize_q40(w, group_size)
                serialize_int4(out_file, q)
                serialize_fp32(out_file, s)
                ew.append((err, name))
                # print(f"Quantize {name} {tuple(w.shape)} to Q4_0 with max error {err}")
        else:
            serialize_else(out_file, w)
    # print the highest error across all weights, should be very small, e.g. O(~0.001)
    ew.sort(reverse=True)
    print(
        f"Tensor {ew[0][1]} has max quantization group error across all weights: {ew[0][0]}"
    )

    out_file.close()
    print(f"Wrote {filepath}")


def model_info(model):
    p = model.params
    hidden_dim = model.layers[0].feed_forward.w1.weight.shape[0]
    n_kv_heads = p.n_heads if p.n_kv_heads is None else p.n_kv_heads
    n_heads = p.n_heads
    print("dim:", p.dim)
    print("hidden_dim:", hidden_dim)
    print("n_heads:", n_heads)
    print("n_kv_heads:", n_kv_heads)
    print("vocab_size:", p.vocab_size)
    print("max_seq_len:", p.max_seq_len)

    print()
    print("tok_embeddings shape:", model.tok_embeddings.weight.shape)
    print("model norm shape:", model.norm.weight.shape)
    print("attn_norm shape:", model.layers[0].attention_norm.weight.shape)
    print("ffn_norm shape:", model.layers[0].ffn_norm.weight.shape)
    print("wq shape:", model.layers[0].attention.wq.weight.shape)
    print("wk shape:", model.layers[0].attention.wk.weight.shape)
    print("wv shape:", model.layers[0].attention.wv.weight.shape)
    print("wo shape:", model.layers[0].attention.wo.weight.shape)
    print("w1 shape:", model.layers[0].feed_forward.w1.weight.shape)
    print("w2 shape:", model.layers[0].feed_forward.w2.weight.shape)
    print("w3 shape:", model.layers[0].feed_forward.w3.weight.shape)
    print("output shape:", model.output.weight.shape)
    print("freqs_cis shape:", model.freqs_cis.shape)
    print()

    print(model)


# -----------------------------------------------------------------------------
# Load / import functions


def load_hf_model(model_path, model_type: ModelType):

    try:
        from transformers import AutoModelForCausalLM
    except ImportError:
        print("Error: transformers package is required to load huggingface models")
        print("Please run `pip install transformers` to install it")
        return None

    # load HF model
    hf_model = AutoModelForCausalLM.from_pretrained(model_path)
    hf_dict = hf_model.state_dict()

    # convert LlamaConfig to ModelArgs
    config = (
        llama2.ModelArgs() if model_type == ModelType.Llama2 else llama3.ModelArgs()
    )
    config.dim = hf_model.config.hidden_size
    config.n_layers = hf_model.config.num_hidden_layers
    config.n_heads = hf_model.config.num_attention_heads
    config.n_kv_heads = hf_model.config.num_key_value_heads
    config.vocab_size = hf_model.config.vocab_size
    config.norm_eps = hf_model.config.rms_norm_eps
    # config.hidden_dim = hf_model.config.intermediate_size
    config.max_seq_len = hf_model.config.max_position_embeddings

    if hf_model.config.rope_theta is not None:
        config.rope_theta = hf_model.config.rope_theta

    # create a new Transformer object and set weights
    model = (
        llama2.Transformer(config)
        if model_type == ModelType.Llama2
        else llama3.Transformer(config)
    )

    model.tok_embeddings.weight = nn.Parameter(
        hf_dict["model.embed_tokens.weight"])
    model.norm.weight = nn.Parameter(hf_dict["model.norm.weight"])

    # huggingface permutes WQ and WK, this function reverses it
    def permute_reverse(w, n_heads=config.n_heads):
        return (
            w.view(n_heads, 2, w.shape[0] // n_heads // 2, *w.shape[1:])
            .transpose(1, 2)
            .reshape(w.shape)
        )

    for layer in model.layers:
        i = layer.layer_id
        layer.attention_norm.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.input_layernorm.weight"]
        )
        layer.attention.wq.weight = nn.Parameter(
            permute_reverse(
                hf_dict[f"model.layers.{i}.self_attn.q_proj.weight"])
        )
        layer.attention.wk.weight = nn.Parameter(
            permute_reverse(
                hf_dict[f"model.layers.{i}.self_attn.k_proj.weight"],
                n_heads=config.n_kv_heads,
            )
        )
        layer.attention.wv.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.self_attn.v_proj.weight"]
        )
        layer.attention.wo.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.self_attn.o_proj.weight"]
        )
        layer.ffn_norm.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.post_attention_layernorm.weight"]
        )
        layer.feed_forward.w1.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.mlp.gate_proj.weight"]
        )
        layer.feed_forward.w2.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.mlp.down_proj.weight"]
        )
        layer.feed_forward.w3.weight = nn.Parameter(
            hf_dict[f"model.layers.{i}.mlp.up_proj.weight"]
        )

    # final classifier
    model.output.weight = nn.Parameter(hf_dict["lm_head.weight"])
    model.eval()
    return model


# -----------------------------------------------------------------------------
# CLI entrypoint

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dtype",
        choices=["fp32", "fp16", "w8a32", "w8a16", "w4a32", "w4a16"],
        default="fp32",
        nargs="?",
        help="dtype of the model, w8a16/w8a32/w4a16/w4a32 are quantized types, default to fp32",
    )
    parser.add_argument(
        "--group-size",
        type=int,
        default=64,
        help="group size for quantization, default to 64. Use -1 to quantize the row/column. Use -2 to quantize the layer",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show model info w/o conversion"
    )
    parser.add_argument(
        "--out", type=str, help="if specified, use this as model output path"
    )
    parser.add_argument("hf_model", type=str,
                        help="huggingface model name or path")
    args = parser.parse_args()

    # Supported models:
    # - Llama 2
    # - Llama 3
    if "Llama-2" in args.hf_model:
        model_type = ModelType.Llama2
    elif "Llama-3" in args.hf_model:
        model_type = ModelType.Llama3
    else:
        raise ValueError(f"Unknown model type {args.hf_model}")

    model = load_hf_model(args.hf_model, model_type)
    model_name = args.hf_model.split("/")[-1]

    if args.dry_run:
        model_info(model)
    else:
        pwd = os.path.dirname(os.path.realpath(__file__))
        if args.dtype in ["fp32", "fp16"]:
            default_path = os.path.join(
                pwd, f"{model_name}-{args.dtype}.model")
            model_path = args.out if args.out else default_path
            fp_export(model, model_path, model_type, args.dtype)
        else:
            default_path = os.path.join(
                pwd, f"{model_name}-{args.dtype}-g{args.group_size}.model"
            )
            model_path = args.out if args.out else default_path
            int_export(
                model,
                model_path,
                model_type,
                group_size=args.group_size,
                quant_type=args.dtype,
            )
