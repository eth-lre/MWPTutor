# Scaling the Authoring of AutoTutors with Large Language Models (MWPTutor)

> **Abstract:** Large Language Models (LLMs) have found several use cases in education, ranging from automatic question generation to essay evaluation. In this paper, we explore the potential of using Large Language Models (LLMs) to author Intelligent Tutoring Systems. A common pitfall of LLMs is their straying from desired pedagogical strategies such as leaking the answer to the student, and in general, providing no guarantees. We posit that while LLMs with certain guardrails can take the place of subject experts, the overall pedagogical design still needs to be handcrafted for the best learning results. Based on this principle, we create a sample end-to-end tutoring system named MWPTutor, which uses LLMs to fill in the state space of a pre-defined finite state transducer. This approach retains the structure and the pedagogy of traditional tutoring systems that has been developed over the years by learning scientists but brings in additional flexibility of LLM-based approaches. Through a human evaluation study on two datasets based on math word problems, we show that our hybrid approach achieves a better overall tutoring score than an instructed, but otherwise free-form, GPT-4. MWPTutor is completely modular and opens up the scope for the community to improve its performance by improving individual modules or using different teaching strategies that it can follow 

For now [read the paper](https://arxiv.org/abs/2402.09216) and cite as:
```
@misc{chowdhury2024scaling,
      title={Scaling the Authoring of AutoTutors with Large Language Models}, 
      author={Sankalan Pal Chowdhury and Vilém Zouhar and Mrinmaya Sachan},
      year={2024},
      eprint={2402.09216},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

<img src="https://github.com/eth-lre/MWPTutor/assets/7661193/d660176d-233d-468e-b871-5443a524263c" width="400em">


## Running the code

TODO
