import os
from huggingface_hub import snapshot_download
from src.config.configs import EMBEDDING_MODEL_NAME

def download_model():
    """
    Downloads the embedding model specified in src/config/configs.py
    and saves it to the setup/models directory for offline use.
    """
    local_dir = os.path.join("setup", "models", "embedding-model")
    
    print(f"🚀 Starting download of model: {EMBEDDING_MODEL_NAME}")
    print(f"📂 Destination: {local_dir}")
    
    try:
        snapshot_download(
            repo_id=EMBEDDING_MODEL_NAME,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ Successfully downloaded model to {local_dir}")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")

if __name__ == "__main__":
    # Ensure setup/models directory exists
    os.makedirs(os.path.join("setup", "models"), exist_ok=True)
    download_model()
