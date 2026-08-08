import asyncio
import shutil
from pathlib import Path

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.dataset import Dataset
from app.models.project import Project
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository

DEMO_EMAIL = "demo@insightops.com"
DEMO_PASSWORD = "demo-password"
DEMO_PROJECT_NAME = "Demo Analytics Project"
DEMO_DATASET_NAME = "demo_orders.csv"

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_DATASET_PATH = PROJECT_ROOT / "sample_data" / "orders_valid.csv"

DEMO_DATASET_RELATIVE_PATH = Path("uploads") / "datasets" / DEMO_DATASET_NAME

DEMO_DATASET_ABSOLUTE_PATH = PROJECT_ROOT / DEMO_DATASET_RELATIVE_PATH


async def main() -> None:
    if not SAMPLE_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Sample dataset not found: {SAMPLE_DATASET_PATH}"
        )

    DEMO_DATASET_ABSOLUTE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    async with AsyncSessionLocal() as db:
        user_repo = UserRepository()
        project_repo = ProjectRepository()
        dataset_repo = DatasetRepository()

        user = await user_repo.get_by_email(db, DEMO_EMAIL)

        if user is None:
            user = await user_repo.create(
                db,
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
            )

        project_result = await db.execute(
            select(Project).where(
                Project.owner_id == user.id,
                Project.name == DEMO_PROJECT_NAME,
            )
        )
        project = project_result.scalar_one_or_none()

        if project is None:
            project = await project_repo.create(
                db,
                owner_id=user.id,
                name=DEMO_PROJECT_NAME,
                description="Demo project for InsightOps AI review.",
            )

        shutil.copyfile(
            SAMPLE_DATASET_PATH,
            DEMO_DATASET_ABSOLUTE_PATH,
        )

        dataset_result = await db.execute(
            select(Dataset).where(
                Dataset.project_id == project.id,
                Dataset.name == DEMO_DATASET_NAME,
            )
        )
        dataset = dataset_result.scalar_one_or_none()

        if dataset is None:
            dataset = await dataset_repo.create(
                db,
                name=DEMO_DATASET_NAME,
                file_path=DEMO_DATASET_RELATIVE_PATH.as_posix(),
                project_id=project.id,
            )

        print("Demo data is ready.")
        print(f"Email: {DEMO_EMAIL}")
        print(f"Password: {DEMO_PASSWORD}")
        print(f"Project ID: {project.id}")
        print(f"Dataset ID: {dataset.id}")
        print(f"Dataset path: {dataset.file_path}")


if __name__ == "__main__":
    asyncio.run(main())
