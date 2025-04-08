"""The :mod:`~virtual_ecosystem.models.animal.cnp` module contains the class for
managing pools of stoichiometric explicit mass: carbon (C), nitrogen (N), and phosphorus
(P).
"""  # noqa: D205

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class CNP:
    """A dataclass representing Carbon (C), Nitrogen (N), and Phosphorus (P) mass.

    This class features common operations on CNP mass, including arithmetic
    manipulations, stoichiometric calculations, and ratio/proportion retrieval.

    Attributes:
        carbon (float): The mass of carbon in the entity [kg].
        nitrogen (float): The mass of nitrogen in the entity [kg].
        phosphorus (float): The mass of phosphorus in the entity [kg].
    """

    carbon: float
    nitrogen: float
    phosphorus: float

    @property
    def total(self) -> float:
        """Calculate the total combined mass of C, N, and P.

        Returns:
            float: The sum of carbon, nitrogen, and phosphorus mass.
        """
        return self.carbon + self.nitrogen + self.phosphorus

    def __getitem__(self, key: str) -> float:
        """Allow dictionary-style access to C, N, and P values.

        Args:
            key (str): One of 'carbon', 'nitrogen', or 'phosphorus'.

        Returns:
            float: The corresponding element's mass.

        Raises:
            KeyError: If the key is not one of the three valid elements.
        """
        if key not in {"carbon", "nitrogen", "phosphorus"}:
            raise KeyError(
                f"Invalid key: {key}. Must be 'carbon', 'nitrogen', or 'phosphorus'."
            )
        return getattr(self, key)

    def _validate_non_negative(self) -> None:
        """Ensure that no element becomes negative after an update.

        Raises:
            ValueError: If carbon, nitrogen, or phosphorus is negative.
        """
        for name, value in asdict(self).items():
            if value < 0:
                raise ValueError(
                    f"{name.capitalize()} mass cannot be negative. Current values: "
                    f"carbon={self.carbon}, nitrogen={self.nitrogen},"
                    f"phosphorus={self.phosphorus}."
                )

    def update(
        self, *, carbon: float = 0.0, nitrogen: float = 0.0, phosphorus: float = 0.0
    ) -> None:
        """Update C, N, and P values. Positive values add; negative values subtract.

        Args:
            carbon: Amount of carbon to adjust. Defaults to 0.0.
            nitrogen: Amount of nitrogen to adjust. Defaults to 0.0.
            phosphorus: Amount of phosphorus to adjust. Defaults
             to 0.0.

        """

        self.carbon += carbon
        self.nitrogen += nitrogen
        self.phosphorus += phosphorus
        self._validate_non_negative()

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> CNP:
        """Create a CNP instance from a dictionary.

        Args:
            data (dict[str, float]): A dictionary containing 'carbon', 'nitrogen', and
                'phosphorus' as keys.

        Returns:
            CNP: A new CNP instance with the values from the dictionary.
        """
        return cls(
            carbon=data.get("carbon", 0.0),
            nitrogen=data.get("nitrogen", 0.0),
            phosphorus=data.get("phosphorus", 0.0),
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
            "C:N": self.carbon / self.nitrogen if self.nitrogen > 0 else 0.0,
            "C:P": self.carbon / self.phosphorus if self.phosphorus > 0 else 0.0,
        }

    def get_proportions(self) -> dict[str, float]:
        """Calculate the proportion of each element relative to the total CNP mass.

        If the total mass is zero, proportions are set to zero to avoid division errors.

        Returns:
            dict[str, float]: A dictionary containing:
                - "carbon" (float): Proportion of carbon in total mass.
                - "nitrogen" (float): Proportion of nitrogen in total mass.
                - "phosphorus" (float): Proportion of phosphorus in total mass.
        """
        total_mass = self.total
        return {
            "carbon": self.carbon / total_mass if total_mass > 0 else 0.0,
            "nitrogen": self.nitrogen / total_mass if total_mass > 0 else 0.0,
            "phosphorus": self.phosphorus / total_mass if total_mass > 0 else 0.0,
        }
