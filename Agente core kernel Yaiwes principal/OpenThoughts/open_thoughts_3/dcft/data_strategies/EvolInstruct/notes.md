https://github.com/nlpxucan/WizardLM/tree/main/Evol_Instruct

These four files. 

(1) Load alpaca and combine input and instruction
(2) randomly choose one of the 4 methods to evolve the instruction via a prompt
(3) use the model to evolve the instruction
(4) use the model to annotate the evolved instruction

Not that they use top_p = 0.95, which is different from the default of 1.0