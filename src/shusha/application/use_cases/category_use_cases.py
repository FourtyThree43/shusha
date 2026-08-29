"""
Category management and auto-classification use cases for Shusha 2.
"""

from dataclasses import dataclass

from shusha.domain.category import Category, CategoryRule
from shusha.domain.errors import DownloadNotFoundError
from shusha.domain.identifiers import CategoryId, DownloadId, make_category_id
from shusha.infrastructure.persistence.repositories.category_repository import (
    CategoryRepository,
)
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)


@dataclass(frozen=True, slots=True)
class CategoryDTO:
    name: str
    download_dir: str
    extensions: list[str]
    host_patterns: list[str]
    icon_name: str = "folder"
    id: str | None = None


class CreateCategoryUseCase:
    """Creates a new download category."""

    def __init__(self, category_repo: CategoryRepository) -> None:
        self.category_repo = category_repo

    def execute(self, dto: CategoryDTO) -> CategoryId:
        cat_id = make_category_id(dto.id or dto.name)
        rule = CategoryRule(extensions=dto.extensions, host_patterns=dto.host_patterns)
        cat = Category(
            id=cat_id,
            name=dto.name,
            download_dir=dto.download_dir,
            rule=rule,
            icon_name=dto.icon_name,
        )
        self.category_repo.save(cat)
        return cat_id


class UpdateCategoryUseCase:
    """Updates an existing category definition."""

    def __init__(self, category_repo: CategoryRepository) -> None:
        self.category_repo = category_repo

    def execute(self, category_id: CategoryId, dto: CategoryDTO) -> None:
        rule = CategoryRule(extensions=dto.extensions, host_patterns=dto.host_patterns)
        cat = Category(
            id=category_id,
            name=dto.name,
            download_dir=dto.download_dir,
            rule=rule,
            icon_name=dto.icon_name,
        )
        self.category_repo.save(cat)


class DeleteCategoryUseCase:
    """Deletes a category."""

    def __init__(self, category_repo: CategoryRepository) -> None:
        self.category_repo = category_repo

    def execute(self, category_id: CategoryId) -> bool:
        return self.category_repo.delete(category_id)


class AssignCategoryUseCase:
    """Assigns or changes the category on a specific download."""

    def __init__(
        self, download_repo: DownloadRepository, category_repo: CategoryRepository
    ) -> None:
        self.download_repo = download_repo
        self.category_repo = category_repo

    def execute(self, download_id: DownloadId, category_id: CategoryId | None) -> None:
        dl = self.download_repo.get_by_id(download_id)
        if not dl:
            raise DownloadNotFoundError(f"Download '{download_id}' not found")

        updated_dl = dl.assign_category(category_id)
        self.download_repo.save(updated_dl)
