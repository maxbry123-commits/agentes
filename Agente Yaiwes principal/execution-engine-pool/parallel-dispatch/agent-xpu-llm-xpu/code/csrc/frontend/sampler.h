#pragma once

namespace hllm {
typedef struct {
    float prob;
    int index;
} ProbIndex; // struct used when sorting probabilities during top-p sampling

// The Sampler, which takes logits and returns a sampled token
// sampling can be done in a few ways: greedy argmax, sampling, top-p sampling
class Sampler {
  public:
    Sampler(int vocab_size);
    ~Sampler();

    // Sample from logits (probs)
    // input: logits (float[], length = vocab_size)
    // output: sampled next token id
    int sample(void* logits, float temperature = 0.6, float top_p = 0.9, int seed = -1);

  private:
    int vocab_size_;
    ProbIndex* prob_index_; // buffer used in top-p sampling
    float gen_rand_f32(int seed) const;

    int sample_argmax(float* probs) const;

    int sample_mult(float* probs, int seed) const;

    // Top-p sampling selects the smallest set of tokens whose cumulative
    // probability exceeds the probability p The distribution is renormalized to
    // the selected tokens probs: the probability distribution over the vocabulary
    // p: the probability threshold for top-p sampling
    int sample_top_p(float* probs, float top_p, int seed) const;
};
} // namespace hllm
