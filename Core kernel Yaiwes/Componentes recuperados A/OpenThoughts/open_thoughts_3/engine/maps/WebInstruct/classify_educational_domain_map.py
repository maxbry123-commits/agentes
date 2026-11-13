import re

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class IsEducationalDomainResponse(BaseModel):
    is_education_domain: bool


class ClassifyEducationalDomainMapConfig(BaseModel):
    input_domain_column: str
    output_classification_column: str


CLASSIFY_EDUCATIONAL_DOMAIN_SYSTEM_PROMPT = """
You are tasked with filtering a list of domains to identify those most likely to contain educational content, specifically focusing on instruction materials such as exam problems, tutorials, or learning resources across various disciplines like math, science, and engineering.

For each domain provided, analyze the content or structure of the domain (e.g., keywords in the domain name, common subpages, and general website purpose) and classify it as either educational or non-educational. Prioritize domains that are likely to offer instructional data, exam problems, study guides, or teaching materials for educational purposes.

If a domain appears highly likely to belong to an academic institution, online learning platform, or a repository of educational resources, classify it as educational. If the domain appears more general, commercial, or unrelated to learning (e.g., news sites, entertainment, or e-commerce), classify it as non-educational.
"""


class ClassifyEducationalDomainMap(CompletionsMap):
    """
    A map that classifies whether a domain is an educational domain.
    """

    def __init__(self, config: dict):
        config = ClassifyEducationalDomainMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return IsEducationalDomainResponse

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """

        return [
            {"role": "system", "content": CLASSIFY_EDUCATIONAL_DOMAIN_SYSTEM_PROMPT},
            {"role": "user", "content": dataset_row[self.config.input_domain_column]},
        ]

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row[self.config.output_classification_column] = (
            response.is_education_domain
        )
        return original_dataset_row
