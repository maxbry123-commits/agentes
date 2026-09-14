// FILE: src/module/test_sampler.cc

#include "module/sampler.h"
#include <gtest/gtest.h>

namespace hllm {

class SamplerTest : public ::testing::Test {
protected:
  void SetUp() override {
    // Initialize the Sampler object with some default values
    vocab_size = 5;
    temperature = 1.0f;
    top_p = 0.9f;
    seed = 42;
  }

  int vocab_size;
  float temperature;
  float top_p;
  int seed;
};

TEST_F(SamplerTest, GreedyArgmaxSampling) {
  float logits[] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
  Tensor t = create_tensor(Dtype::float32, {(size_t)vocab_size});
  t.copy_data(logits);
  temperature = 0.0f; // Set temperature to 0 for greedy argmax sampling
  Sampler sampler = Sampler(vocab_size, temperature, top_p, seed);
  int sampled_index = sampler.sample(t);
  EXPECT_EQ(sampled_index, 4); // The highest probability index
}

TEST_F(SamplerTest, SamplingWithTemperature) {
  float logits[] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
  Tensor t = create_tensor(Dtype::float32, {(size_t)vocab_size});
  t.copy_data(logits);
  temperature = 1.0f; // Set temperature to 1 for normal sampling
  Sampler sampler = Sampler(vocab_size, temperature, top_p, seed);
  int sampled_index = sampler.sample(t);
  EXPECT_GE(sampled_index, 0);
  EXPECT_LT(sampled_index, vocab_size);
}

TEST_F(SamplerTest, TopPSampling) {
  float logits[] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
  Tensor t = create_tensor(Dtype::float32, {(size_t)vocab_size});
  t.copy_data(logits);
  top_p = 0.6f; // Set top_p to 0.6 for top-p sampling
  Sampler sampler = Sampler(vocab_size, temperature, top_p, seed);
  int sampled_index = sampler.sample(t);
  EXPECT_GE(sampled_index, 0);
  EXPECT_LT(sampled_index, vocab_size);
}

} // namespace hllm

int main(int argc, char **argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}