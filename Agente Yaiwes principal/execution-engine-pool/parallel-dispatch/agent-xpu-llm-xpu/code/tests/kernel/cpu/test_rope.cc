#include "fp16/include/half/half.hpp"
#include "kernel/kernel.h"
#include "model/transformer.h"
#include "util/util.h"
#include <gtest/gtest.h>
#include <iostream>
#ifdef _WIN32
#include <io.h>
#define F_OK 0 // Define F_OK for Windows
#else
#include <unistd.h>
#endif

using namespace hllm;

static auto cpu_kernel = get_kernel(hllm::DeviceType::CPU);

class RopeTestCPU : public ::testing::Test {
protected:
  Transformer *model;
  const char *model_7b_fp32_path =
      "../../../../models/llama2/Llama-2-7b-fp32.model";

  RopeTestCPU() {
    if (access(model_7b_fp32_path, F_OK) == -1) {
      std::cerr << "******[ERROR] Model file not found: " << model_7b_fp32_path;
      exit(1);
    }
    model = new Transformer(model_7b_fp32_path, cpu_kernel);
  }
  ~RopeTestCPU() { delete model; }
};

TEST_F(RopeTestCPU, Rope1D_fp32) {
  auto config = model->get_config();
  auto freqs_cis = model->get_freqs_cis();
  int dim = config.dim;
  int n_heads = config.n_heads;
  // int head_size = dim / n_heads;
  float *x = new float[dim];
  for (int i = 0; i < dim; i++) {
    x[i] = (float)rand() / RAND_MAX;
  }
  auto t1 = create_tensor(Dtype::float32, {(size_t)dim});
  t1.copy_data(x);
  auto t2 = t1.copy();

  auto last_time = get_time();
  cpu_kernel->rope(t1, 33, n_heads, freqs_cis); // precompute freqs_cis
  std::cout << "Elapsed time (rope-1d) w/ precompute: "
            << elapsed_time_ms(last_time) << "ms\n";
  last_time = get_time();
  cpu_kernel->rope(t2, 33, n_heads,
                   std::nullopt); // compute freqs_cis on the fly
  std::cout << "Elapsed time (rope-1d) w/o precompute: "
            << elapsed_time_ms(last_time) << "ms\n";

  EXPECT_EQ(*((float *)t1.at(0)), *((float *)t2.at(0)));
  EXPECT_EQ(*((float *)t1.at(1)), *((float *)t2.at(1)));
  EXPECT_EQ(*((float *)t1.at(233)), *((float *)t2.at(233)));
  EXPECT_EQ(*((float *)t1.at((int)dim * 0.666)),
            *((float *)t2.at((int)dim * 0.666)));

  delete[] x;
}

TEST_F(RopeTestCPU, Rope2D_fp32) {
  auto config = model->get_config();
  auto freqs_cis = model->get_freqs_cis();
  int dim = config.dim;
  int n_heads = config.n_heads;
  // int head_size = dim / n_heads;
  float *x = new float[dim * 1000];
  for (int i = 0; i < dim * 1000; i++) {
    x[i] = (float)rand() / RAND_MAX;
  }
  auto t1 = create_tensor(Dtype::float32, {1000, (size_t)dim});
  t1.copy_data(x);
  auto t2 = t1.copy();

  auto last_time = get_time();
  cpu_kernel->rope(t1, -1, n_heads, freqs_cis); // precompute freqs_cis
  std::cout << "Elapsed time (rope-2d) w/ precompute: "
            << elapsed_time_ms(last_time) << "ms\n";
  last_time = get_time();
  cpu_kernel->rope(t2, -1, n_heads,
                   std::nullopt); // compute freqs_cis on the fly
  std::cout << "Elapsed time (rope-2d) w/o precompute: "
            << elapsed_time_ms(last_time) << "ms\n";

  EXPECT_EQ(*((float *)t1.at(0, 0)), *((float *)t2.at(0, 0)));
  EXPECT_EQ(*((float *)t1.at(0, 1)), *((float *)t2.at(0, 1)));
  EXPECT_EQ(*((float *)t1.at(1, 233)), *((float *)t2.at(1, 233)));
  EXPECT_EQ(*((float *)t1.at(1, (int)dim * 0.666)),
            *((float *)t2.at(1, (int)dim * 0.666)));
  EXPECT_EQ(*((float *)t1.at(333, 1023)), *((float *)t2.at(333, 1023)));

  delete[] x;
}