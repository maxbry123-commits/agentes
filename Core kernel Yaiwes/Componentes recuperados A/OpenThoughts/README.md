<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="images/open_thoughts.png" width="60%" alt="Open Thoughts GitHub Repository" />
</div>
<p align="center">
  <a href="https://open-thoughts.ai">
    <img alt="Static Badge" src="https://img.shields.io/badge/Home-open--thoughts.ai-blue?style=flat&link=https%3A%2F%2Fopen-thoughts.ai">
  </a>
  <a href="https://huggingface.co/open-thoughts">
    <img alt="Hugging Face" src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Open%20Thoughts-blue?color=ffc107&logoColor=white&style=flat&link=https%3A%2F%2Fhuggingface.co/open-thoughts">
  </a>
  <a href="https://discord.gg/9DsKjFtdXp">
    <img alt="Discord" src="https://img.shields.io/badge/Discord-Join%20Community-7289DA?style=flat&logo=discord&logoColor=white">
  </a>
  <br>
  <i>Curating the best open reasoning datasets</i><br> 
  A collaboration led by <a href="https://bespokelabs.ai/">Bespoke Labs</a> and the <a href="https://www.datacomp.ai/">DataComp</a> community

</p>
<hr>

Our first goal is to curate a reasoning dataset to train state-of-the-art small reasoning models that surpass [DeepSeek-R1-Distill-Qwen-32B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) and [DeepSeek-R1-Distill-Qwen-7B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B) on math and code reasoning benchmarks.


