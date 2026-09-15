#include "tokenizer.h"

#include <cctype>
#include <cstring>

namespace hllm {

Tokenizer::Tokenizer(const char* vocab_path) {
    // read in the vocabulary file
    FILE* file = fopen(vocab_path, "rb");
    if (!file) {
        std::throw_with_nested(std::runtime_error("Failed to load vocabulary"));
    }
    if (fread(&vocab_size, sizeof(int), 1, file) != 1) {
        std::throw_with_nested(std::runtime_error("Failed to read vocabulary size"));
    }
    vocab = new char*[vocab_size];
    int tok_str_len;
    for (int i = 0; i < vocab_size; i++) {
        if (fread(&tok_str_len, sizeof(int), 1, file) != 1) {
            std::throw_with_nested(std::runtime_error("Failed to read token length at index"));
        }
        vocab[i] = new char[tok_str_len + 1];
        if (fread(vocab[i], tok_str_len, 1, file) != 1) {
            std::throw_with_nested(std::runtime_error("Failed to read token string at index"));
        }
        vocab[i][tok_str_len] = '\0'; // add the string terminating character
    }
    fclose(file);
}

Tokenizer::~Tokenizer() {
    for (int i = 0; i < vocab_size; i++) {
        delete[] vocab[i];
    }
    delete[] vocab;
}

LlamaTokenizer::LlamaTokenizer(const char* vocab_path) : Tokenizer(vocab_path) {
    for (int i = 0; i < 256; i++) {
        byte_pieces[i * 2] = (unsigned char)i;
        byte_pieces[i * 2 + 1] = '\0';
    }
}

bool LlamaTokenizer::is_end_of_text(int tok_i) const {
    char* piece = get_token_str(tok_i);
    return strcmp(piece, "<|eot_id|>") == 0 || strcmp(piece, "<|end_of_text|>") == 0;
}

const char* LlamaTokenizer::decode(int tok_i) const {
    char* piece = get_token_str(tok_i);
    // careful, some tokens designate raw bytes, and look like e.g. '<0x01>'
    // parse this and convert and return the actual byte
    unsigned char byte_val;
    if (sscanf(piece, "<0x%02hhX>", &byte_val) == 1) {
        piece = (char*)byte_pieces + byte_val * 2;
    }

    // piece might be a raw byte token, and we only want to print printable chars
    // or whitespace because some of the other bytes can be various control codes,
    // backspace, etc.
    if (piece == nullptr) {
        return "\0";
    }
    if (piece[0] == '\0') {
        return "\0";
    }
    if (piece[1] == '\0') {
        unsigned char byte_val = piece[0];
        if (!(isprint(byte_val) || isspace(byte_val))) {
            return "\0"; // bad byte, don't print it
        }
    }
    if (strcmp(piece, "<|begin_of_text|>") == 0 || strcmp(piece, "<|end_of_text|>") == 0) {
        return "\0";
    }
    return piece;
}
}; // namespace hllm
