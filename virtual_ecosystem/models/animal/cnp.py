"""The :mod:`~virtual_ecosystem.models.animal.cnp` module contains the class for
managing pools of stoichiometric explicit mass: carbon (C), nitrogen (N), and phosphorus
(P).
"""  # noqa: D205

from dataclasses import dataclass


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

    def scale(self, proportions: dict[str, float]) -> "CNP":
        """Redistribute the total mass according to specified proportions.

        This method scales the carbon, nitrogen, and phosphorus masses such that their
        new values sum to the original total mass, following the given proportions.

        Args:
            proportions (dict[str, float]): A dictionary specifying the desired
                proportions for "carbon", "nitrogen", and "phosphorus". These should
                  sum to 1.

        Returns:
            CNP: A new CNP instance with masses adjusted to match the proportions.

        Raises:
            KeyError: If `proportions` is missing any required keys.
            ValueError: If the proportions do not sum to 1 (allowing small
              floating-point errors).
        """
        required_keys = {"carbon", "nitrogen", "phosphorus"}

        # Ensure all required keys are present
        if not required_keys.issubset(proportions):
            raise KeyError(
                f"Missing required proportion keys: "
                f"{required_keys - proportions.keys()}"
            )

        # Sum of proportions must be 1 (allowing a small floating-point error)
        total_proportion = sum(proportions.values())
        if not (0.999 <= total_proportion <= 1.001):
            raise ValueError(
                f"Proportions must sum to 1.0, but got {total_proportion:.6f}"
            )

        # Redistribute mass according to the given proportions
        total_mass = self.total
        return CNP(
            carbon=total_mass * proportions["carbon"],
            nitrogen=total_mass * proportions["nitrogen"],
            phosphorus=total_mass * proportions["phosphorus"],
        )

    def add(self, other: "CNP") -> "CNP":
        """Perform element-wise addition with another CNP object.

        Args:
            other (CNP): Another CNP instance.

        Returns:
            CNP: A new CNP instance representing the sum of both.
        """
        return CNP(
            carbon=self.carbon + other.carbon,
            nitrogen=self.nitrogen + other.nitrogen,
            phosphorus=self.phosphorus + other.phosphorus,
        )

    def subtract(self, other: "CNP") -> "CNP":
        """Perform element-wise subtraction with another CNP object.

        Args:
            other (CNP): Another CNP instance.

        Returns:
            CNP: A new CNP instance representing the element-wise difference.
        """
        return CNP(
            carbon=self.carbon - other.carbon,
            nitrogen=self.nitrogen - other.nitrogen,
            phosphorus=self.phosphorus - other.phosphorus,
        )

    def to_dict(self) -> dict[str, float]:
        """Convert the CNP object to a dictionary representation.

        Returns:
            dict[str, float]: A dictionary with 'carbon', 'nitrogen', and 'phosphorus'
                as keys and their respective mass values as values.
        """
        return {
            "carbon": self.carbon,
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "CNP":
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
