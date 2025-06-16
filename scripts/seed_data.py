import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.db import db_session_manager
from src.storage.models import (
    AiProvider,
    AiProviderModel,
    Limits,
    ModelHost,
    Usage,
    User,
    UserGroup,
    UserGroupLimits,
    WhiteList,
)
from src.storage.models.budget import Budget
from src.storage.models.model_host_association import ModelHostAssociation

from src.config import settings


def load_seed_data(env: str, filename: str) -> Dict[str, Any]:
    """Load seed data from the specified environment directory."""
    json_path = root_dir / "seeds" / env / filename
    if not json_path.exists():
        print(f"Warning: Seed file {json_path} does not exist.")
        return {}

    with open(json_path, "r") as f:
        return json.load(f)


async def handle_host(db: AsyncSession, host_data: Dict[str, Any], update: bool = False) -> ModelHost:
    """Process a host record and return the host object."""
    # Check if host already exists
    result = await db.execute(select(ModelHost).where(ModelHost.slug == host_data["slug"]))
    existing_host = result.scalar_one_or_none()

    if existing_host:
        if update:
            # Update existing host
            for key, value in host_data.items():
                setattr(existing_host, key, value)
            host = existing_host
            print(f"Updated host: {host.name}")
        else:
            host = existing_host
            print(f"Host already exists: {host.name}")
    else:
        # Create new host
        host = ModelHost(**host_data)
        db.add(host)
        await db.flush()  # Flush to get the host ID
        print(f"Created host: {host.name}")

    return host


async def handle_model(
    db: AsyncSession,
    model_data: Dict[str, Any],
    provider_id: UUID,
    update: bool = False
) -> None:
    """Process a model record."""
    model_slug = model_data["slug"]

    # Check if model already exists
    result = await db.execute(
        select(AiProviderModel).where(
            AiProviderModel.slug == model_slug,
            AiProviderModel.provider_id == provider_id,
        )
    )
    existing_model = result.scalar_one_or_none()

    # Remove hosts from model_data before creating/updating the model
    model_data_copy = {k: v for k, v in model_data.items() if k != "hosts"}

    # Create or update the model first
    if existing_model:
        if update:
            # Update existing model
            for key, value in model_data_copy.items():
                setattr(existing_model, key, value)
            model = existing_model
            print(f"Updated model: {model.name}")
        else:
            model = existing_model
            print(f"Model already exists: {model.name}")
    else:
        # Create new model
        model = AiProviderModel(provider_id=provider_id, **model_data_copy)
        db.add(model)
        await db.flush()  # Flush to get the model ID
        print(f"Created model: {model.name}")

    # Process hosts data and create associations
    if "hosts" in model_data and model_data["hosts"]:
        # Get existing host associations for this model
        result = await db.execute(
            select(ModelHostAssociation).where(ModelHostAssociation.model_id == model.id)
        )
        existing_associations = {assoc.host_id: assoc for assoc in result.scalars().all()}
        
        # Track processed host IDs to handle removals
        processed_host_ids = set()
        
        # Process each host with its priority
        for priority, host_data in enumerate(model_data["hosts"]):
            # Extract priority if specified, otherwise use the list order
            host_priority = host_data.pop("priority", priority)
            
            # Get or create the host
            host = await handle_host(db, host_data, update)
            processed_host_ids.add(host.id)
            
            # Check if association already exists
            if host.id in existing_associations:
                assoc = existing_associations[host.id]
                if update or assoc.priority != host_priority:
                    # Update priority if needed
                    assoc.priority = host_priority
                    print(f"Updated priority for host {host.name} to {host_priority}")
            else:
                # Create new association
                assoc = ModelHostAssociation(
                    model_id=model.id,
                    host_id=host.id,
                    priority=host_priority
                )
                db.add(assoc)
                print(f"Created association between model {model.name} and host {host.name} with priority {host_priority}")
        
        # Remove associations for hosts that are no longer associated with this model
        if update:
            for host_id, assoc in existing_associations.items():
                if host_id not in processed_host_ids:
                    await db.delete(assoc)
                    print(f"Removed association for host ID {host_id} from model {model.name}")


async def handle_provider(db: AsyncSession, provider_data: Dict[str, Any], update: bool = False) -> None:
    """Process a provider record and its associated models."""
    # Check if provider already exists
    result = await db.execute(select(AiProvider).where(AiProvider.slug == provider_data["slug"]))
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
        await handle_model(db, model_data, provider.id, update)


