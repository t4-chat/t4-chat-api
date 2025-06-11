import json
import os
import sys
from pathlib import Path
from uuid import UUID
from dotenv import load_dotenv

# Add root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from sqlalchemy.orm import Session

from src.storage.db import get_db
from src.storage.models import AiProvider, AiProviderModel
from src.storage.models.user import User
from src.config import settings

def load_json_data(filename):
    """Load JSON data from the mock-data directory."""
    json_path = root_dir / "tests" / "mock-data" / filename
    with open(json_path, "r") as f:
        return json.load(f)


def setup_providers(db: Session):
    """Set up AI providers and their models."""
    print("Setting up AI providers...")
    data = load_json_data("ai-providers.json")
    
    for provider_data in data["providers"]:
        # Create provider
        provider = AiProvider(
            name=provider_data["name"],
            slug=provider_data["slug"],
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
                is_active=model_data["is_active"],
                price_input_token=model_data["price_input_token"],
                price_output_token=model_data["price_output_token"],
                context_length=model_data["context_length"]
            )
            db.add(model)
    
    print("AI providers setup complete.")


def setup_test_users(db: Session):
    """Set up test users for development."""
    print("Setting up test users...")
    
    # Create main test user with fixed UUID
    test_user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    test_user = User(
        id=test_user_id, 
        email="test@test.com", 
        first_name="Test", 
        last_name="User"
    )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.id == test_user_id).first()
    if not existing_user:
        db.add(test_user)
        print(f"Created test user: {test_user.email}")
    else:
        print(f"Test user already exists: {existing_user.email}")
    
    # You can add more test users here as needed
    
    print("Test users setup complete.")


# Add more setup functions as needed
# def setup_conversations(db: Session):
#     """Set up test conversations."""
#     pass


def main():
    print("Setting up test environment...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Get database session
    db = next(get_db())

    try:
        # Run all setup functions
        setup_providers(db)
        setup_test_users(db)
        # Add more setup functions here as needed
        # setup_conversations(db)
        
        # Commit all changes
        db.commit()
        print("Test environment setup complete!")
    except Exception as e:
        print(f"Error setting up test environment: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main() 