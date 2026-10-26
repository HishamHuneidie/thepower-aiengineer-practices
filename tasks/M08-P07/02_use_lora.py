"""
    Use LoRA adapter
"""

# imports

import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from typing import Any, TypedDict
from colorize import colorize

load_dotenv()

OPEN_MODEL_ID = os.environ.get('OPEN_MODEL_ID', 'Qwen/Qwen3-0.6B')
HF_REPO_ID = os.environ.get('HF_REPO_ID', None)
HF_TOKEN = os.environ.get('HF_TOKEN', None)
RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', './lora')
RESULTS_FINAL_FOLDER = os.environ.get('RESULTS_FINAL_FOLDER', './lora-final')

class UserMessage(TypedDict):
    role: str
    content: str

# load model and tokenizer

model = AutoModelForCausalLM.from_pretrained(OPEN_MODEL_ID, device_map='auto')
tokenizer = AutoTokenizer.from_pretrained(OPEN_MODEL_ID)

model = PeftModel.from_pretrained(model, HF_REPO_ID or '')
#model = PeftModel.from_pretrained(model, RESULTS_FINAL_FOLDER)

model.eval()

# Generate method

def wrap_question(question: str) -> UserMessage:
    return {'role': 'user', 'content': question}

# TODO: Quitar el Any
def generate(question: str) -> Any:
    q = wrap_question(question)
    
    inputs = tokenizer.apply_chat_template(
        [q],
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors='pt',
    ).to(model.device)

    outputs = model.generate(
        input_ids=inputs["input_ids"],
        max_new_tokens=30,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    return tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[-1]:],
        skip_special_tokens=True,
    )

# Asking loop

INTRO = """

Pregunta algo como lo siguiente:
· ¿Venden móviles?
· ¿A que hora cierran?
· Puedo comprar online?

> """

while True:
    try:
        question = input(colorize(INTRO, 'gray'))
        
        if question == '':
            continue
        
        answer = generate(question)
        print(colorize(answer, 'green'))
    except:
        print(colorize('Bye bye', 'blue'))
        break
