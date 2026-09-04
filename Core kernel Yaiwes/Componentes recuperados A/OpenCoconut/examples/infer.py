import torch
from transformers import AutoTokenizer, TextStreamer
from opencoconut import AutoCoconutForCausalLM

def get_device():
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"

model_name = "coconut_output_stage3/checkpoint-10000"

tokenizer = AutoTokenizer.from_pretrained(model_name)
streamer = TextStreamer(tokenizer, skip_prompt=False, skip_special_tokens=False)

model = AutoCoconutForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.bfloat16, device_map=get_device()
)
model.tokenizer = tokenizer # only for debugging

prompt = "John cuts his grass to 2 inches. " \
         "It grows .5 inches per month. " \
         "When it gets to 4 inches he cuts it back down to 2 inches. " \
         "It cost $100 to get his grass cut. How much does he pay per year?"

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    do_sample=True,
    max_new_tokens=64,
    streamer=streamer,
    eos_token_id=tokenizer.eos_token_id,
)