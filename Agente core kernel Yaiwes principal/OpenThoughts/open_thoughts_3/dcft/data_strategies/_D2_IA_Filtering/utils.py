from datasets import Dataset


def k_shortest_verification(dataset: Dataset, response_column: str, verified_response_column: str, k: int) -> Dataset:
    def f(x):
        responses = x[response_column]
        sorted_responses = sorted(responses, key=len)
        k_shortest = sorted_responses[:k] if len(sorted_responses) >= k else sorted_responses
        x["_majority_responses"] = k_shortest
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)



def k_longest_verification(dataset: Dataset, response_column: str, verified_response_column: str, k: int) -> Dataset:
    def f(x):
        responses = x[response_column]
        sorted_responses = sorted(responses, key=len, reverse=True)
        k_longest = sorted_responses[:k] if len(sorted_responses) >= k else sorted_responses
        x["_majority_responses"] = k_longest
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)