from __future__ import annotations

import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from peft import PeftModel


def load_model_and_tokenizer() -> tuple[AutoModelForCausalLM, AutoTokenizer, str]:
    base_model_id = "microsoft/phi-3-mini-4k-instruct"
    adapters_dir = Path(__file__).resolve().parent / "phi3-powershell-adapters"

    # Device / dtype selection optimized for MacBook Air M4 (MPS)
    use_cuda = torch.cuda.is_available()
    use_mps = getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()
    device = "cuda" if use_cuda else ("mps" if use_mps else "cpu")

    if use_cuda and hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported():
        chosen_dtype = torch.bfloat16
    elif use_mps:
        chosen_dtype = torch.float16
    else:
        chosen_dtype = torch.float32

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Base model — avoid device_map on MPS to prevent CPU fallback; use eager attention
    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=chosen_dtype,
            low_cpu_mem_usage=True,
            attn_implementation="eager",
            trust_remote_code=True,
        )
    except Exception as exc:  # As a last resort, drop to float32
        print(f"[inference] Warning loading in {chosen_dtype}: {exc}. Falling back to float32.", file=sys.stderr)
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            attn_implementation="eager",
            trust_remote_code=True,
        )

    model = model.to(device)

    # Load PEFT adapter and merge into the base model for inference
    peft_wrapped = PeftModel.from_pretrained(model, str(adapters_dir))
    model = peft_wrapped.merge_and_unload()

    model.eval()
    # Disable KV cache to avoid DynamicCache API mismatches across transformers versions
    model.config.use_cache = False
    if getattr(model.config, "pad_token_id", None) is None:
        model.config.pad_token_id = tokenizer.pad_token_id

    return model, tokenizer, device


def build_phi3_prompt(instruction: str) -> str:
    # Phi-3 instruct chat format
    return f"<|user|>\n{instruction}<|end|>\n<|assistant|>\n"


def main() -> None:
    model, tokenizer, device = load_model_and_tokenizer()

    # Try to use Phi-3 specific end token if available
    end_token_id = tokenizer.convert_tokens_to_ids("<|end|>")
    if end_token_id == tokenizer.unk_token_id or end_token_id is None:
        end_token_id = tokenizer.eos_token_id

    print("Interactive Phi-3 (PEFT adapters merged, optimized for Apple Silicon). Type 'quit' to exit.\n")
    while True:
        try:
            instruction = input("Instruction> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if instruction.lower() in {"quit", "exit"}:
            break
        if not instruction:
            continue

        prompt = build_phi3_prompt(instruction)
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Stream tokens to avoid feeling "stuck" during generation on MPS
        streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        with torch.inference_mode():
            _ = model.generate(
                **inputs,
                max_new_tokens=80,
                do_sample=False,  # greedy for speed/stability on MPS
                eos_token_id=end_token_id,
                pad_token_id=tokenizer.pad_token_id,
                use_cache=False,
                streamer=streamer,
            )
        print("\n")


if __name__ == "__main__":
    main()


