import os

from datasets import load_dataset

dataset = load_dataset("mlfoundations-dev/addition_pdf_flow", split="train")
dataset = dataset.select_columns(
    [
        "url",
        "page_number",
        "output_extraction",
        "extracted_question",
        "extracted_response",
        "improved_question",
        "page_bytes",
    ]
)
dataset.to_json(os.path.expanduser("~/Downloads/pdf_data.jsonl"))
