import copy
import re
import string
from collections import Counter, defaultdict
from itertools import combinations
from typing import Dict, List, Set

import nltk
import numpy as np
import torch
from datasets import Dataset, Sequence, Value
from fast_bleu import SelfBLEU
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from scipy.spatial import ConvexHull
from sklearn.cluster import KMeans
from torch import nn
from tqdm import tqdm
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer
from vendi_score import vendi

try:
    # Download required NLTK data if not present
    nltk.download("punkt_tab", quiet=True)
    nltk.download("stopwords", quiet=True)
except LookupError as e:
    raise LookupError(f"Failed to download NLTK data: {str(e)}")


def ForCausalLMLoss(
    logits,
    labels,
    vocab_size: int,
    num_items_in_batch: int = None,
    ignore_index: int = -100,
    **kwargs,
):
    # Upcast to float if we need to compute the loss to avoid potential precision issues
    logits = logits.float()
    # Shift so that tokens < n predict n
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()

    # Flatten the tokens
    shift_logits = shift_logits.view(-1, vocab_size)
    shift_labels = shift_labels.view(-1)
    # Enable model parallelism
    shift_labels = shift_labels.to(shift_logits.device)
    loss = fixed_cross_entropy(
        shift_logits, shift_labels, num_items_in_batch, ignore_index, **kwargs
    )
    return loss


def fixed_cross_entropy(
    source, target, num_items_in_batch: int = None, ignore_index: int = -100, **kwargs
):
    loss = nn.functional.cross_entropy(
        source, target, ignore_index=ignore_index, reduce=False
    )
    return loss


def convert_conversation_to_text(
    dataset: Dataset, format: str, conversation_column: str, output_column: str
) -> Dataset:
    if format == "openai":
        role_tag = "role"
        content_tag = "content"
        assistant_tag = "assistant"
    elif format == "sharegpt":
        role_tag = "from"
        content_tag = "value"
        assistant_tag = "gpt"

    def filter(row: Dict) -> Dict:
        for item in row[conversation_column]:
            if item[role_tag] == assistant_tag:
                row[output_column] = item[content_tag]
                return row

    dataset = dataset.map(filter)
    return dataset


def tokenize_text(text, remove_stopwords=False):
    """
    Splits text into words, removing punctuation and optionally stopwords.

    Args:
        text (str): Input text to tokenize
        remove_stopwords (bool): Whether to remove common stopwords

    Returns:
        list: List of cleaned tokens

    Raises:
        LookupError: If required NLTK data is not downloaded
    """
    # Tokenize text
    tokens = word_tokenize(text)

    # Remove punctuation
    tokens = [token.lower() for token in tokens if token not in string.punctuation]

    # Remove tokens that contain punctuation
    tokens = [token for token in tokens if not re.search(r"[^\w\s]", token)]

    # Optionally remove stopwords
    if remove_stopwords:
        stop_words = set(stopwords.words("english"))
        tokens = [token for token in tokens if token not in stop_words]

    return tokens


def self_bleu(dataset: Dataset, text_column: str) -> Dataset:
    try:
        # Download required NLTK data if not present
        nltk.download("punkt_tab")
    except LookupError as e:
        raise LookupError(f"Failed to download NLTK data: {str(e)}")
    all_strings = dataset[text_column]
    all_strings = [tokenize_text(string) for string in tqdm(all_strings)]
    weights = {"bigram": (1 / 2.0, 1 / 2.0), "trigram": (1 / 3.0, 1 / 3.0, 1 / 3.0)}
    self_bleu = SelfBLEU(all_strings, weights)
    all_scores = self_bleu.get_score()
    self_bleu = np.mean(all_scores["bigram"] + all_scores["trigram"])
    dataset = dataset.add_column("self_bleu", [self_bleu] * len(dataset))
    dataset = dataset.cast_column("self_bleu", Value("float64"))
    return dataset


def get_ngrams(text: str, n: int) -> List[str]:
    tokens = text.split()
    return [" ".join(gram) for gram in ngrams(tokens, n)]


def ngram_uniqueness(dataset: Dataset, text_column: str, n: int = 3) -> Dataset:
    all_ngrams = []
    total_ngrams = 0

    dataset.save_to_disk("ngram_uniqueness_dataset.json")

    for text in dataset[text_column]:
        text_ngrams = get_ngrams(text, n)
        all_ngrams.extend(text_ngrams)
        total_ngrams += len(text_ngrams)

    unique_ngrams = len(set(all_ngrams))
    uniqueness = unique_ngrams / total_ngrams if total_ngrams > 0 else 0
    dataset = dataset.add_column(f"ngram_{n}_uniqueness", [uniqueness] * len(dataset))
    dataset = dataset.cast_column(f"ngram_{n}_uniqueness", Value("float64"))
    return dataset


