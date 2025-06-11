import json
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID
from dotenv import load_dotenv

# Add root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.storage.db import get_db
from src.storage.models import AiProvider, AiProviderModel
from src.storage.models.user import User
from src.config import settings

def load_json_data(filename):
    """Load JSON data from the mock-data directory."""
    json_path = root_dir / "tests" / "mock-data" / filename
    with open(json_path, "r") as f:
        return json.load(f)


async def setup_providers(db: AsyncSession):
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
        await db.flush()  # Flush to get the provider ID

        # Create models for the provider
        for model_data in provider_data["models"]:
            model = AiProviderModel(
                provider_id=provider.id,
                **model_data
            )
            db.add(model)
    
    print("AI providers setup complete.")


async def setup_test_users(db: AsyncSession):
    """Set up test users for development."""
    print("Setting up test users...")
    
    # Create main test user with fixed UUID
    test_user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.id == test_user_id)
    )
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        test_user = User(
            id=test_user_id, 
            email="test@test.com", 
            first_name="Test", 
            last_name="User"
        )
        db.add(test_user)
        print(f"Created test user: {test_user.email}")
    else:
        print(f"Test user already exists: {existing_user.email}")
    
    # You can add more test users here as needed
    
    print("Test users setup complete.")


# Add more setup functions as needed
# async def setup_conversations(db: AsyncSession):
#     """Set up test conversations."""
#     pass


async def main():
    print("Setting up test environment...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Get database session
    async for db in get_db():
        try:
            # Run all setup functions
            await setup_providers(db)
            await setup_test_users(db)
            # Add more setup functions here as needed
            # await setup_conversations(db)
            
            # Commit all changes
            await db.commit()
            print("Test environment setup complete!")
        except Exception as e:
            print(f"Error setting up test environment: {e}")
            await db.rollback()
        finally:
            # Session is automatically closed by the async context manager in get_db
            pass


if __name__ == "__main__":
    asyncio.run(main()) 