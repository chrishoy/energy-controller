# --- Optimiser Class (The Context) ---


from typing import Any, Dict, List

from src.rates.types import Rate

from .types import OptimisationStrategy, OptimisationParams


class Optimiser:
    """
    A class to select and execute the chosen optimisation algorithm
    using the Strategy Pattern.
    """

    def run_optimisation(
        self,
        data: List[Rate],
        strategy: OptimisationStrategy,
        optimisation_params: OptimisationParams,
    ) -> Dict[str, Any]:
        """
        Executes the selected optimisation strategy, unpacking parameters
        from the OptimisationParams object.

        Args:
            data: The time-series data (rates).
            strategy: The OptimisationStrategy Enum member to use.
            optimisation_params: Dataclass holding the optimisation tuning parameters.

        Returns:
            The result of the optimisation (schedule, cost, etc.).
        """

        # Convert the dataclass parameters to a dictionary (**kwargs)
        params_dict = optimisation_params.__dict__

        # Execute the chosen algorithm using the standard signature
        result = strategy(data=data, **params_dict)  # Unpack all the parameters

        return result