def entropy(dataset: Dataset, text_column: str) -> Dataset:
    all_words = []
    for text in dataset[text_column]:
        words = text.split()
        all_words.extend(words)

    word_counts = Counter(all_words)
    total_words = sum(word_counts.values())
    probabilities = [count / total_words for count in word_counts.values()]

    entropy_value = -sum(p * np.log2(p) for p in probabilities)
    dataset = dataset.add_column("entropy", [entropy_value] * len(dataset))
    dataset = dataset.cast_column("entropy", Value("float64"))
    return dataset


def kmeans_inertia(
    dataset: Dataset,
    vector_column_name: str,
    n_clusters: int = 5,
    output_name: str = "kmeans_inertia",
) -> Dataset:
    embeddings = dataset[vector_column_name]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(embeddings)
    inertia = kmeans.inertia_

    dataset = dataset.add_column(output_name, [inertia] * len(dataset))
    dataset = dataset.cast_column(output_name, Value("float64"))

    dataset = dataset.add_column(
        output_name + "_normalized", [inertia / len(embeddings)] * len(dataset)
    )
    dataset = dataset.cast_column(output_name + "_normalized", Value("float64"))

    return dataset


def d_lexsim(dataset: Dataset, text_column: str) -> Dataset:
    def fast_levenshtein(s1: str, s2: str, max_distance: float = float("inf")) -> int:
        """Optimized Levenshtein with early stopping based on maximum distance."""
        if len(s1) < len(s2):
            return fast_levenshtein(s2, s1, max_distance)

        if len(s2) == 0:
            return len(s1)

        # Early length-based optimization
        if abs(len(s1) - len(s2)) > max_distance:
            return max_distance + 1

        # Use smaller array
        current = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            prev = current
            current = [i + 1]
            for j, c2 in enumerate(s2):
                current.append(
                    min(
                        prev[j + 1] + 1, current[-1] + 1, prev[j] + (c1 != c2)
                    )  # deletion  # insertion  # substitution
                )

            # Early stopping if we exceed max_distance
            if min(current) > max_distance:
                return max_distance + 1

        return current[-1]

    def get_word_groups(words: Set[str], threshold: int = 3) -> Dict[str, List[str]]:
        """Group words by length to reduce comparison space."""
        length_groups = defaultdict(set)
        for word in words:
            word_len = len(word)
            # Group words that could be within threshold edit distance
            for length in range(max(0, word_len - threshold), word_len + threshold + 1):
                length_groups[length].add(word)
        return length_groups

    # Step 1: Collect unique words and their frequencies
    word_freq = defaultdict(int)
    for text in dataset[text_column]:
        for word in text.split():
            word_freq[word] += 1

    # Step 2: Filter out rare words (optional)
    min_freq = 2  # Adjust this threshold as needed
    all_words = {word for word, freq in word_freq.items() if freq >= min_freq}

    # Step 3: Group words by length
    length_groups = get_word_groups(all_words)

    # Step 4: Calculate distances more efficiently
    total_distance = 0
    word_pairs = 0
    max_distance_threshold = 0.8  # Adjust this threshold as needed

    # Process words in parallel within each length group
    for length, words in tqdm(length_groups.items()):
        # Use combinations to avoid redundant comparisons
        for w1, w2 in combinations(sorted(words), 2):
            max_len = max(len(w1), len(w2))
            if max_len > 0:
                # Calculate maximum allowed raw distance based on normalized threshold
                max_allowed_distance = int(max_len * max_distance_threshold)
                distance = fast_levenshtein(w1, w2, max_allowed_distance)

                # Only count if within threshold
                if distance <= max_allowed_distance:
                    normalized_distance = distance / max_len
                    total_distance += normalized_distance
                    word_pairs += 1

    d_lexsim = total_distance / word_pairs if word_pairs > 0 else 0

    # Use numpy for efficient column addition
    d_lexsim_column = np.full(len(dataset), d_lexsim)
    dataset = dataset.add_column("d_lexsim", d_lexsim_column)
    dataset = dataset.cast_column("d_lexsim", Value("float64"))

    return dataset