# News
- **[2025/06/10]** 🎉 [OpenThoughts3-1.2M dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M) is the #1 trending dataset on Hugging Face. 
- **[2025/06/04]** 🎉🎉🎉 We release our OpenThoughts [paper](https://arxiv.org/abs/2506.04178)!
- **[2025/06/04]** 🎉🎉🎉 [OpenThinker3](https://www.openthoughts.ai/blog/ot3) is released! 
- **[2025/05/09]** 🎉 Join our [Discord community](https://discord.gg/9DsKjFtdXp) to discuss OpenThoughts and connect with other users!
- **[2025/04/07]** 🎉 [OpenThoughts2-1M dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts2-1M) is the #1 trending dataset on Hugging Face.
- **[2025/04/03]** 🎉 [OpenThinker2](https://www.open-thoughts.ai/blog/thinkagain) has arrived: [OpenThoughts2-1M](https://huggingface.co/datasets/open-thoughts/OpenThoughts2-1M), [OpenThinker2-7B](https://huggingface.co/open-thoughts/OpenThinker2-7B), [OpenThinker2-32B](https://huggingface.co/open-thoughts/OpenThinker2-32B).
- **[2025/03/13]** 🎉 We release [an analysis of reasoning models](https://www.open-thoughts.ai/blog/aiw) on [Alice in Wonderland](https://github.com/LAION-AI/AIW).
- **[2025/02/16]** 🎉 [OpenThinker on Ollama](https://ollama.com/library/openthinker) reaches 400k downloads.
- **[2025/02/14]** 🎉 Chat with OpenThinker in the [online playground](https://playground.bespokelabs.ai/).
- **[2025/02/13]** 🎉 OpenThinker is now [available on Ollama](https://ollama.com/library/openthinker) for easy local inference.
- **[2025/02/12]** 🎉 We release [OpenThinker-32B](https://huggingface.co/open-thoughts/OpenThinker-32B), the [best open-data reasoning model](https://www.open-thoughts.ai/blog/scale).
- **[2025/02/02]** 🎉 [OpenThoughts-114k dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) is the #1 trending dataset on Hugging Face.
- **[2025/01/30]** 🎉 Reasoning benchmarks are added to [Evalchemy](https://github.com/mlfoundations/Evalchemy) and [compared](https://www.open-thoughts.ai/blog/measure) to publicly reported scores.
- **[2025/01/28]** 🎉 [Open Thoughts](https://www.open-thoughts.ai/) launches with [OpenThoughts-114k dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) and [OpenThinker-7B model](https://huggingface.co/open-thoughts/OpenThinker-7B).
- **[2025/01/27]** 🎉 [Bespoke-Stratos-17k dataset](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k) is the #2 trending dataset on Hugging Face.
- **[2025/01/22]** 🎉 [Bespoke-Stratos-17k dataset](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k) and [Bespoke-Stratos-32B model](https://huggingface.co/bespokelabs/Bespoke-Stratos-32B) are [announced](https://www.bespokelabs.ai/blog/bespoke-stratos-the-unreasonable-effectiveness-of-reasoning-distillation).

# Results
Our [OpenThinker3-7B](https://huggingface.co/open-thoughts/OpenThinker3-7B) model trained on [OpenThoughts3-1.2M](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M) is the state-of-the-art open-data 7B reasoning model.
The numbers reported in the table below are evaluated with our open-source tool [Evalchemy](https://github.com/mlfoundations/Evalchemy).

| Model                                                                                           | Data  | AIME24 | AIME25 |  AMC23 | MATH500 | HMMT O2/25 | LCB 06/24-01/25 | CodeElo | CodeForces | GPQA-D | JEEBench |
| ----------------------------------------------------------------------------------------------- | ----- | ------ | ------ | ------ | ------- | ---------- | --------------- | ------- | ---------- | ------ | -------- |
| [OpenThinker-7B](https://huggingface.co/open-thoughts/OpenThinker-7B)                           | ✅    |  30.7  |  22.0  |  72.5  |   82.8  |   15.7     |    26.1         |  11.1   |  14.9      |  38.6  |  45.3    |
| [OpenThinker2-7B](https://huggingface.co/open-thoughts/OpenThinker2-7B)                         | ✅    |  60.7  |  38.7  |  89.8  |   87.6  |   24.7     |    40.6         |  22.8   |  26.6      |  47.0  |  65.1    |
| **[OpenThinker3-7B](https://huggingface.co/open-thoughts/OpenThinker3-7B)**                     | ✅    |**69.0**|**53.3**|**93.5**| **90.0**|   **42.7** |    **51.7**     |  31.0   |**32.2**    |  53.7  |**72.4**  |
| [DeepSeek-R1-Distill-Qwen-32B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) | ❌    |  51.3  |  38.0  |  92.0  |   88.0  |   25.0     |    34.5         |  19.9   |  21.1      |  33.2  |  50.4    |
| [OpenR1-Distill-7B](https://huggingface.co/open-r1/OpenR1-Distill-7B)                           | ✅    |  57.7  |  39.7  |  87.0  |   88.0  |   25.7     |    30.7         |  30.1   |  29.3      |**58.9**|  68.7    |
| [Llama-3.1-Nemotron-Nano-8B-v1](https://huggingface.co/nvidia/Llama-3.1-Nemotron-Nano-8B-v1)    | ✅    |  62.0  |  48.0  |**94.0**|   89.4  |   26.7     |    **50.9**     |  30.9   |**32.9**    |  52.9  |  70.7    |
| [AceReason-Nemotron-7B](https://huggingface.co/nvidia/AceReason-Nemotron-7B)                    | ✅    |**71.0**|  50.7  |**93.8**|   89.8  |   33.3     |    44.3         |**32.9** |**30.9**    |  52.9  |  64.3    |


To mitigate variance in evaluation accuracy, we compute average scores over multiple evaluation runs with different seeds. More details can be found in our OpenThoughts [paper](https://arxiv.org/abs/2506.04178).


We are fully open-source. Our [model weights](https://huggingface.co/open-thoughts), [datasets](https://huggingface.co/open-thoughts), [data generation code](https://github.com/open-thoughts/open-thoughts), [evaluation code](https://github.com/mlfoundations/Evalchemy), and [training code](https://github.com/hiyouga/LLaMA-Factory) are all publicly available. 

# Installation
```
make install
poetry shell
```
Set the DeepSeek API key:
```
export DEEPSEEK_API_KEY=your_api_key
```

Set HF_ORG to your organization id. Set HF_PRIVATE=true if you want to push to a private repo.
```
export HF_ORG=your_org_id
export HF_PRIVATE=false
```
# OpenThoughts3-1.2M Data Generation
The [OpenThoughts3-1.2M](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M) dataset consists of 850,000 math questions, 250,000 code questions, and 100,000 science questions. As opposed to previous OpenThoughts models that used R1 annotations, OpenThoughts3's reasoning traces are generated with QwQ-32B. This dataset is the result of 1000+ experiments to test out various design choices involved in dataset curation. More details can be found in our [OpenThoughts paper](https://arxiv.org/abs/2506.04178). 

<picture>
    <source media="(prefers-color-scheme: light)" width="100%" srcset="images/openthoughts3-diagram.png">
    <img alt="Data Curation Recipe" width="100%" src="images/openthoughts3-diagram_dark.png">
</picture>


# OpenThoughts2-1M Data Generation
The [OpenThoughts2-1M](https://huggingface.co/datasets/open-thoughts/OpenThoughts2-1M) dataset is a combination of [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k), [OpenR1-Math](https://huggingface.co/datasets/open-r1/OpenR1-Math-Raw), and our newly generated math and code reasoning data. We generate the additional math and code data by ablating on 26 different question generation methodologies and sampling from the highest performing ones.

The recipe is outlined below:
<picture>
    <source media="(prefers-color-scheme: light)" width="100%" srcset="images/openthoughts2-diagram.png">
    <img alt="Data Curation Recipe" width="100%" src="images/openthoughts2-diagram_dark.png">
</picture>

More details can be found in our [blog post](https://www.open-thoughts.ai/blog/thinkagain). 


# OpenThoughts-114k Data Generation

For OpenThoughts-114k, we generate data for the following domains:
1. Code
2. Math
3. Science
4. Puzzle

The recipe is outlined below:
<picture>
    <source media="(prefers-color-scheme: light)" width="100%" srcset="images/diagram.png">
    <img alt="Data Curation Recipe" width="100%" src="images/diagram_dark.png">
</picture>

More instructions are in [open_thoughts/README.md](open_thoughts/README.md).


# Training and Evaluation
Training and evaluation code coming soon.

# Links
- 📝 [OpenThoughts Paper](https://arxiv.org/abs/2506.04178)
- 📊 [OpenThoughts3-1.2M and OpenThinker3-7B Blog Post](https://www.open-thoughts.ai/blog/ot3)
- 💻 [Open Thoughts GitHub Repository](https://github.com/open-thoughts/open-thoughts)
- 🧠 [OpenThoughts3-1.2M dataset](https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M)
- 🤖 [OpenThinker3-7B model](https://huggingface.co/open-thoughts/OpenThinker3-7B)


# About Us

We are a team of researchers and engineers from [Bespoke Labs](https://www.bespokelabs.ai/), Stanford, University of California Berkeley, University of Washington, UT Austin, Juelich Supercomputing Center (JSC), LAION, UCLA, UNC Chapel Hill, UT Austin, and Toyota Research Institute united around building the best datasets (and thus the best models). See our previous works at [datacomp.ai](https://www.datacomp.ai/) and [mlfoundations](https://github.com/mlfoundations).

# Sponsors
Open Thoughts is supported by 
- [Bespoke Labs](https://www.bespokelabs.ai/)
- [Toyota Research Institute](https://www.tri.global)
- [Lambda Labs](https://lambdalabs.com/)
- [NSF IFML](https://www.ifml.institute/)
- [UT Austin Machine Learning Lab](https://ml.utexas.edu/)
- [Juelich Supercomputing Center](https://www.fz-juelich.de/en/ias/jsc)


# Community
[Make an edit](https://github.com/open-thoughts/open-thoughts/edit/main/README.md) to add your project!

Join our [Discord community](https://discord.gg/9DsKjFtdXp) to discuss OpenThoughts and connect with other users!

What the open source community is building with OpenThoughts:

- [Light-R1-SFT](https://huggingface.co/datasets/qihoo360/Light-R1-SFTData) includes examples from [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) and is used to train [Light-R1-14B-DS](https://huggingface.co/qihoo360/Light-R1-14B-DS), [Light-R1-32B](https://huggingface.co/qihoo360/Light-R1-32B), [Light-R1-7B-DS](https://huggingface.co/qihoo360/Light-R1-7B-DS), [Light-R1-32B-DS](https://huggingface.co/qihoo360/Light-R1-32B-DS)
- [Traceback-12B](https://huggingface.co/secemp9/TraceBack-12b) is a reasoning model trained on a [dataset](https://huggingface.co/datasets/secemp9/instruction_solution_thought) that includes [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) and [Bespoke-Stratos-17k](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k)
- [190+ public models on Hugging Face](https://huggingface.co/models?dataset=dataset:open-thoughts/OpenThoughts-114k) have been trained using [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k)
- [100+ public models on Hugging Face](https://huggingface.co/models?dataset=dataset:bespokelabs/Bespoke-Stratos-17k) have been trained using [Bespoke-Stratos-17k](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k)
- [Sky-T1](https://arxiv.org/abs/2502.07374) uses [Bespoke-Stratos-17k](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k) for their R1 SFT experiments
- Ollama has [created quantized versions](https://ollama.com/library/openthinker) of the OpenThinker-7B and OpenThinker-32B models, for running locally on your laptop
- [CuratedThoughts](https://huggingface.co/datasets/bethgelab/CuratedThoughts) is a filtered version of [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) to make it suitable for RL training
- [OpenThoughts-114k-math](https://huggingface.co/datasets/open-r1/OpenThoughts-114k-math) is a filtered version of the math subset in [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) using [Math-Verify](https://github.com/huggingface/Math-Verify) verification on top of our LLM Judge with GT verification
- [SmallThoughts](https://huggingface.co/datasets/SmallDoge/SmallThoughts) regenerates a 50k version of [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) using a [fork](https://github.com/SmallDoges/small-thoughts) of this repo
- [AM-DeepSeek-R1-Distilled-1.4M](https://huggingface.co/datasets/a-m-team/AM-DeepSeek-R1-Distilled-1.4M) is a state of the art reasoning dataset mix containing [OpenThoughts-114k](https://huggingface.co/datasets/open-thoughts/OpenThoughts-114k) and [Bespoke-Stratos-17k](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k)
- [Marin 8B](https://huggingface.co/marin-community/marin-8b-instruct) of the Stanford Marin Project, a collaborative effort to develop open-source foundation models, is trained on [Bespoke-Stratos-17k](https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k).


# Citation
```
@misc{guha2025openthoughtsdatarecipesreasoning,
  title={OpenThoughts: Data Recipes for Reasoning Models}, 
  author={Etash Guha and Ryan Marten and Sedrick Keh and Negin Raoof and Georgios Smyrnis and Hritik Bansal and Marianna Nezhurina and Jean Mercat and Trung Vu and Zayne Sprague and Ashima Suvarna and Benjamin Feuer and Liangyu Chen and Zaid Khan and Eric Frankel and Sachin Grover and Caroline Choi and Niklas Muennighoff and Shiye Su and Wanjia Zhao and John Yang and Shreyas Pimpalgaonkar and Kartik Sharma and Charlie Cheng-Jie Ji and Yichuan Deng and Sarah Pratt and Vivek Ramanujan and Jon Saad-Falcon and Jeffrey Li and Achal Dave and Alon Albalak and Kushal Arora and Blake Wulfe and Chinmay Hegde and Greg Durrett and Sewoong Oh and Mohit Bansal and Saadia Gabriel and Aditya Grover and Kai-Wei Chang and Vaishaal Shankar and Aaron Gokaslan and Mike A. Merrill and Tatsunori Hashimoto and Yejin Choi and Jenia Jitsev and Reinhard Heckel and Maheswaran Sathiamoorthy and Alexandros G. Dimakis and Ludwig Schmidt},
  year={2025},
  eprint={2506.04178},
  archivePrefix={arXiv},
  primaryClass={cs.LG},
  url={https://arxiv.org/abs/2506.04178}, 
}
```
