#include "model/transformer.h"
#include <cstdint>
#include <gtest/gtest.h>
#include <iostream>
#include <string>
#ifdef _WIN32
#define F_OK 0
#endif

using namespace hllm;

class ModelLoadTest : public ::testing::Test {
protected:
  Transformer *model;
  const char *model_7b_fp32_path = "../../models/llama2/Llama-2-7b-fp32.model";
  const char *model_7b_fp16_path = "../../models/llama2/Llama-2-7b-fp16.model";
};

TEST_F(ModelLoadTest, LoadFP32Model) {
  if (access(model_7b_fp32_path, F_OK) == -1) {
    FAIL() << "******[ERROR] Model file not found: " << model_7b_fp32_path;
  }
  model =
      new Transformer(model_7b_fp32_path, get_kernel(hllm::DeviceType::CPU));
  auto config = model->get_config();
  EXPECT_EQ(config.dim, 4096);
  EXPECT_EQ(config.hidden_dim, 11008);
  EXPECT_EQ(config.n_layers, 32);
  EXPECT_EQ(config.n_heads, 32);
  EXPECT_EQ(config.n_kv_heads, 32);
  EXPECT_EQ(config.vocab_size, 32000);
  EXPECT_EQ(config.max_seq_len, 4096);

  auto token_embedding_table = model->get_token_embedding_table();
  auto layer_weights = model->get_layer_weights();
  auto final_rms_weight = model->get_final_rms_weight();
  auto out_weight = model->get_out_weight();

  auto tval = [](Tensor &t, int i, int j) -> uint32_t {
    return *((uint32_t *)t.get_data() + t.offset(i, j));
  };
  auto tval_float32 = [](Tensor &t, int i, int j) -> float {
    return *((float *)t.get_data() + t.offset(i, j));
  };
  EXPECT_EQ(tval_float32(layer_weights[13].attn_rms_weight, 333, 0), 0.3984375);

  EXPECT_EQ(tval(token_embedding_table, 0, 0), 0x35a80000);
  EXPECT_EQ(tval(layer_weights[2].attn_wq, 388, 2323), 0x3c130000);
  EXPECT_EQ(tval(layer_weights[16].attn_wk, 222, 999), 0xbcdf0000);
  EXPECT_EQ(tval(layer_weights[23].ffn_up, 2044, 2000), 0x3cd10000);
  EXPECT_EQ(tval(layer_weights[9].ffn_rms_weight, 333, 0), 0x3e6d0000);
  EXPECT_EQ(tval(final_rms_weight, 0, 0), 0x3fef0000);
  EXPECT_EQ(tval(out_weight, 333, 333), 0xbcc30000);
  delete model;
}

TEST_F(ModelLoadTest, LoadFP16Model) {
  if (access(model_7b_fp16_path, F_OK) == -1) {
    FAIL() << "******[ERROR] Model file not found: " << model_7b_fp16_path;
  }
  model =
      new Transformer(model_7b_fp16_path, get_kernel(hllm::DeviceType::CPU));
  auto config = model->get_config();
  EXPECT_EQ(config.dim, 4096);
  EXPECT_EQ(config.hidden_dim, 11008);
  EXPECT_EQ(config.n_layers, 32);
  EXPECT_EQ(config.n_heads, 32);
  EXPECT_EQ(config.n_kv_heads, 32);
  EXPECT_EQ(config.vocab_size, 32000);
  EXPECT_EQ(config.max_seq_len, 4096);

  auto token_embedding_table = model->get_token_embedding_table();
  auto layer_weights = model->get_layer_weights();
  auto final_rms_weight = model->get_final_rms_weight();
  auto out_weight = model->get_out_weight();

  auto tval = [](Tensor &t, int i, int j) -> uint16_t {
    return *((uint16_t *)t.get_data() + t.offset(i, j));
  };
  EXPECT_EQ(tval(token_embedding_table, 0, 0), 0x0015);
  EXPECT_EQ(tval(layer_weights[2].attn_wq, 388, 2323), 0x2098);
  EXPECT_EQ(tval(layer_weights[16].attn_wk, 222, 999), 0xa6f8);
  EXPECT_EQ(tval(layer_weights[23].ffn_up, 2044, 2000), 0x2688);
  EXPECT_EQ(tval(layer_weights[9].ffn_rms_weight, 333, 0), 0x3368);
  EXPECT_EQ(tval(final_rms_weight, 0, 0), 0x3f78);
  EXPECT_EQ(tval(out_weight, 333, 333), 0xa618);

  delete model;
}
