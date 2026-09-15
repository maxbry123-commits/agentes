#include "sampler.h"

#include <algorithm>
#include <random>

static void mat_scale_inplace(float* t, int size, float scale) {
    for (int i = 0; i < size; i++) {
        t[i] *= scale;
    }
}

static void softmax_inplace_1D(float* t, int size) {
    float max_val = t[0];
    for (int i = 1; i < size; i++) {
        max_val = std::max(max_val, t[i]);
    }
    float sum = 0.0f;
    for (int i = 0; i < size; i++) {
        t[i] = std::exp(t[i] - max_val);
        sum += t[i];
    }
    for (int i = 0; i < size; i++) {
        t[i] /= sum;
    }
}

namespace hllm {
Sampler::Sampler(int vocab_size) : vocab_size_(vocab_size) {
    prob_index_ = new ProbIndex[vocab_size];
}

Sampler::~Sampler() { delete[] prob_index_; }

int Sampler::sample(void* _logits, float temperature, float top_p, int seed) {
    float* logits = static_cast<float*>(_logits);
    int next;
    if (temperature == 0.0f) {
        // greedy argmax sampling: take the token with the highest probability
        next = sample_argmax(logits);
    } else {
        // apply the temperature to the logits
        mat_scale_inplace(logits, vocab_size_, 1.0f / temperature);
        // apply softmax to the logits to get the probabilities for next token
        softmax_inplace_1D(logits, vocab_size_);
        if (top_p <= 0 || top_p >= 1) {
            // simply sample from the predicted probability distribution
            next = sample_mult(logits, seed);
        } else {
            // top-p (nucleus) sampling, clamping the least likely tokens to zero
            next = sample_top_p(logits, top_p, seed);
        }
    }
    return next;
}

float Sampler::gen_rand_f32(int seed) const {
    static std::random_device rd;
    int seed_ = (seed == -1) ? rd() : seed;
    static std::mt19937 gen(seed_);
    static std::uniform_real_distribution<float> dis(0.0f, 1.0f);
    return dis(gen);
}

// return the index that has the highest probability
int Sampler::sample_argmax(float* probs) const {
    int max_i = 0;
    float max_p = probs[0];
    for (int i = 1; i < vocab_size_; i++) {
        if (probs[i] > max_p) {
            max_i = i;
            max_p = probs[i];
        }
    }
    return max_i;
}

// Sample index from probabilities (they must sum to 1!)
int Sampler::sample_mult(float* probs, int seed) const {
    float cdf = 0.0f;
    float thresh = gen_rand_f32(seed);
    for (int i = 0; i < vocab_size_; i++) {
        cdf += probs[i];
        if (thresh < cdf) {
            return i;
        }
    }
    return vocab_size_ - 1; // in case of rounding errors
}

// Top-p sampling selects the smallest set of tokens whose cumulative
// probability exceeds the probability p The distribution is renormalized to the
// selected tokens probs: the probability distribution over the vocabulary p:
// the probability threshold for top-p sampling
int Sampler::sample_top_p(float* probs, float top_p, int seed) const {
    int sampled_size = 0;
    const float cutoff = (1.0f - top_p) / (vocab_size_ - 1);
    // cutoff is the minimum probability to be included in the top-p sampling
    for (int i = 0; i < vocab_size_; i++) {
        if (probs[i] >= cutoff) {
            prob_index_[sampled_size].prob = probs[i];
            prob_index_[sampled_size].index = i;
            sampled_size++;
        }
    }
    // sort the probabilities in descending order
    std::sort(prob_index_, prob_index_ + sampled_size,
              [](const ProbIndex& a, const ProbIndex& b) { return a.prob > b.prob; });

    // truncate the list where cumulative probability exceeds top_p
    float cumulative_prob = 0.0f;
    int last_idx = sampled_size - 1; // in case of rounding errors consider all elements
    for (int i = 0; i < sampled_size; i++) {
        cumulative_prob += prob_index_[i].prob;
        if (cumulative_prob > top_p) {
            last_idx = i;
            break; // we've exceeded topp by including last_idx
        }
    }

    // sample from the truncated list
    float thresh = gen_rand_f32(seed);
    float r = thresh * cumulative_prob;
    float cdf = 0.0f;
    for (int i = 0; i <= last_idx; i++) {
        cdf += prob_index_[i].prob;
        if (r < cdf) {
            return prob_index_[i].index;
        }
    }
    return prob_index_[last_idx].index; // in case of rounding errors
}

} // namespace hllm