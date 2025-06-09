import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Load environment variables
load_dotenv(root_dir / ".env")

from sqlalchemy.orm import Session

from src.storage.db import get_db
from src.storage.models import AiProvider, AiProviderModel


def load_providers_data():
    json_path = root_dir / "tests" / "mock-data" / "ai-providers.json"
    with open(json_path, "r") as f:
        return json.load(f)


def upload_providers(db: Session, data: dict):
    for provider_data in data["providers"]:
        # Create provider
        provider = AiProvider(
            name=provider_data["name"],
            base_url=provider_data["base_url"],
            is_active=provider_data["is_active"]
        )
        db.add(provider)
        db.flush()  # Flush to get the provider ID

        # Create models for the provider
        for model_data in provider_data["models"]:
            model = AiProviderModel(
                name=model_data["name"],
                provider_id=provider.id,
                modalities=model_data["modalities"],
                is_active=model_data["is_active"],
                price_input_token=model_data["price_input_token"],
                price_output_token=model_data["price_output_token"],
                context_length=model_data["context_length"]
            )
            db.add(model)

    db.commit()


def main():
    # Debug: Print DATABASE_URL
    print(f"Database URL: {os.getenv('DATABASE_URL')}")
    
    # Load the JSON data
    data = load_providers_data()

    # Get database session
    db = next(get_db())

    try:
        # Upload the data
        upload_providers(db, data)
        print("Successfully uploaded AI providers data")
    except Exception as e:
        print(f"Error uploading data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main() 