def gini_index(dataset: Dataset, text_column: str) -> Dataset:
    all_words = []
    for text in dataset[text_column]:
        words = text.split()
        all_words.extend(words)

    word_counts = Counter(all_words)
    total_words = sum(word_counts.values())
    probabilities = sorted([count / total_words for count in word_counts.values()])

    n = len(probabilities)
    if n == 0:
        gini = 0
    else:
        cumsum = np.cumsum(probabilities)
        gini = (n + 1 - 2 * np.sum((n + 1 - np.arange(1, n + 1)) * probabilities)) / (
            n * (n + 1)
        )

    dataset = dataset.add_column("gini_index", [gini] * len(dataset))
    dataset = dataset.cast_column("gini_index", Value("float64"))
    return dataset


def vendi_score(
    dataset: Dataset, vector_column_name: str, output_column: str
) -> Dataset:
    embeddings = dataset[vector_column_name]
    vendi_score = vendi.score_dual(np.asarray(embeddings))
    dataset = dataset.add_column(output_column, [vendi_score.item()] * len(dataset))
    dataset = dataset.cast_column(output_column, Value("float64"))
    return dataset


def optimized_preallocate(model):
    grads = torch.nn.utils.parameters_to_vector(
        [p.grad for p in model.parameters() if p.grad is not None]
    )
    grads = grads.expand(1, len(grads)).float()
    return grads


def calc_average_gradient(
    dataset: Dataset,
    conversation_column: str,
    projection_dimension: int = 8192,
    batch_size: int = 8,
    model_name="HuggingFaceTB/SmolLM2-135M-Instruct",
):
    # This import code needs to stay here since it's a prebuilt wheel
    # that only works on GPU. If we import it outside, driver CPU code will
    # try to import it and fail.
    import fast_jl

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="flash_attention_2",
    )
    tokenizer.pad_token = tokenizer.eos_token
    device = "cuda"
    all_results = []
    dataset_size = len(dataset[conversation_column])
    total_batches = (
        dataset_size + batch_size - 1
    ) // batch_size  # Ceiling division to include partial batch
    for param in model.parameters():
        param.requires_grad = True

    for batch_idx in tqdm(range(total_batches)):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, dataset_size)
        batch_texts = dataset[conversation_column][start_idx:end_idx]
        queue = []
        gradients = []
        non_trainable_queue = []

        for text in batch_texts:
            messages = tokenizer.apply_chat_template(text, tokenize=False)
            non_trainable_messages = tokenizer.apply_chat_template(
                text[:-1], tokenize=False
            )
            queue.append(messages)
            non_trainable_queue.append(non_trainable_messages)

        inputs = tokenizer(queue, padding="longest", return_tensors="pt").to(device)
        inputs["return_dict"] = True
        output = model(**inputs)
        labels = copy.deepcopy(inputs["input_ids"])

        for idx, messages in enumerate(non_trainable_queue):
            non_trainable_inputs = tokenizer(messages, return_tensors="pt")
            labels[idx, : len(non_trainable_inputs["input_ids"][0])] = -100

            loss_itm = torch.mean(
                ForCausalLMLoss(output.logits[idx], labels[idx], tokenizer.vocab_size)
            )
            loss_itm.backward(retain_graph=True)
            grad_vec = optimized_preallocate(model)
            grad_vec = grad_vec / torch.linalg.norm(grad_vec)
            gradients.append(grad_vec)
            model.zero_grad()
        all_results.append(
            fast_jl.project_rademacher_8(
                torch.stack(gradients).squeeze(1),
                projection_dimension,
                0,
                torch.cuda.get_device_properties(
                    model.device.index
                ).multi_processor_count,
            ).cpu()
            / np.sqrt(projection_dimension)
        )
    dataset = dataset.add_column(
        "projected_gradients", torch.cat(all_results).numpy().tolist()
    )
    dataset = dataset.cast_column("projected_gradients", Sequence(Value("float64")))
    return dataset


def calc_log_det(
    dataset: Dataset, vector_column_name: str, output_column: str
) -> Dataset:
    all_vectors = dataset[vector_column_name]
    matrix = np.stack(all_vectors)

    ATA = matrix.T @ matrix
    eigenvalues = np.linalg.eig(ATA)[0]
    volume = np.log(np.prod(eigenvalues))
    dataset = dataset.add_column(output_column, [volume.item()] * len(dataset))
    dataset = dataset.cast_column(output_column, Value("float64"))
    return dataset
