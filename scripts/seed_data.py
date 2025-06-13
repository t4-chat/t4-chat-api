#!/usr/bin/env python
import json
import asyncio
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.storage.models import AiProvider, AiProviderModel, Limits, UserGroup, User, UserGroupLimits
from src.storage.models.budget import Budget
from src.config import settings
from src.storage.database import db_session_manager


def load_seed_data(env: str, filename: str) -> Dict[str, Any]:
    """Load seed data from the specified environment directory."""
    json_path = root_dir / "seeds" / env / filename
    if not json_path.exists():
        print(f"Warning: Seed file {json_path} does not exist.")
        return {}
    
    with open(json_path, "r") as f:
        return json.load(f)


async def seed_providers(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up AI providers and their models idempotently."""
    print("Seeding AI providers...")
    data = load_seed_data(env, "ai-providers.json")
    if not data:
        return

    for provider_data in data.get("providers", []):
        # Check if provider already exists
        result = await db.execute(
            select(AiProvider).where(AiProvider.slug == provider_data["slug"])
        )
        existing_provider = result.scalar_one_or_none()

        if existing_provider:
            if update:
                # Update existing provider
                for key, value in provider_data.items():
                    if key != "models":
                        setattr(existing_provider, key, value)
                provider = existing_provider
                print(f"Updated provider: {provider.name}")
            else:
                provider = existing_provider
                print(f"Provider already exists: {provider.name}")
        else:
            # Create new provider without models first
            provider_dict = {k: v for k, v in provider_data.items() if k != "models"}
            provider = AiProvider(**provider_dict)
            db.add(provider)
            await db.flush()  # Flush to get the provider ID
            print(f"Created provider: {provider.name}")

        # Handle models for the provider
        for model_data in provider_data.get("models", []):
            model_slug = model_data["slug"]
            # Check if model already exists
            result = await db.execute(
                select(AiProviderModel).where(
                    AiProviderModel.slug == model_slug,
                    AiProviderModel.provider_id == provider.id
                )
            )
            existing_model = result.scalar_one_or_none()

            if existing_model:
                if update:
                    # Update existing model
                    for key, value in model_data.items():
                        setattr(existing_model, key, value)
                    print(f"Updated model: {existing_model.name}")
                else:
                    print(f"Model already exists: {existing_model.name}")
            else:
                # Create new model
                model = AiProviderModel(provider_id=provider.id, **model_data)
                db.add(model)
                print(f"Created model: {model.name}")

    print("AI providers seeding complete.")


async def seed_limits(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up limits idempotently."""
    print("Seeding limits...")
    data = load_seed_data(env, "limits.json")
    if not data:
        return

    for limit_data in data.get("limits", []):
        # Check if limit already exists for this model
        result = await db.execute(
            select(Limits).where(Limits.model_id == limit_data["model_id"])
        )
        existing_limit = result.scalar_one_or_none()

        if existing_limit:
            if update:
                # Update existing limit
                for key, value in limit_data.items():
                    setattr(existing_limit, key, value)
                print(f"Updated limit for model_id: {existing_limit.model_id}")
            else:
                print(f"Limit already exists for model_id: {existing_limit.model_id}")
        else:
            # Create new limit
            limit = Limits(**limit_data)
            db.add(limit)
            print(f"Created limit for model_id: {limit_data['model_id']}")

    print("Limits seeding complete.")


async def seed_user_groups(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up user groups idempotently."""
    print("Seeding user groups...")
    data = load_seed_data(env, "user-groups.json")
    if not data:
        return

    for group_data in data.get("groups", []):
        # Check if group already exists
        result = await db.execute(
            select(UserGroup).where(UserGroup.name == group_data["name"])
        )
        existing_group = result.scalar_one_or_none()

        if existing_group:
            if update:
                # Update existing group
                for key, value in group_data.items():
                    setattr(existing_group, key, value)
                print(f"Updated user group: {existing_group.name}")
            else:
                print(f"User group already exists: {existing_group.name}")
        else:
            # Create new group
            group = UserGroup(**group_data)
            db.add(group)
            print(f"Created user group: {group.name}")

    print("User groups seeding complete.")


async def seed_user_group_limits(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up user group limits idempotently."""
    print("Seeding user group limits...")
    data = load_seed_data(env, "user-group-limits.json")
    if not data:
        return

    for mapping in data.get("user_group_limits", []):
        user_group_name = mapping["user_group_name"]
        limit_model_ids = mapping["limit_model_ids"]

        # Get user group
        result = await db.execute(
            select(UserGroup).where(UserGroup.name == user_group_name)
        )
        user_group = result.scalar_one_or_none()
        if not user_group:
            print(f"Warning: User group '{user_group_name}' not found, skipping its limits")
            continue

        # Process each limit model ID
        for model_id in limit_model_ids:
            # Get limit for this model
            result = await db.execute(
                select(Limits).where(Limits.model_id == model_id)
            )
            limit = result.scalar_one_or_none()
            if not limit:
                print(f"Warning: Limit for model ID {model_id} not found, skipping")
                continue

            # Check if association already exists
            result = await db.execute(
                select(UserGroupLimits).where(
                    UserGroupLimits.user_group_name == user_group_name,
                    UserGroupLimits.limits_id == limit.id
                )
            )
            existing_association = result.scalar_one_or_none()

            if existing_association:
                print(f"Association between '{user_group_name}' and limit for model {model_id} already exists")
            else:
                # Create new association
                association = UserGroupLimits(
                    user_group_name=user_group_name,
                    limits_id=limit.id
                )
                db.add(association)
                print(f"Created association between '{user_group_name}' and limit for model {model_id}")

    print("User group limits seeding complete.")


async def seed_test_users(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up test users idempotently."""
    print("Seeding test users...")
    data = load_seed_data(env, "users.json")
    if not data:
        return

    for user_data in data.get("users", []):
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if update:
                # Update existing user
                for key, value in user_data.items():
                    setattr(existing_user, key, value)
                print(f"Updated user: {existing_user.email}")
            else:
                print(f"User already exists: {existing_user.email}")
        else:
            # Create new user
            user = User(**user_data)
            db.add(user)
            print(f"Created user: {user.email}")

    print("Test users seeding complete.")


async def seed_budget(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up budget idempotently."""
    print("Seeding budget...")
    data = load_seed_data(env, "budget.json")
    if not data:
        return

    result = await db.execute(select(Budget))
    existing_budget = result.scalar_one_or_none()
    
    if existing_budget:
        print("Budget already exists, skipping")
    else:
        budget = Budget(**data)
        db.add(budget)
    
    print("Budget seeding complete.")


async def main():
    parser = argparse.ArgumentParser(description="Seed database with initial data")
    parser.add_argument("--env", default="poc", help="Environment to seed from (e.g., dev, poc)")
    parser.add_argument("--update", action="store_true", help="Update existing records")
    args = parser.parse_args()

    env = args.env
    update = args.update

    print(f"Seeding database with data from {env} environment...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Update mode: {'enabled' if update else 'disabled'}")

    # Get database session
    async with db_session_manager.session() as db:
        try:
            # Run all seeding functions - order matters for dependencies
            await seed_providers(db, env, update)
            await seed_limits(db, env, update)
            await seed_user_groups(db, env, update)
            await seed_user_group_limits(db, env, update)
            await seed_test_users(db, env, update)
            await seed_budget(db, env, update)
            # Commit all changes
            await db.commit()
            print("Database seeding complete!")
        except Exception as e:
            print(f"Error seeding database: {e}")
            await db.rollback()
            raise
        finally:
            # Session is automatically closed by the async context manager in session
            pass


if __name__ == "__main__":
    asyncio.run(main()) 