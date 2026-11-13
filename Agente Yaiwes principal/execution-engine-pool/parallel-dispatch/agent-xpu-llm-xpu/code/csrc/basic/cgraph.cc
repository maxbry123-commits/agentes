#include "cgraph.h"

#include <cstdlib>
using namespace hllm;

static char* visited_name;

static void dfs_visit(Tensor& node, std::vector<Tensor>& nodes_storage,
                      std::map<std::string, Tensor>& nodes, int& id) {
    if (node->name() == visited_name || (node->name() && nodes.find(node->name()) != nodes.end())) {
        return;
    }

    for (auto& src : node->src()) {
        dfs_visit(src, nodes_storage, nodes, id);
    }
    nodes_storage.emplace_back(node);
    if (node->name() != nullptr) {
        nodes[node->name()] = node;
    } else {
        std::string name = std::to_string(id++);
        nodes[name] = node;
        node->set_name(visited_name);
    }
}

static void dfs_clear_visited(Tensor& node) {
    if (node->name() == nullptr) {
        return;
    }

    for (auto& src : node->src()) {
        dfs_clear_visited(src);
    }
    if (node->name() == visited_name) {
        node->set_name(nullptr);
    }
}

void hllm::ComputeGraph::create_from_output_node(Tensor& output_node) {
    assert(nodes_storage.empty());
    int id = 0;
    assert(visited_name == nullptr);
    visited_name = (char*)malloc(10);
    strcpy(visited_name, "visited");
    dfs_visit(output_node, nodes_storage, nodes_, id);
    dfs_clear_visited(output_node);
    free((void*)visited_name);
    visited_name = nullptr;
}

Tensor hllm::ComputeGraph::get_node_by_name(const std::string& name) { return nodes_.at(name); }