async def seed_providers(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up AI providers and their models idempotently."""
    print("Seeding AI providers...")
    data = load_seed_data(env, "ai-providers.json")
    if not data:
        return

    for provider_data in data.get("providers", []):
        await handle_provider(db, provider_data, update)

    print("AI providers seeding complete.")


async def seed_limits(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up limits idempotently."""
    print("Seeding limits...")
    data = load_seed_data(env, "limits.json")
    if not data:
        return

    for limit_data in data.get("limits", []):
        model_name = limit_data.pop("model_name", None)
        if not model_name:
            print(f"Warning: Model name not provided for limit, skipping")
            continue

        # Find the model by name
        result = await db.execute(select(AiProviderModel).where(AiProviderModel.name == model_name))
        model = result.scalar_one_or_none()
        if not model:
            print(f"Warning: Model with name '{model_name}' not found, skipping limit")
            continue

        # Add model_id to limit_data
        limit_data["model_id"] = model.id

        # Check if limit already exists for this model
        result = await db.execute(select(Limits).where(Limits.model_id == model.id))
        existing_limit = result.scalar_one_or_none()

        if existing_limit:
            if update:
                # Update existing limit
                for key, value in limit_data.items():
                    setattr(existing_limit, key, value)
                print(f"Updated limit for model: {model_name}")
            else:
                print(f"Limit already exists for model: {model_name}")
        else:
            # Create new limit
            limit = Limits(**limit_data)
            db.add(limit)
            print(f"Created limit for model: {model_name}")

    print("Limits seeding complete.")


async def seed_user_groups(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up user groups idempotently."""
    print("Seeding user groups...")
    data = load_seed_data(env, "user-groups.json")
    if not data:
        return

    for group_data in data.get("groups", []):
        # Check if group already exists
        result = await db.execute(select(UserGroup).where(UserGroup.name == group_data["name"]))
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
        limit_model_names = mapping["limit_model_names"]

        # Get user group
        result = await db.execute(select(UserGroup).where(UserGroup.name == user_group_name))
        user_group = result.scalar_one_or_none()
        if not user_group:
            print(f"Warning: User group '{user_group_name}' not found, skipping its limits")
            continue

        # Process each model name
        for model_name in limit_model_names:
            # Find the model by name
            result = await db.execute(select(AiProviderModel).where(AiProviderModel.name == model_name))
            model = result.scalar_one_or_none()
            if not model:
                print(f"Warning: Model with name '{model_name}' not found, skipping")
                continue

            # Get limit for this model
            result = await db.execute(select(Limits).where(Limits.model_id == model.id))
            limit = result.scalar_one_or_none()
            if not limit:
                print(f"Warning: Limit for model '{model_name}' not found, skipping")
                continue

            # Check if association already exists
            result = await db.execute(
                select(UserGroupLimits).where(
                    UserGroupLimits.user_group_id == user_group.id,
                    UserGroupLimits.limits_id == limit.id,
                )
            )
            existing_association = result.scalar_one_or_none()

            if existing_association:
                print(f"Association between '{user_group_name}' and limit for model '{model_name}' already exists")
            else:
                # Create new association
                association = UserGroupLimits(user_group_id=user_group.id, limits_id=limit.id)
                db.add(association)
                print(f"Created association between '{user_group_name}' and limit for model '{model_name}'")

    print("User group limits seeding complete.")


async def seed_test_users(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up test users idempotently."""
    print("Seeding test users...")
    data = load_seed_data(env, "users.json")
    if not data:
        return

    for user_data in data.get("users", []):
        # Get the group name from the user data and find the corresponding group
        group_name = user_data.pop("group_name", None)
        if group_name:
            # Find the group by name
            result = await db.execute(select(UserGroup).where(UserGroup.name == group_name))
            group = result.scalar_one_or_none()
            if not group:
                print(f"Warning: User group '{group_name}' not found for user {user_data['email']}, skipping")
                continue
            
            # Set the group_id field
            user_data["group_id"] = group.id

        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data["email"]))
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


async def seed_white_list(db: AsyncSession, env: str) -> None:
    print("Seeding white list...")
    data = load_seed_data(env, "white-list.json")
    if not data:
        return

    for email in data.get("emails", []):
        result = await db.execute(select(WhiteList).where(WhiteList.email == email))
        existing_item = result.scalar_one_or_none()

        if not existing_item:
            item = WhiteList(email=email)
            db.add(item)

    print("White list seeding complete.")


async def seed_usage(db: AsyncSession, env: str, update: bool = False) -> None:
    """Set up usage records idempotently."""
    print("Seeding usage data...")
    data = load_seed_data(env, "usage.json")
    if not data:
        return

    for usage_data in data.get("usage", []):
        email = usage_data.pop("email")
        model_name = usage_data.pop("model_name")
        date_str = usage_data.pop("date", None)

        # Find the user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Warning: User with email {email} not found, skipping usage record")
            continue

        # Find the model by name
        result = await db.execute(select(AiProviderModel).where(AiProviderModel.name == model_name))
        model = result.scalar_one_or_none()
        if not model:
            print(f"Warning: Model with name '{model_name}' not found, skipping usage record")
            continue

        # Calculate tokens
        prompt_tokens = usage_data.get("input_tokens", 0)
        completion_tokens = usage_data.get("output_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        # Parse date if provided
        usage_date = None
        if date_str:
            try:
                usage_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(f"Warning: Invalid date format {date_str}, using current time")

        # Check if usage record already exists for this user, model, and date
        query = select(Usage).where(
            Usage.user_id == user.id,
            Usage.model_id == model.id
        )

        if usage_date:
            query = query.where(Usage.created_at == usage_date)

        result = await db.execute(query)
        existing_usage = result.scalar_one_or_none()

        if existing_usage:
            if update:
                # Update existing usage record
                existing_usage.prompt_tokens = prompt_tokens
                existing_usage.completion_tokens = completion_tokens
                existing_usage.total_tokens = total_tokens
                print(f"Updated usage record for user {email} and model '{model_name}'")
            else:
                print(f"Usage record already exists for user {email} and model '{model_name}'")
        else:
            # Create new usage record
            usage = Usage(
                user_id=user.id,
                model_id=model.id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            # Set creation date if provided
            if usage_date:
                usage.created_at = usage_date
                usage.updated_at = usage_date

            db.add(usage)
            print(f"Created usage record for user {email} and model '{model_name}'")

    print("Usage data seeding complete.")


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
            await seed_white_list(db, env)
            await seed_usage(db, env, update)
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
