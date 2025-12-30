import csv
import json
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# --- CẤU HÌNH (CONFIG) ---
MODEL_CONFIG = {
    "model_name": "qwen/qwen3-4b-thinking-2507",  # Thay bằng model bạn muốn (vd: "ura-hcmut/ura-llama-7b")
    "input_csv": "questions_test (2).csv",
    "data_file": "fine_tuning_data.jsonl",
    "output_dir": "./fine_tuned_model",
    "num_train_epochs": 1,
    "batch_size": 4,
    "learning_rate": 2e-4,
    "max_seq_length": 512,
    "use_4bit": True,            # Kích hoạt 4-bit quantization
    "lora_r": 64,
    "lora_alpha": 16,
    "lora_dropout": 0.1
}

def convert_csv_to_jsonl(input_csv_path, output_jsonl_path):
    """
    Bước 1: Chuyển đổi file CSV sang định dạng JSONL (Chat Format)
    """
    if not os.path.exists(input_csv_path):
        print(f"❌ Lỗi: Không tìm thấy file CSV tại '{input_csv_path}'")
        return False

    print(f"🔄 Đang chuyển đổi dữ liệu từ {input_csv_path} sang {output_jsonl_path}...")
    data_buffer = []
    
    try:
        with open(input_csv_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            # Kiểm tra cột
            required_columns = ['Question', 'Keyword']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                print(f"❌ Lỗi: File CSV thiếu cột. Cần có: {required_columns}")
                return False

            for row in csv_reader:
                question = row['Question'].strip()
                keyword = row['Keyword'].strip()
                
                if not question or not keyword:
                    continue

                # Format dữ liệu theo chuẩn Chat (System - User - Assistant)
                training_example = {
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a keyword extraction expert. Extract important keywords from the user's question."
                        },
                        {
                            "role": "user", 
                            "content": question
                        },
                        {
                            "role": "assistant", 
                            "content": keyword
                        }
                    ]
                }
                data_buffer.append(training_example)

        # Ghi file JSONL
        with open(output_jsonl_path, mode='w', encoding='utf-8') as jsonl_file:
            for entry in data_buffer:
                json.dump(entry, jsonl_file, ensure_ascii=False)
                jsonl_file.write('\n')

        print(f"✅ Đã tạo file JSONL với {len(data_buffer)} mẫu dữ liệu.")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi xử lý CSV: {e}")
        return False

def run_fine_tuning(config):
    """
    Bước 2: Thực hiện Fine-tuning với QLoRA
    """
    model_name = config["model_name"]
    data_file = config["data_file"]
    output_dir = config["output_dir"]

    if not model_name:
        print("⚠️ Cảnh báo: Chưa cấu hình tên model.")
        return

    print(f"\n--- 🚀 BẮT ĐẦU FINE-TUNING: {model_name} ---")

    # 1. Cấu hình Quantization (4-bit)
    bnb_config = None
    if config["use_4bit"]:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=False,
        )

    # 2. Load Model & Tokenizer
    print("... Đang tải Model & Tokenizer ...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
    except Exception as e:
        print(f"❌ Lỗi tải model: {e}")
        return

    # 3. Cấu hình LoRA
    peft_config = LoraConfig(
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        r=config["lora_r"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 4. Load Dataset
    print(f"... Đang tải dataset từ {data_file} ...")
    try:
        dataset = load_dataset("json", data_files=data_file, split="train")
    except Exception as e:
        print(f"❌ Lỗi tải dataset: {e}")
        return

    # 5. Cấu hình Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config["num_train_epochs"],
        per_device_train_batch_size=config["batch_size"],
        gradient_accumulation_steps=1,
        learning_rate=config["learning_rate"],
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_32bit"
    )

    # 6. Khởi tạo Trainer
    print("... Khởi tạo SFTTrainer ...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="messages",
        max_seq_length=config["max_seq_length"],
        tokenizer=tokenizer,
        args=training_args,
    )

    # 7. Bắt đầu Train
    print("... Đang training ...")
    trainer.train()

    # 8. Lưu kết quả
    print(f"✅ Training hoàn tất. Lưu model tại {output_dir}")
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    # Bước 1: Chuyển đổi dữ liệu
    success = convert_csv_to_jsonl(MODEL_CONFIG["input_csv"], MODEL_CONFIG["data_file"])
    
    # Bước 2: Nếu chuyển đổi thành công, bắt đầu train
    if success:
        run_fine_tuning(MODEL_CONFIG)