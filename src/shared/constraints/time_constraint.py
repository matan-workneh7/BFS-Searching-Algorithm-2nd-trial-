"""
Time constraint implementation.
Generic constraint that can work with any graph and path calculator.
"""

from typing import List

from core.graph_interface import GraphInterface, ConstraintInterface, PathCalculatorInterface


class TimeConstraint(ConstraintInterface):
    """Constraint to limit estimated travel time along a path."""

    def __init__(
        self,
        max_time_seconds: float,
        path_calculator: PathCalculatorInterface,
        average_speed_m_per_s: float,
    ):
        """
        Initialize with maximum allowed time and speed model.

        Args:
            max_time_seconds: Maximum allowed travel time (in seconds)
            path_calculator: Calculator to compute path distance (in meters)
            average_speed_m_per_s: Assumed average travel speed in m/s
        """
        self.max_time_seconds = max_time_seconds
        self.path_calculator = path_calculator
        self.average_speed_m_per_s = average_speed_m_per_s

    def validate(self, path: List[int], graph: GraphInterface) -> tuple[bool, str]:
        """
        Validate that the estimated travel time doesn't exceed the limit.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.average_speed_m_per_s <= 0:
            # Degenerate speed, treat as no time constraint
            return True, ""

        distance_m = self.path_calculator.calculate_path_cost(path, graph)
        # Convert distance and speed to time
        estimated_time_s = distance_m / self.average_speed_m_per_s

        if estimated_time_s > self.max_time_seconds:
            # Present message in minutes for easier interpretation
            est_min = estimated_time_s / 60.0
            max_min = self.max_time_seconds / 60.0
            return (
                False,
                f"Estimated travel time ({est_min:.1f} min) exceeds maximum ({max_min:.1f} min)",
            )

        return True, ""


