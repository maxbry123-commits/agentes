from datasets import concatenate_datasets, disable_progress_bars

from dcft.data_strategies.OpenHermes.data_curation.source_dataset_info import (
    SOURCE_DATASET_INFO,
)
from dcft.data_strategies.OpenHermes.data_curation.source_labels import (
    load_source_prompts,
)

disable_progress_bars()

"""
Expected output:
---------------------------------------------
Dataset Name                        Prompts
---------------------------------------------
Airoboros 2.2                        44,838
CamelAI Biology                      20,000
CamelAI Chemistry                    20,000
CamelAI Math                         50,000
CamelAI Physics                      20,000
Chatbot Arena                        33,000
lmsys-1m                          1,000,000
Collective Cognition                    156
Evol Instruct 70K                    70,000
Evol Instruct 140K                  143,000
Glaive Code Assistant               136,109
GPT4-LLM                             54,568
GPTeacher                            89,260
MetaMath 40k                        395,000
SlimOrca 550K                       517,982
Platypus                             24,926
ShareGPT                             92,837
CogStack                              4,689
CoT Alpaca                           46,801
Unnatural Instructions               66,010
caseus_custom                         2,688
dataforge_economics                     880
---------------------------------------------
Total                             2,832,744
---------------------------------------------
"""

if __name__ == "__main__":
    all_source_prompts = []
    print("-" * 45)
    print(f"{'Dataset Name':<30} {'Prompts':>12}")
    print("-" * 45)

    for dataset_name in SOURCE_DATASET_INFO.keys():
        source_prompts = load_source_prompts(dataset_name, add_source=True)
        all_source_prompts.append(source_prompts)
        print(f"{dataset_name:<30} {len(source_prompts):>12,}")

    union_dataset = concatenate_datasets(all_source_prompts)
    print("-" * 45)
    print(f"{'Total':<30} {len(union_dataset):>12,}")
    print("-" * 45)
