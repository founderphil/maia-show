# backend/llm/convert.py
import os
import subprocess
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "meta-llama/Llama-3.2-1B"

# Load model and tokenizer from Hugging Face
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Save to local directory
model_save_path = "./llama3_hf_local"
model.save_pretrained(model_save_path)
tokenizer.save_pretrained(model_save_path)

# Convert the model to MLX format
subprocess.run([
    "mlx_lm.convert",
    "--hf-path", model_save_path,
    "--mlx-path", "./llama3_mlx"
])