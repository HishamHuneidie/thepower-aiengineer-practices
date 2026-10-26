"""
    Finetune Qwen3 model with LoRA
"""

# imports

from dotenv import load_dotenv
import os
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer
from huggingface_hub import HfApi
from colorize import colorize

load_dotenv()

OPEN_MODEL_ID = os.environ.get('OPEN_MODEL_ID', 'Qwen/Qwen3-0.6B')
HF_REPO_ID = os.environ.get('HF_REPO_ID', None)
HF_TOKEN = os.environ.get('HF_TOKEN', None)
RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', './lora')
RESULTS_FINAL_FOLDER = os.environ.get('RESULTS_FINAL_FOLDER', './lora-final')

# load dataset for training, validation and test

dataset = load_dataset('csv', data_files='./assets/example_questions_responses.csv', split='train')

split = dataset.train_test_split(test_size=0.3, seed=42)
remaining = split['test'].train_test_split(test_size=0.50, seed=42)

train, validation, test = split['train'], remaining['train'], remaining['train']

# LoRA config and training

lora = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
)

config = SFTConfig(
    output_dir=RESULTS_FOLDER,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    learning_rate=1e-4,
    max_length=256,
    eos_token="<|im_end|>",
    eval_strategy="epoch",
)

# train

trainer = SFTTrainer(
    model=OPEN_MODEL_ID,
    train_dataset=train,
    eval_dataset=validation,
    peft_config=lora,
    args=config,
)

trainer.train()

result = trainer.evaluate(eval_dataset=test)

print()
print('result:')
print(f"Loss: {result['eval_loss']:.4f}")
print(f"Accuracy: {result['eval_mean_token_accuracy']:.2%}")
print(f"Evaluation time: {result['eval_runtime']:.2f}s")

# save model and publish

trainer.save_model(RESULTS_FINAL_FOLDER)

# publish to hub

if HF_REPO_ID and HF_TOKEN:
    hf_api = HfApi(token=HF_TOKEN)
    
    hf_api.create_repo(
        repo_id=HF_REPO_ID,
        private=True,
        exist_ok=True,
    )
    
    hf_api.upload_folder(
        folder_path=RESULTS_FINAL_FOLDER,
        repo_id=HF_REPO_ID,
    )
    
    print()
    print(colorize('HF Repo was uploaded', 'green'))
else:
    print()
    print(colorize(f'HF Repo could not be uploaded. {HF_REPO_ID} {HF_TOKEN}', 'red'))