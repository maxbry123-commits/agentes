#pragma once
#include <stdexcept>

namespace hllm {
// Tokenizer translates token index -> string (decode)
// Note: encoding is preprocessed elsewhere in Python
class Tokenizer {
  public:
    Tokenizer(const char* vocab_path);
    virtual ~Tokenizer();

    virtual const char* decode(int tok_i) const = 0;

    char* get_token_str(int tok_i) const {
        check_token_index(tok_i);
        return vocab[tok_i];
    }
    int get_vocab_size() const { return vocab_size; }

    virtual bool is_end_of_text(int tok_i) const = 0;

    void check_token_index(int tok_i) const {
        if (tok_i < 0 || tok_i >= vocab_size) {
            std::throw_with_nested(std::runtime_error("token index out of bound"));
        }
        if (vocab == nullptr) {
            std::throw_with_nested(std::runtime_error("uninitialized vocab"));
        }
    }

  private:
    char** vocab = nullptr;
    int vocab_size = 0;
};

// LLama tokenizer (SentencePiece and TikToken)
// Used by Llama2 and Llama3 models
class LlamaTokenizer : public Tokenizer {
  public:
    LlamaTokenizer(const char* vocab_path);

    // return token str with given token index
    // return "\0" if the decoded token is not printable
    const char* decode(int tok_i) const override;
    bool is_end_of_text(int tok_i) const override;

  private:
    unsigned char byte_pieces[512]; // stores all single-byte strings
};

} // namespace hllm
