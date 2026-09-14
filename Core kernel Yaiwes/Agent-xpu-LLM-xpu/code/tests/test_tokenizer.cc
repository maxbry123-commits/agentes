#include "module/tokenizer.h"
#include <gtest/gtest.h>
#ifdef _WIN32
#define F_OK 0
#endif
using namespace hllm;

class TokenizerTest : public ::testing::Test {
protected:
  SentencePieceTokenizer *tokenizer;
  const char *vocab_path = "../../models/llama2/vocab.model";
};

TEST_F(TokenizerTest, LoadVocab) {
  if (access(vocab_path, F_OK) == -1) {
    FAIL() << "******[ERROR] Vocab file not found: " << vocab_path;
  }
  tokenizer = new SentencePieceTokenizer(vocab_path);
  EXPECT_EQ(tokenizer->get_vocab_size(), 32000);
  delete tokenizer;
}

TEST_F(TokenizerTest, Decode) {
  tokenizer = new SentencePieceTokenizer(vocab_path);
  EXPECT_STREQ(tokenizer->decode(0), "<unk>");
  EXPECT_STREQ(tokenizer->decode(1), "<s>");
  EXPECT_STREQ(tokenizer->decode(2), "</s>");
  EXPECT_STREQ(tokenizer->decode(277), "it");
  EXPECT_STREQ(tokenizer->decode(278), " the");
  EXPECT_STREQ(tokenizer->decode(1057), "::");
  EXPECT_STREQ(tokenizer->decode(25120), "Gre");
  delete tokenizer;
}
