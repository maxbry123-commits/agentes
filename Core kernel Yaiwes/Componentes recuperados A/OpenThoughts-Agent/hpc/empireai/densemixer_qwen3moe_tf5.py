"""DenseMixer Qwen3-MoE custom forward — PORTED to transformers >= 5.x.

Drop-in replacement for densemixer 1.0.1's
`densemixer/models/qwen3_moe_custom.py`, which is INCOMPATIBLE with
transformers 5.x (it crashes at the first forward with
`AttributeError: 'tuple' object has no attribute 'to'`).

WHY the stock file breaks on transformers 5.12 (Qwen3MoE was refactored):
  * `self.gate` is now a `Qwen3MoeTopKRouter` whose `forward` returns a TUPLE
    `(router_logits, router_scores, router_indices)` — stock densemixer did
    `self.gate(x).to(dtype)` assuming a logits TENSOR → crash. `top_k`,
    `num_experts`, `norm_topk_prob` now live on `self.gate`, not the block.
  * `self.experts` is now a FUSED `Qwen3MoeExperts` module holding 3D weight
    params (`gate_up_proj[e]`, `down_proj[e]`, `act_fn`) — no per-expert
    `self.experts[e]` nn.Module list to call.
  * the block's `forward` now returns a bare TENSOR — stock densemixer returned
    `(final_output, router_logits)`, which the new decoder layer can't consume.

The DenseMixer MECHANISM is preserved byte-for-byte in intent (yaof20/DenseMixer,
marin #7088): dense forward through ALL experts + full-softmax router, an STE
combine (forward value = the sparse/top-k output; backward = the dense
all-experts gradient), and a per-expert gradient hook so expert *params* still
update only on their routed tokens. Router gets the dense counterfactual gradient;
inference is untouched (this forward is training-only, installed by
`apply_qwen3_moe_patch()`).

Installed into the image by hpc/empireai/mega_densemixer_layer.sbatch (copied over
the pip-installed file so the fix is baked into mega_final_dm.sqsh).
"""

import torch
import torch.nn.functional as F

try:
    from densemixer.logging_utils import log_custom_forward_usage
except Exception:  # pragma: no cover - logging is best-effort

    def log_custom_forward_usage(_name):
        return None


class CustomQwen3MoeSparseMoeBlock:
    """Patched forward for transformers>=5.x `Qwen3MoeSparseMoeBlock`."""

    @staticmethod
    def forward(self, hidden_states: torch.Tensor):
        # marker: tf5-ported-densemixer  (grepped by the build gate)
        log_custom_forward_usage("Qwen3-MoE")

        batch_size, seq_length, hidden_dim = hidden_states.shape
        dtype = hidden_states.dtype
        device = hidden_states.device

        flat_hidden = hidden_states.view(-1, hidden_dim)  # (N, hidden)
        n_tokens = flat_hidden.size(0)

        gate = self.gate  # Qwen3MoeTopKRouter (transformers 5.x)
        num_experts = gate.num_experts
        top_k = gate.top_k
        norm_topk_prob = gate.norm_topk_prob

        # full router logits over ALL experts (new router returns them as elem 0)
        router_logits, _, _ = gate(flat_hidden)
        router_logits = router_logits.to(dtype=dtype)  # (N, num_experts)

        routing_weights = F.softmax(
            router_logits, dim=1, dtype=torch.float
        )  # (N, num_experts)
        routing_weights_topk, selected_experts = torch.topk(
            routing_weights, top_k, dim=-1
        )
        if norm_topk_prob:
            norm_ratio = routing_weights_topk.sum(dim=-1, keepdim=True)
            routing_weights_topk = routing_weights_topk / norm_ratio
            mask = (
                F.one_hot(selected_experts, num_classes=num_experts)
                .sum(dim=1)
                .to(dtype)
            )
            # partscale_fix_expert (stock densemixer default): detached renorm on the
            # off-top-k mass, live renorm on the selected mass.
            routing_weights = (
                routing_weights * (1.0 - mask) / norm_ratio.detach()
                + routing_weights * mask / norm_ratio
            )
        routing_weights_topk = routing_weights_topk.to(dtype=dtype)
        routing_weights = routing_weights.to(dtype=dtype)

        dense_outputs = torch.zeros((n_tokens, hidden_dim), dtype=dtype, device=device)
        sparse_outputs = torch.zeros((n_tokens, hidden_dim), dtype=dtype, device=device)

        experts = self.experts  # fused Qwen3MoeExperts (3D weight params)
        gate_up_proj = experts.gate_up_proj  # (num_experts, 2*inter, hidden)
        down_proj = experts.down_proj  # (num_experts, hidden, inter)
        act_fn = experts.act_fn

        for expert_idx in range(num_experts):
            # per-expert MLP, computed for ALL tokens (the dense forward)
            gate_up = F.linear(flat_hidden, gate_up_proj[expert_idx])
            g, u = gate_up.chunk(2, dim=-1)
            expert_output = F.linear(act_fn(g) * u, down_proj[expert_idx]).to(
                dtype=dtype
            )  # (N, hidden)

            # per-expert grad hook: expert params only see grad from their routed tokens
            activation_mask = (
                (selected_experts == expert_idx)
                .any(dim=1)
                .float()
                .unsqueeze(-1)
                .to(dtype)
            )
            if expert_output.requires_grad:
                expert_output.register_hook(
                    lambda grad, mask=activation_mask: grad * mask
                )

            # dense accumulation (full-softmax weight for this expert, every token)
            weight_full = routing_weights[:, expert_idx].unsqueeze(-1)  # (N, 1)
            dense_outputs = dense_outputs + expert_output * weight_full

            # sparse accumulation (only tokens where this expert is in top-k)
            matches = selected_experts == expert_idx  # (N, top_k)
            if matches.any():
                token_indices, k_indices = torch.where(matches)
                weights_topk = routing_weights_topk[token_indices, k_indices].unsqueeze(
                    -1
                )
                sparse_outputs[token_indices] = (
                    sparse_outputs[token_indices]
                    + expert_output[token_indices] * weights_topk
                )

        # STE: forward value = sparse (conventional) output; backward grad = dense.
        final_flat = sparse_outputs.detach() + (dense_outputs - dense_outputs.detach())
        final_flat = final_flat.to(dtype=dtype)
        # transformers 5.x block returns a bare TENSOR (not a tuple).
        return final_flat.view(batch_size, seq_length, hidden_dim)
