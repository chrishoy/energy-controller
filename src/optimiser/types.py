"""Data structures for heating optimiser."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple

from .simple_greedy_optimiser import (
    optimize_heating_schedule as simple_greedy_optimiser,
)
from .advanced_predictive_optimiser import (
    optimize_heating_schedule as advanced_predictive_optimiser,
)


@dataclass
class OptimisationParams:
    """Structure to hold all optional parameters for the optimiser."""

    comfort_hours: List[Tuple[int, int]] = field(
        default_factory=lambda: [(7, 9), (17, 22)]
    )
    preheat_slots: int = 2
    retain_slots: int = 4
    slot_duration_hours: float = 0.5
    power_kw: float = 1.0


# --- Strategy Enum ---


class OptimisationStrategy(Enum):
    """Enumeration to select the optimization algorithm."""

    SIMPLE_GREEDY = simple_greedy_optimiser
    ADVANCED_PREDICTIVE = advanced_predictive_optimiser

    def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        """Allows the Enum member to be called directly like a function."""
        return self.value(*args, **kwargs)
