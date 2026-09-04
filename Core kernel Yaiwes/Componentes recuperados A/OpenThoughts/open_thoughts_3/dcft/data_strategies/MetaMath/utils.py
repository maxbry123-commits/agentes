from datasets import Dataset


def fobar(dataset: Dataset):
    # Implement fobar method from the MetaMath paper
    # Example:
    # - Question: James buys X packs of beef that are 4 pounds each. The price of beef is $5.50 per pound.
    #   How much did he pay for the beef?
    # - Answer: $110
    # - New question: James buys X packs of beef that are 4 pounds each. The price of beef is $5.50 per pound.
    #   How much did he pay for the beef? If we know the answer to the above question is $100,
    #   what is the value of unknown variable X?
    def _fobar_map(row: dict) -> dict:
        row["inverse_question"] = (
            f"{row['inverse_question']} If we know the answer to the above question is {row['answer']}, what is the value of unknown variable X?"
        )
        row["method"] = "fobar"
        return row

    return dataset.map(_fobar_map)
