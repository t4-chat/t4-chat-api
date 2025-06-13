import json
import asyncio
import sys
from pathlib import Path

# Add root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.storage.db import get_db
from src.storage.models import AiProvider, AiProviderModel, Limits, UserGroup
from src.config import settings


def load_json_data(filename):
    """Load JSON data from the mock-data directory."""
    json_path = root_dir / "tests" / "mock-data" / filename
    with open(json_path, "r") as f:
        return json.load(f)
    
async def setup_providers_models(db: AsyncSession, provider: AiProvider, models: list[dict]):
    for model_data in models:
        result = await db.execute(
            select(AiProviderModel).where(
                AiProviderModel.provider_id == provider.id,
                AiProviderModel.id == model_data["id"]
            )
        )
        model = result.scalars().first()
        
        if model:
            for key, value in model_data.items():
                setattr(model, key, value)
        else:
            model = AiProviderModel(provider_id=provider.id, **model_data)
            db.add(model)


async def setup_providers(db: AsyncSession):
    """Set up AI providers and their models."""
    print("Setting up AI providers...")
    data = load_json_data("ai-providers.json")

    for provider_data in data["providers"]:
        result = await db.execute(select(AiProvider).where(AiProvider.slug == provider_data["slug"]))
        provider = result.scalars().first()
        
        if provider:
            provider.name = provider_data["name"]
            provider.base_url = provider_data["base_url"]
            provider.is_active = provider_data["is_active"]
        else:
            provider = AiProvider(name=provider_data["name"], slug=provider_data["slug"], 
                                  base_url=provider_data["base_url"], is_active=provider_data["is_active"])
            db.add(provider)
            await db.flush()

        await setup_providers_models(db, provider, provider_data["models"])

    print("AI providers setup complete.")


async def setup_limits(db: AsyncSession):
    """Set up limits for the test users."""
    print("Setting up limits...")
    data = load_json_data("limits.json")

    for limit_data in data["limits"]:
        result = await db.execute(
            select(Limits).where(
                Limits.model_id == limit_data.get("model_id")
            )
        )
        limit = result.scalars().first()
        
        if limit:
            for key, value in limit_data.items():
                setattr(limit, key, value)
        else:
            limit = Limits(**limit_data)
            db.add(limit)

    print("Limits setup complete.")


async def setup_groups(db: AsyncSession):
    """Set up groups for the test users."""
    print("Setting up groups...")
    data = load_json_data("user-groups.json")

    for group_data in data["groups"]:
        result = await db.execute(select(UserGroup).where(UserGroup.name == group_data["name"]))
        group = result.scalars().first()
        
        if group:
            for key, value in group_data.items():
                setattr(group, key, value)
        else:
            group = UserGroup(**group_data)
            db.add(group)

    print("Groups setup complete.")


async def main():
    print("Setting up test environment...")
    print(f"Database URL: {settings.DATABASE_URL}")

    # Get database session
    async with get_db() as db:
        try:
            # Run all setup functions
            await setup_providers(db)
            await setup_limits(db)
            await setup_groups(db)

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
