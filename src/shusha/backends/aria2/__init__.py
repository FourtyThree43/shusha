"""aria2 Reference Backend implementation package for Shusha."""

from shusha.backends.aria2.adapter import ARIA2_CAPABILITIES, Aria2Backend
from shusha.backends.aria2.options import load_aria2_options
from shusha.backends.aria2.supervisor import Aria2Supervisor

__all__ = [
    "ARIA2_CAPABILITIES",
    "Aria2Backend",
    "Aria2Supervisor",
    "load_aria2_options",
]
