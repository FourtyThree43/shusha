"""
Download category and automatic classification rules in Shusha 2.
"""

from dataclasses import dataclass
from pathlib import PurePath

from shusha.domain.identifiers import CategoryId


@dataclass(frozen=True, slots=True)
class CategoryRule:
    """Pattern matching rule for automatic category assignment."""

    extensions: list[str]
    host_patterns: list[str]
    regex_pattern: str | None = None

    def matches(self, filename: str, url: str) -> bool:
        """Evaluate whether a download matches this category's rules."""
        # 1. Extension matching
        if self.extensions:
            ext = PurePath(filename).suffix.lstrip(".").lower()
            if ext in [e.lstrip(".").lower() for e in self.extensions]:
                return True

        # 2. Host pattern matching
        if self.host_patterns:
            url_lower = url.lower()
            for pat in self.host_patterns:
                if pat.lower() in url_lower:
                    return True

        return False


@dataclass(frozen=True, slots=True)
class Category:
    """Category entity with default destination directory and matching rules."""

    id: CategoryId
    name: str
    download_dir: str
    rule: CategoryRule
    icon_name: str = "folder"
