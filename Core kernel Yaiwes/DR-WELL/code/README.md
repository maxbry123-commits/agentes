# DR. WELL

**Dynamic Reasoning and Learning with a Symbolic World Model for Embodied Multi-Agent Cooperation**

> **Heads up!** We are currently cleaning up this codebase to make it more polished and easier to work with. The system is fully functional, but some parts are still being reorganized and streamlined. Feel free to explore and experiment, keeping in mind that things are still evolving.

## Overview

This repository contains the implementation of **DR. WELL**, a decentralized neurosymbolic framework for studying and enabling **cooperative intelligence** in embodied multi-agent systems driven by LLMs.

DR. WELL is designed for settings where many agents must coordinate under embodied constraints, and where cooperation requires meaningful **individual cognitive abilities**, not just simple swarm-like rules. The framework integrates negotiation, symbolic planning, and dynamic world modeling to support scalable cooperation.

At each timestep, agents follow an iterative cycle:

- **Joint negotiation** to propose and agree on task allocation  
- **Individual planning** through primitive and symbolic spaces  
- **Execution** in the embodied environment  
- **Refinement** through feedback from a shared symbolic world model  

The symbolic world model simulates partial environment feedback, updates its internal representation based on joint outcomes, and helps agents improve their cooperative strategies over time without having to exchange full plans.

**DR. WELL Paper:**  
[*Dynamic Reasoning and Learning with Symbolic World Model for Embodied LLM-Based Multi-Agent Collaboration*](https://narjesno.github.io/DR.WELL/)

DR. WELL operates within the **CUBE** environment.  
Learn more at:  
[*CUBE: Collaborative Multi-Agent Block-Pushing Environment for Collective Planning with LLM Agents*](https://happyeureka.github.io/cube/)

## Citation

If you find this work useful, please cite:

```bibtex
@inproceedings{nourzad2025drwell,
  title     = {DR. WELL: Dynamic Reasoning and Learning with Symbolic World Model for Embodied LLM-Based Multi-Agent Collaboration},
  author    = {Nourzad, Narjes and Yang, Hanqing and Chen, Shiyu and Joe-Wong, Carlee},
  booktitle = {Workshop on Bridging Language, Agent, and World Models for Reasoning and Planning},
  year      = {2025}
}
```

If you like the environment, please also check out our CUBE paper:

```bibtex
@inproceedings{yangcube,
  title     = {CUBE: Collaborative Multi-Agent Block-Pushing Environment for Collective Planning with LLM Agents},
  author    = {Yang, Hanqing and Nourzad, Narjes and Chen, Shiyu and Joe-Wong, Carlee},
  booktitle = {Workshop on Scaling Environments for Agents},
  year      = {2025}
}
```
