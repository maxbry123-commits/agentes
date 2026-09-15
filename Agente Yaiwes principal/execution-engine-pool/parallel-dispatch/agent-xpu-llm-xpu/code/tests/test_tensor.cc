#include "basic/tensor.h"
#include <gtest/gtest.h>

using namespace hllm;

TEST(TensorTest, CreateTensor1D) {
  Tensor t = create_tensor(Dtype::float32, {10});
  ASSERT_EQ(t.dims(), 1);
  ASSERT_EQ(t.shape(0), 10);
}

TEST(TensorTest, CreateTensor2D) {
  Tensor t = create_tensor(Dtype::float32, {10, 20});
  ASSERT_EQ(t.dims(), 2);
  ASSERT_EQ(t.shape(0), 10);
  ASSERT_EQ(t.shape(1), 20);
}

TEST(TensorTest, SetAndCopyData) {
  Tensor t = create_tensor(Dtype::float32, {10});
  float data[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
  t.copy_data(data);
  float *tensor_data = (float *)t.get_data();
  for (int i = 0; i < 10; ++i) {
    ASSERT_EQ(tensor_data[i], data[i]);
  }
}

TEST(TensorTest, DeepCopy) {
  Tensor t = create_tensor(Dtype::int32, {10, 20}, hllm::ALLOC);
  *((int32_t *)t.get_data()) = 33;
  *((int32_t *)t.get_data() + t.offset(1, 5)) = 1;
  *((int32_t *)t.get_data() + t.offset(3, 3)) = 2;
  *((int32_t *)t.get_data() + t.offset(5, 1)) = 3;
  Tensor t_copy = t.copy();
  ASSERT_EQ(t_copy.dims(), t.dims());
  for (size_t i = 0; i < (size_t)t.dims(); ++i) {
    ASSERT_EQ(t_copy.shape(i), t.shape(i));
  }
  ASSERT_EQ(*((int32_t *)t_copy.get_data()), 33);
  ASSERT_EQ(*((int32_t *)t_copy.get_data() + t_copy.offset(1, 5)), 1);
  ASSERT_EQ(*((int32_t *)t_copy.get_data() + t_copy.offset(3, 3)), 2);
  ASSERT_EQ(*((int32_t *)t_copy.get_data() + t_copy.offset(5, 1)), 3);
}
