import os
from fastapi import APIRouter, Depends, HTTPException, status
import requests
from sqlmodel import Session, select
from db.session import get_db
from models.repositories import (
    Repository,
    RepositoryStatus,
    RepositoryCreate,
    RepositoryResponse,
)
import git
from core.config import config
from core.parsers import scanner
from core.utils.logger import setup as setup_logger
from models import utcnow

logger = setup_logger(
    name="API-REPOSITORIES",
    log_path=config.LOG_PATH,
    DEBUG=config.LOG_DEBUG,
)


router = APIRouter(prefix="/repositories", tags=["repositories"])


def save_repository_to_db(
    repo_full_name: str,
    db: Session,
    branch: str = "swipe-refactor",
    commit: str = "Обновление {data}",
    status: RepositoryStatus = RepositoryStatus.riddle,
    is_public: bool = True,
) -> Repository | None:
    try:
        new_repo = Repository(
            repo_full_name=repo.repo_full_name,
            branch_name=branch,
            commit_name=commit,
            status=status,
            is_public_template=is_public,
        )

        db.add(new_repo)
        db.commit()
        db.refresh(new_repo)
        logger.info(f"Репозиторий {repo_full_name} сохранён в БД с id={new_repo.id}")
        return new_repo
    except Exception as e:
        logger.error(f"Ошибка при сохранении репозитория в БД: {e}")
        return None


def update_repo_data(existing_repo_db, repo_path, db: Session):
    existing_repo_db.updated_at = utcnow()
    db.add(existing_repo_db)
    db.commit()
    db.refresh(existing_repo_db)
    scanner.scan_repo(
        repo_path=repo_path,
        repository_id=existing_repo_db.id,
    )


@router.get("/", status_code=status.HTTP_200_OK)
def list_repositories(db: Session = Depends(get_db)):
    repositories = db.exec(select(Repository)).all()
    return repositories


@router.post(
    "/clone", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED
)
def clone_repository(repo: RepositoryCreate, db: Session = Depends(get_db)):
    owner = repo.repo_full_name.split("/")[0]
    repo_name = repo.repo_full_name.split("/")[1]
    repo_url = f"https://github.com/{owner}/{repo_name}"
    response = requests.head(repo_url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Репозиторий не найден: {repo_url} (HTTP {response.status_code})",
        )
    repo_path = config.TEMP_REPO_PATH + f"/{owner}/{repo_name}"

    existing_repo_db = db.exec(
        select(Repository).where(Repository.repo_full_name == repo.repo_full_name)
    ).first()

    if os.path.isdir(repo_path):
        repo_instance = git.Repo(repo_path)
        repo_instance.remotes.origin.pull()
        scanner.scan_repo(
            repo_path=repo_path,
            repository_id=existing_repo_db.id,
        )

        if existing_repo_db:
            update_repo_data(existing_repo_db, repo_path, db)
            return RepositoryResponse(
                message=f"Данные репозитория {repo.repo_full_name} обновлены в БД"
            )
        else:
            save_repository_to_db(repo_full_name=repo.repo_full_name, db=db)
    else:
        git.Repo.clone_from(repo_url, repo_path)
        logger.info(f"Репозиторий {repo.repo_full_name} успешно клонирован")
        if existing_repo_db:
            update_repo_data(existing_repo_db, repo_path, db)
    return RepositoryResponse(message="Клонирование успешно выполнено")
