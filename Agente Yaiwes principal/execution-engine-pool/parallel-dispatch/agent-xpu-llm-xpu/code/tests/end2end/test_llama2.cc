#include "fp16/include/half/half.hpp"
#include "kernel/kernel.h"
#include "model/transformer.h"
#include "module/sampler.h"
#include "module/tokenizer.h"
#include <fcntl.h>
#include <gtest/gtest.h>
#include <memory>
#include <sys/stat.h>
#ifdef _WIN32
#include <io.h>
#else
#include <sys/mman.h>
#include <unistd.h>
#endif

using namespace hllm;

#define DEBUG_PREFILL
#define DEBUG_DECODE
#define max(a, b) ((a) > (b) ? (a) : (b))

static auto cpu_kernel = get_kernel(hllm::DeviceType::CPU);

template <typename T1, typename T2>
bool array_eq(T1 *a, T2 *b, int len, float error_bound = 3e-2) {
  for (int i = 0; i < len; i++) {
    if (std::abs(a[i] - b[i]) > abs_error_bound) {
      std::cerr << "Mismatch at index " << i << ": " << a[i] << " != " << b[i]
                << std::endl;
      ok = false;
      return false;
    }
  }
  return ok;
}

class Llama2Test : public Transformer, public ::testing::Test {
public:
  Llama2Test(const char *model_path, hllm::DeviceType device);
  ~Llama2Test();

  int steps;
  char *prompt;
  int *prompt_tokens;
  int prompt_len;
  void parse_prompt(const char *prompt_path);

  // Intermediate results
  unsigned long seq_len;
  float *tok_embeddings_res;
  std::shared_ptr<float *[]> attn_out_res = nullptr;
  std::shared_ptr<float *[]> ffn_out_res = nullptr;
  float *final_rms_out_res;
  float *logits_res;
  int ref_fd;
  void *ref_addr;
  off_t ref_size;
  void read_ref(const char *ref_path);

  SentencePieceTokenizer tokenizer;
  Sampler sampler;
  Logger &logger = Logger::get_instance();
};

Llama2Test::Llama2Test(const char *model_path, hllm::DeviceType device)
    : Transformer(model_path, get_kernel(device)),
      tokenizer("../../../models/llama2/vocab.model"),
      sampler(this->config_.vocab_size, 0.0, 0.0, 0) {
  this->steps = 5;
  this->prompt = nullptr;
  this->prompt_tokens = nullptr;
  this->prompt_len = 0;
  parse_prompt("../../../tests/end2end/input.prompt");
  this->seq_len = prompt_len + steps - 1;
  read_ref("../../../tests/end2end/ref.bin");
}

Llama2Test::~Llama2Test() {
  delete[] prompt;
  delete[] prompt_tokens;
#ifdef _WIN32
  UnmapViewOfFile(ref_addr);
#else
  if (munmap(ref_addr, ref_size) == -1) {
    logger.error("Couldn't munmap file");
  }
#endif
  close(ref_fd);
}

void Llama2Test::parse_prompt(const char *prompt_path) {
  std::ifstream file(prompt_path);
  if (!file.is_open()) {
    logger.error("Couldn't open file {}", prompt_path);
  }

  // Read the first line into prompt
  std::string line;
  if (std::getline(file, line)) {
    delete[] prompt;
    prompt = new char[strlen(line.c_str()) + 1];
    strcpy(prompt, line.c_str());

  } else {
    logger.error("Failed to read prompt from file {}", prompt_path);
  }

  // Read the second line into prompt_tokens
  if (std::getline(file, line)) {
    std::istringstream iss(line);
    std::vector<int> tokens;
    int token;
    while (iss >> token) {
      tokens.push_back(token);
    }
    prompt_len = tokens.size();
    delete[] prompt_tokens;
    prompt_tokens = new int[prompt_len];
    std::copy(tokens.begin(), tokens.end(), prompt_tokens);
  } else {
    logger.error("Failed to read prompt tokens from file {}", prompt_path);
  }
}

