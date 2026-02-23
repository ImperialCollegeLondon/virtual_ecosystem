"""The :mod:`~virtual_ecosystem.models.animal.cnp` module contains the class for
managing pools of stoichiometric explicit mass: carbon (C), nitrogen (N), and phosphorus
(P).
"""  # noqa: D205

from __future__ import annotations

from dataclasses import asdict, dataclass

from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.models.soil.model_config import SoilConfiguration


@dataclass
class CNP:
    """A dataclass representing Carbon (C), Nitrogen (N), and Phosphorus (P) mass.

    This class features common operations on CNP mass, including arithmetic
    manipulations, stoichiometric calculations, and ratio/proportion retrieval.

    Attributes:
        C (float): The mass of carbon in the entity [kg].
        N (float): The mass of nitrogen in the entity [kg].
        P (float): The mass of phosphorus in the entity [kg].
    """

    C: float
    N: float
    P: float

    @property
    def total(self) -> float:
        """Calculate the total combined mass of C, N, and P.

        Returns:
            float: The sum of carbon, nitrogen, and phosphorus mass.
        """
        return self.C + self.N + self.P

    def __getitem__(self, key: str) -> float:
        """Allow dictionary-style access to C, N, and P values.

        Args:
            key (str): One of 'C', 'N', or 'P'.

        Returns:
            float: The corresponding element's mass.

        Raises:
            KeyError: If the key is not one of the three valid elements.
        """
        if key not in {"C", "N", "P"}:
            raise KeyError(f"Invalid key: {key}. Must be 'C', 'N', or 'P'.")
        return getattr(self, key)

    def _validate_non_negative(self) -> None:
        """Ensure that no element becomes negative after an update.

        Raises:
            ValueError: If C, N, or P is negative.
        """
        for name, value in asdict(self).items():
            if value < 0:
                raise ValueError(
                    f"{name.capitalize()} mass cannot be negative. Current values: "
                    f"C={self.C}, N={self.N},"
                    f"P={self.P}."
                )

    def update(self, *, C: float = 0.0, N: float = 0.0, P: float = 0.0) -> None:
        """Update C, N, and P values. Positive values add; negative values subtract.

        Args:
            C: Amount of carbon to adjust. Defaults to 0.0.
            N: Amount of nitrogen to adjust. Defaults to 0.0.
            P: Amount of phosphorus to adjust. Defaults
             to 0.0.

        """

        self.C += C
        self.N += N
        self.P += P
        self._validate_non_negative()

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> CNP:
        """Create a CNP instance from a dictionary.

        Args:
            data (dict[str, float]): A dictionary containing 'C', 'N', and
                'P' as keys.

        Returns:
            CNP: A new CNP instance with the values from the dictionary.
        """
        return cls(
            C=data.get("C", 0.0),
            N=data.get("N", 0.0),
            P=data.get("P", 0.0),
        )

    def get_ratios(self) -> dict[str, float]:
        """Calculate the Carbon:Nitrogen (C:N) and Carbon:Phosphorus (C:P) ratios.

        TODO: finalize alternative output with jacob

        Returns:
            dict[str, float]: A dictionary containing:
                - "C:N" (float): Carbon-to-nitrogen ratio
                - "C:P" (float): Carbon-to-phosphorus ratio
        """
        return {
            "C:N": self.C / self.N if self.N > 0 else 0.0,
            "C:P": self.C / self.P if self.P > 0 else 0.0,
        }

    def get_proportions(self) -> dict[str, float]:
        """Calculate the proportion of each element relative to the total CNP mass.

        If the total mass is zero, proportions are set to zero to avoid division errors.

        Returns:
            dict[str, float]: A dictionary containing:
                - "C" (float): Proportion of carbon in total mass.
                - "N" (float): Proportion of nitrogen in total mass.
                - "P" (float): Proportion of phosphorus in total mass.
        """
        total_mass = self.total
        return {
            "C": self.C / total_mass if total_mass > 0 else 0.0,
            "N": self.N / total_mass if total_mass > 0 else 0.0,
            "P": self.P / total_mass if total_mass > 0 else 0.0,
        }


def find_microbial_stoichiometries(
    config: CompiledConfiguration,
) -> dict[str, dict[str, float]]:
    """Find the stoichiometries of each microbial functional group.

    This extracts the soil configuration from the simulation configuration and then
    compiles a dictionary of CN and CP ratios for each microbial group.

    Args:
        config: A compiled Virtual Ecosystem configuration instance.

    Returns:
        A dictionary containing the carbon to nutrient ratios of each microbial
        functional group, for both nitrogen and phosphorus [unitless]
    """

    soil_config: SoilConfiguration = config.get_subconfiguration(
        "soil", SoilConfiguration
    )

    return {
        group.name: {"N": group.c_n_ratio, "P": group.c_p_ratio}
        for group in soil_config.microbial_group_definition
    }
