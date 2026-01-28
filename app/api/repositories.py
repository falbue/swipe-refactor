from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select
from db.session import get_db
from schemas.repository import RepositoryCreate, RepositoryResponse
from models import Repository, RepositoryStatus
import git
from core import config


router = APIRouter()


@router.post(
    "/clone", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED
)
def clone_repository(repo: RepositoryCreate, db: Session = Depends(get_db)):
    owner = repo.repo_full_name.split("/")[0]
    repo_name = repo.repo_full_name.split("/")[1]
    repo_url = f"https://github.com/{owner}/{repo_name}.git"

    existing_repo = db.exec(
        select(Repository).where(Repository.repo_full_name == repo.repo_full_name)
    ).first()

    if existing_repo:
        git.Repo.pull(existing_repo.repo_full_name)
        return RepositoryResponse(
            message="Репозиторий уже существует, выполнено обновление"
        )

    new_repo = Repository(
        repo_full_name=repo.repo_full_name,
        branch_name="swipe-refactor",
        commit_name="Обновление для Swipe Refactor",
        status=RepositoryStatus.riddle,
        is_public_template=True,
    )

    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    try:
        git.Repo.clone_from(repo_url, config.TEMP_REPO_PATH + f"/{owner}/{repo_name}")
    except Exception as e:
        db.delete(new_repo)
        db.commit()
        return RepositoryResponse(message=f"Репозиторий не найден: {str(e)}")

    return RepositoryResponse(message="Клонирование успешно выполнено")
