#pragma once
/**
 * @file cgraph.h
 * @brief Compute graph. Up to now, we only support a compute graph with a
 * single output node.
 */
#include "tensor.h"

#include <map>
#include <string>

namespace hllm {
class [[deprecated(
    "This class is deprecated and will be removed in a future version")]] ComputeGraph {
  public:
    ComputeGraph() = default;
    ~ComputeGraph() = default;

    void create_from_output_node(Tensor& output_node);
    Tensor get_node_by_name(const std::string& name);

    std::vector<Tensor> nodes_storage;

  private:
    std::map<std::string, Tensor> nodes_;
};
} // namespace hllm