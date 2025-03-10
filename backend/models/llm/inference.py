# LLM inference code (Llama, GPT4All, etc.)
# backend/llm/inference.py
import subprocess
import re
from transformers import AutoTokenizer

def generate_response(prompt, max_tokens=128, adapter_path="./adapters", model_path="./llama3_mlx"):
    result = subprocess.run([
        "mlx_lm.generate",
        "--model", model_path,
        "--adapter-path", adapter_path,
        "--prompt", prompt,
        "--max-tokens", str(max_tokens)
    ], capture_output=True, text=True)
    
    output_text = result.stdout.strip()
    # Clean output text
    output_text = re.sub(r"=+", "", output_text)
    output_text = re.sub(r"^\s*MAIA:\s*", "", output_text)
    output_text = re.sub(r"User:.*", "", output_text, flags=re.DOTALL)
    output_text = re.sub(r"Querent:.*MAIA:", "", output_text, flags=re.DOTALL)
    output_text = re.sub(r"^\s*MAIA:\s*", "", output_text)
    return output_text.strip()

def test_tokenization():
    model_path = "./llama3_mlx"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    test_input = "<|im_start|>user\nWho created The Creators?<|im_end|>\n<|im_start|>assistant\n"
    tokens = tokenizer(test_input, return_tensors="pt")
    decoded_text = tokenizer.batch_decode(tokens["input_ids"], skip_special_tokens=False)
    print("Decoded Test Text:", decoded_text)

if __name__ == "__main__":
    test_tokenization()
    prompt = "Who created The Creators?"
    response = generate_response(prompt)
    print("Generated Response:", response)