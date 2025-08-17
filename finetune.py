from __future__ import annotations

import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer, SFTConfig


def main() -> None:
    # Model configuration
    model_id = "microsoft/phi-3-mini-4k-instruct"

    # Decide precision based on available hardware (Macs often use MPS with fp16)
    use_cuda = torch.cuda.is_available()
    use_mps = getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()
    bf16_supported = use_cuda and hasattr(torch.cuda, "is_bf16_supported") and torch.cuda.is_bf16_supported()

    if bf16_supported:
        chosen_dtype = torch.bfloat16
        training_precision = {"bf16": True, "fp16": False}
        precision_note = "Using bfloat16 on CUDA"
    elif use_mps:
        chosen_dtype = torch.float16
        # Transformers mixed-precision flags (fp16/bf16) are not supported on MPS. Keep them False.
        training_precision = {"bf16": False, "fp16": False}
        precision_note = "Using float16 weights on Apple MPS (no AMP)"
    else:
        chosen_dtype = torch.float32
        training_precision = {"bf16": False, "fp16": False}
        precision_note = "Using float32 on CPU"

    device = "cuda" if use_cuda else ("mps" if use_mps else "cpu")
    print(f"[finetune] {precision_note} | device={device}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Model (no 4-bit quantization on Mac). Avoid device_map to prevent meta/offload issues with Trainer.
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=chosen_dtype,
        low_cpu_mem_usage=False,
        attn_implementation="eager",
        trust_remote_code=True,
    )

    # Place the model explicitly
    model = model.to(device)

    # Disable KV cache during training to avoid DynamicCache API mismatches
    model.config.use_cache = False

    # Ensure pad token id is set
    if getattr(model.config, "pad_token_id", None) is None:
        model.config.pad_token_id = tokenizer.pad_token_id

    # LoRA configuration (QLoRA-style target modules, but without 4-bit quantization on Mac)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        task_type=TaskType.CAUSAL_LM,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "dense"],
        bias="none",
    )

    # Formatting function: format each example into the Phi-3 chat template
    def format_prompt(example: dict) -> str:
        # Formats a single example into the Phi-3 chat template
        return f"<|user|>\n{example['instruction']}<|end|>\n<|assistant|>\n{example['output']}"

    # Dataset: use the generated JSONL file at the repo root
    repo_root = Path(__file__).resolve().parent
    data_path = repo_root / "azure_powershell_dataset.jsonl"
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    # Load raw dataset and map to formatted text field
    raw_dataset = load_dataset("json", data_files=str(data_path), split="train")
    formatted_dataset = raw_dataset.map(lambda example: {"text": format_prompt(example)})

    # Training arguments
    output_dir = str(repo_root / "phi3-powershell-adapters")
    # Prefer no packing on Apple MPS to avoid attention impl issues
    packing_flag = False if use_mps else True

    sft_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=8,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="steps",
        save_steps=10,
        save_total_limit=3,
        bf16=training_precision["bf16"],
        fp16=training_precision["fp16"],
        report_to=[],
        push_to_hub=False,
        dataset_text_field="text",
        packing=packing_flag,
        dataloader_num_workers=0,
        max_steps=50,
    )

    # Trainer: supervise on the 'output' field as requested
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        peft_config=lora_config,
        train_dataset=formatted_dataset,
        args=sft_args,
    )

    # Train
    trainer.train()

    # Save final adapter model
    os.makedirs(output_dir, exist_ok=True)
    trainer.save_model(output_dir)
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)


if __name__ == "__main__":
    main()


