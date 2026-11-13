#include <iostream>
#include <stdexcept>
#include <stdfloat>
#include <random>
#include <openvino/openvino.hpp>
#include <openvino/opsets/opset15.hpp>
using std::float16_t;

const char HELP_MESSAGE[] = "Usage: ./program_name seq_len n_heads head_dim";
                             
int seq_len, n_heads, head_dim;

std::float16_t *Q_buffer;
std::float16_t *K_buffer;
std::float16_t *V_buffer;
std::float16_t *O_buffer;

ov::Core core;

void prepare()
{
    Q_buffer = new float16_t[seq_len * head_dim * n_heads];
    K_buffer = new float16_t[seq_len * head_dim * n_heads];
    V_buffer = new float16_t[seq_len * head_dim * n_heads];
    O_buffer = new float16_t[seq_len * head_dim * n_heads];

    auto rd = std::random_device();
    auto gen = std::minstd_rand(rd());
    auto dis = std::uniform_real_distribution<std::float32_t>(-1.0f, 1.0f);
    for (int i = 0; i < seq_len * head_dim * n_heads; ++i) {
        Q_buffer[i] = dis(gen);
        K_buffer[i] = dis(gen);
        V_buffer[i] = dis(gen);
    }
}


int main(int argc, char* argv[])
{
    if (argc != 4) {
        std::cerr << HELP_MESSAGE << std::endl;
        return 1;
    }

    try {
        seq_len = std::stoi(argv[1]);
        n_heads = std::stoi(argv[2]);
        head_dim = std::stoi(argv[3]);
    } catch (const std::invalid_argument& e) {
        std::cerr << "Invalid argument: " << e.what() << std::endl;
        return 1;
    } catch (const std::out_of_range& e) {
        std::cerr << "Out of range: " << e.what() << std::endl;
        return 1;
    }

    if (seq_len <= 0 || head_dim <= 0 || n_heads <= 0) {
        std::cerr << "All dimensions must be positive integers." << std::endl;
        return 1;
    }

    prepare();

    std::cout << O_buffer[0] << std::endl; // Print the first element of the output tensor before inference
    auto Q = std::make_shared<ov::opset15::Parameter>(
        ov::element::f16, ov::PartialShape{n_heads, ov::Dimension::dynamic(), head_dim});
    auto K = std::make_shared<ov::opset15::Parameter>(
        ov::element::f16, ov::PartialShape{n_heads, ov::Dimension::dynamic(),
        head_dim});
    auto V = std::make_shared<ov::opset15::Parameter>(
        ov::element::f16, ov::PartialShape{n_heads, ov::Dimension::dynamic(),
        head_dim});
    auto scaled_dot_product_attention =
        std::make_shared<ov::opset15::ScaledDotProductAttention>(
            Q, K, V, false);
    auto O = std::make_shared<ov::opset15::Result>(scaled_dot_product_attention);
    auto model = std::make_shared<ov::Model>(
        ov::ResultVector{O}, ov::ParameterVector{Q, K, V});
    model->set_friendly_name("ScaledDotProductAttentionModel");
    auto compiled_model = core.compile_model(model, "GPU");
    auto infer_request = compiled_model.create_infer_request();
    infer_request.set_input_tensor(0, ov::Tensor(ov::element::f16, ov::Shape{n_heads, seq_len, head_dim}, Q_buffer));
    infer_request.set_input_tensor(1, ov::Tensor(ov::element::f16, ov::Shape{n_heads, seq_len, head_dim}, K_buffer));
    infer_request.set_input_tensor(2, ov::Tensor(ov::element::f16, ov::Shape{n_heads, seq_len, head_dim}, V_buffer));
    infer_request.set_output_tensor(0, ov::Tensor(ov::element::f16, ov::Shape{n_heads, seq_len, head_dim}, O_buffer));

    infer_request.infer();
    
    std::cout << O_buffer[0] << std::endl; // Print the first element of the output tensor
    return 0;
}