void Llama2Test::read_ref(const char *ref) {
  ref_fd = open(ref, O_RDONLY);
  if (ref_fd == -1) {
    logger.error("Couldn't open file {}", ref);
  }
  struct stat sb;
  if (fstat(ref_fd, &sb) == -1) {
    close(ref_fd);
    logger.error("Couldn't get file size");
  }
#ifdef _WIN32
  HANDLE hFile = CreateFile(ref, GENERIC_READ, FILE_SHARE_READ, NULL,
                            OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  if (hFile == INVALID_HANDLE_VALUE) {
    logger.error("CreateFile failed!");
  }
  HANDLE hMapping = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
  if (hMapping == NULL) {
    logger.error("CreateFileMapping failed!");
  }
  ref_addr = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
  if (ref_addr == NULL) {
    logger.error("MapViewOfFile failed!");
  }
  CloseHandle(hMapping);
  CloseHandle(hFile);
#else
  ref_addr = mmap(NULL, ref_size, PROT_READ, MAP_PRIVATE, ref_fd, 0);
  if (ref_addr == MAP_FAILED) {
    close(ref_fd);
    logger.error("Couldn't mmap file");
  }
#endif
  ref_size = sb.st_size;
  float *ref_data = (float *)ref_addr;
  tok_embeddings_res = ref_data;
  ref_data += seq_len * config_.dim;
  attn_out_res = std::make_shared<float *[]>(config_.n_layers);
  ffn_out_res = std::make_shared<float *[]>(config_.n_layers);
  for (int l = 0; l < config_.n_layers; l++) {
    attn_out_res[l] = ref_data;
    ref_data += seq_len * config_.dim;
    ffn_out_res[l] = ref_data;
    ref_data += seq_len * config_.dim;
  }
  final_rms_out_res = ref_data;
  ref_data += seq_len * config_.dim;
  logits_res = ref_data;
}

class Llama2Test_CPU_FP32 : public Llama2Test {
public:
  Llama2Test_CPU_FP32()
      : Llama2Test("../../../models/llama2/Llama-2-7b-fp32.model",
                   hllm::DeviceType::CPU) {}
  typedef float dtype_t;
};

class Llama2Test_CPU_FP16 : public Llama2Test {
public:
  Llama2Test_CPU_FP16()
      : Llama2Test("../../../models/llama2/Llama-2-7b-fp16.model",
                   hllm::DeviceType::CPU) {}
  typedef half_float::half dtype_t;
};

TEST_F(Llama2Test_CPU_FP32, GenerateTest_CPU_FP32) {
  bool eq;
  std::cout << prompt << std::flush;

  auto decode_and_print = [this](int next_tok) {
    auto *piece = tokenizer.decode(next_tok);
    std::cout << piece << std::flush;
  };

  /*
   * Prefill
   */
  prompt_embeddings = create_tensor(
      dtype_, {(size_t)prompt_len, (size_t)config_.dim}, hllm::ALLOC);
  attn_out_prefill = create_tensor(
      dtype_, {(size_t)prompt_len, (size_t)config_.dim}, hllm::ALLOC);

  for (int i = 0; i < prompt_len; i++) {
    memcpy((char *)prompt_embeddings.at(i, 0),
           (char *)token_embedding_table.at(prompt_tokens[i], 0),
           config_.dim * dtype_size(dtype_));
  }

#ifdef DEBUG_PREFILL
  EXPECT_TRUE(eq = array_eq((float *)prompt_embeddings.get_data(),
                            tok_embeddings_res, prompt_len * config_.dim));
  if (!eq) {
    std::cerr << "\033[31m" << "Prefill: tok_embedding mismatch" << "\033[0m"
              << std::endl;
  }
#endif

  for (int l = 0; l < config_.n_layers; l++) {
    attns[l]->prefill(prompt_embeddings, attn_out_prefill);

#ifdef DEBUG_PREFILL
    EXPECT_TRUE(eq = array_eq((float *)attn_out_prefill.get_data(),
                              attn_out_res[l], prompt_len * config_.dim));
    if (!eq) {
      std::cerr << "\033[31m" << "Prefill: attn_out mismatch at layer " << l
                << "\033[0m" << std::endl;
    }
#endif

#ifdef DEBUG_PREFILL
    ffns[l]->prefill(attn_out_prefill, prompt_embeddings);
    EXPECT_TRUE(eq = array_eq((float *)prompt_embeddings.get_data(),
                              ffn_out_res[l], prompt_len * config_.dim));
    if (!eq) {
      std::cerr << "\033[31m" << "Prefill: ffn_out mismatch at layer " << l
                << "\033[0m" << std::endl;
    }
#endif

  } // for l in n_layers

  // final RMSNorm (inplace)
  cpu_kernel->rmsnorm(prompt_embeddings, final_rms_weight, prompt_embeddings);

#ifdef DEBUG_PREFILL
  EXPECT_TRUE(eq = array_eq((float *)prompt_embeddings.get_data(),
                            final_rms_out_res, prompt_len * config_.dim));
  if (!eq) {
    std::cerr << "\033[31m" << "Prefill: final_rms_out mismatch" << "\033[0m"
              << std::endl;
  }
#endif

  // classifier into logits
  tok_embedding.copy_data(prompt_embeddings.at(prompt_len - 1, 0));
  cpu_kernel->mat_vec_mul(out_weight, tok_embedding, logits);

#ifdef DEBUG_PREFILL
  EXPECT_TRUE(eq = array_eq((float *)logits.get_data(),
                            logits_res + (prompt_len - 1) * config_.vocab_size,
                            config_.vocab_size));
  if (!eq) {
    std::cerr << "\033[31m" << "Prefill: logits mismatch" << "\033[0m"
              << std::endl;
  }
#endif

  int next_tok = sampler.sample(logits);
  decode_and_print(next_tok);
  /*
   * Decode
   */
  for (int pos = 0; pos < steps - 1 && pos < prompt_len + config_.max_seq_len;
       pos++) {
    tok_embedding.copy_data(token_embedding_table.at(next_tok, 0));

#ifdef DEBUG_DECODE
    EXPECT_TRUE(
        eq = array_eq((float *)tok_embedding.get_data(),
                      tok_embeddings_res + (prompt_len + pos) * config_.dim,
                      config_.dim));
    if (!eq) {
      std::cerr << "\033[31m" << "Decode: tok_embedding mismatch at position "
                << pos << "\033[0m" << std::endl;
    }
#endif

    for (int l = 0; l < config_.n_layers; l++) {
      attns[l]->decode(tok_embedding, attn_out_decode);

#ifdef DEBUG_DECODE
      EXPECT_TRUE(
          eq = array_eq((float *)attn_out_decode.get_data(),
                        attn_out_res[l] + (prompt_len + pos) * config_.dim,
                        config_.dim));
      if (!eq) {
        std::cerr << "\033[31m" << "Decode: attn_out mismatch at position "
                  << pos << ", layer " << l << "\033[0m" << std::endl;
      }
#endif

      ffns[l]->decode(attn_out_decode, tok_embedding);

#ifdef DEBUG_DECODE
      EXPECT_TRUE(
          eq = array_eq((float *)tok_embedding.get_data(),
                        ffn_out_res[l] + (prompt_len + pos) * config_.dim,
                        config_.dim));
      if (!eq) {
        std::cerr << "\033[31m" << "Decode: ffn_out mismatch at position "
                  << pos << ", layer " << l << "\033[0m" << std::endl;
      }
#endif

    } // for l in n_layers

    // final RMSNorm (inplace)
    cpu_kernel->rmsnorm(tok_embedding, final_rms_weight, tok_embedding);

#ifdef DEBUG_DECODE
    EXPECT_TRUE(
        eq = array_eq((float *)tok_embedding.get_data(),
                      final_rms_out_res + (prompt_len + pos) * config_.dim,
                      config_.dim));
    if (!eq) {
      std::cerr << "\033[31m" << "Decode: final_rms_out mismatch at position "
                << pos << "\033[0m" << std::endl;
    }
#endif

    // classifier into logits
    cpu_kernel->mat_vec_mul(out_weight, tok_embedding, logits);

#ifdef DEBUG_DECODE
    EXPECT_TRUE(
        eq = array_eq((float *)logits.get_data(),
                      logits_res + (prompt_len + pos) * config_.vocab_size,
                      config_.vocab_size));
    if (!eq) {
      std::cerr << "\033[31m" << "Decode: logits mismatch at position " << pos
                << "\033[0m" << std::endl;
    }
#endif

    next_tok = sampler.sample(logits);
    decode_and_print(next_tok);
  } // for pos in decode
  std::cout << std::endl;
}

// TEST_F(Llama2Test_CPU_FP16, GenerateTest_CPU_FP16) {
//   bool eq;
//   std::cout << prompt << std::flush;

//   auto decode_and_print = [this](int next_tok) {
//     auto *piece = tokenizer.decode(next_tok);
//     std::cout << piece << std::flush;
//   };

//   /*
//    * Prefill
//    */
//   prompt_embeddings = create_tensor(
//       dtype_, {(size_t)prompt_len, (size_t)config_.dim}, hllm::ALLOC);
//   attn_out_prefill = create_tensor(
//       dtype_, {(size_t)prompt_len, (size_t)config_.dim}, hllm::ALLOC);

//   for (int i = 0; i < prompt_len; i++) {
//     memcpy((char *)prompt_embeddings.at(i, 0),
//            (char *)token_embedding_table.at(prompt_tokens[i], 0),
//            config_.dim * dtype_size(dtype_));
//   }

// #ifdef DEBUG_PREFILL
//   EXPECT_TRUE(eq = array_eq((half_float::half *)prompt_embeddings.get_data(),
//                             tok_embeddings_res, prompt_len * config_.dim));
//   if (!eq) {
//     std::cerr << "\033[31m" << "Prefill: tok_embedding mismatch" << "\033[0m"
//               << std::endl;
//   }
// #endif

//   for (int l = 0; l < config_.n_layers; l++) {
//     attns[l]->prefill(prompt_embeddings, attn_out_prefill);

// #ifdef DEBUG_PREFILL
//     EXPECT_TRUE(eq = array_eq((half_float::half
//     *)attn_out_prefill.get_data(),
//                               attn_out_res[l], prompt_len * config_.dim,
//                               0.1));
//     if (!eq) {
//       std::cerr << "\033[31m" << "Prefill: attn_out mismatch at layer " << l
//                 << "\033[0m" << std::endl;
//     }
// #endif

// #ifdef DEBUG_PREFILL
//     ffns[l]->prefill(attn_out_prefill, prompt_embeddings);
//     // std::cout << attn_out_prefill << std::endl;
//     EXPECT_TRUE(eq = array_eq((half_float::half
//     *)prompt_embeddings.get_data(),
//                               ffn_out_res[l], prompt_len * config_.dim,
//                               0.1));
//     if (!eq) {
//       std::cerr << "\033[31m" << "Prefill: ffn_out mismatch at layer " << l
//                 << "\033[0m" << std::endl;
//     }
// #endif

//   } // for l in n_layers

//   // final RMSNorm (inplace)
//   cpu_kernel->rmsnorm(prompt_embeddings, final_rms_weight,
//   prompt_embeddings);

// #ifdef DEBUG_PREFILL
//   EXPECT_TRUE(eq = array_eq((half_float::half *)prompt_embeddings.get_data(),
//                             final_rms_out_res, prompt_len * config_.dim));
//   if (!eq) {
//     std::cerr << "\033[31m" << "Prefill: final_rms_out mismatch" << "\033[0m"
//               << std::endl;
//   }
// #endif

//   // classifier into logits
//   tok_embedding.copy_data(prompt_embeddings.at(prompt_len - 1, 0));
//   cpu_kernel->mat_vec_mul(out_weight, tok_embedding, logits);

// #ifdef DEBUG_PREFILL
//   EXPECT_TRUE(eq = array_eq((half_float::half *)logits.get_data(),
//                             logits_res + (prompt_len - 1) *
//                             config_.vocab_size, config_.vocab_size));
//   if (!eq) {
//     std::cerr << "\033[31m" << "Prefill: logits mismatch" << "\033[0m"
//               << std::endl;
//   }
// #endif

//   int next_tok = sampler.sample(logits);
//   decode_and_print(next_tok);
//   /*
//    * Decode
//    */
//   for (int pos = 0; pos < steps - 1 && pos < prompt_len +
//   config_.max_seq_len;
//        pos++) {
//     tok_embedding.copy_data(token_embedding_table.at(next_tok, 0));

// #ifdef DEBUG_DECODE
//     EXPECT_TRUE(
//         eq = array_eq((half_float::half *)tok_embedding.get_data(),
//                       tok_embeddings_res + (prompt_len + pos) * config_.dim,
//                       config_.dim));
//     if (!eq) {
//       std::cerr << "\033[31m" << "Decode: tok_embedding mismatch at position
//       "
//                 << pos << "\033[0m" << std::endl;
//     }
// #endif

//     for (int l = 0; l < config_.n_layers; l++) {
//       attns[l]->decode(tok_embedding, attn_out_decode);

// #ifdef DEBUG_DECODE
//       EXPECT_TRUE(
//           eq = array_eq((half_float::half *)attn_out_decode.get_data(),
//                         attn_out_res[l] + (prompt_len + pos) * config_.dim,
//                         config_.dim));
//       if (!eq) {
//         std::cerr << "\033[31m" << "Decode: attn_out mismatch at position "
//                   << pos << ", layer " << l << "\033[0m" << std::endl;
//       }
// #endif

//       ffns[l]->decode(attn_out_decode, tok_embedding);

// #ifdef DEBUG_DECODE
//       EXPECT_TRUE(
//           eq = array_eq((half_float::half *)tok_embedding.get_data(),
//                         ffn_out_res[l] + (prompt_len + pos) * config_.dim,
//                         config_.dim));
//       if (!eq) {
//         std::cerr << "\033[31m" << "Decode: ffn_out mismatch at position "
//                   << pos << ", layer " << l << "\033[0m" << std::endl;
//       }
// #endif

//     } // for l in n_layers

//     // final RMSNorm (inplace)
//     cpu_kernel->rmsnorm(tok_embedding, final_rms_weight, tok_embedding);

// #ifdef DEBUG_DECODE
//     EXPECT_TRUE(
//         eq = array_eq((half_float::half *)tok_embedding.get_data(),
//                       final_rms_out_res + (prompt_len + pos) * config_.dim,
//                       config_.dim));
//     if (!eq) {
//       std::cerr << "\033[31m" << "Decode: final_rms_out mismatch at position
//       "
//                 << pos << "\033[0m" << std::endl;
//     }
// #endif

//     // classifier into logits
//     cpu_kernel->mat_vec_mul(out_weight, tok_embedding, logits);

// #ifdef DEBUG_DECODE
//     EXPECT_TRUE(
//         eq = array_eq((half_float::half *)logits.get_data(),
//                       logits_res + (prompt_len + pos) * config_.vocab_size,
//                       config_.vocab_size));
//     if (!eq) {
//       std::cerr << "\033[31m" << "Decode: logits mismatch at position " <<
//       pos
//                 << "\033[0m" << std::endl;
//     }
// #endif

//     next_tok = sampler.sample(logits);
//     decode_and_print(next_tok);
//   } // for pos in decode
//   std::cout << std::endl;
// }