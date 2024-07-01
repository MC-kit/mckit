"""Code to load source distribution and print corresponding MCNP SDEF."""

from __future__ import annotations

from itertools import pairwise

import numpy as np

from numpy.typing import ArrayLike

from .printer import print_card, separate


class Distribution:
    """Represents a distribution of source variable.

    If the len of probs equals to the len of values, then the distribution is
    either of discrete variable (if is_discrete flag is set) or probs sets
    probability density values. If len(probs) + 1 == len(values), then
    values are bin boundaries for continuous distribution.

    Args:
        name:  Distribution's name. It is needed for MCNP.
        values: A list of values, that variable can be equal to. Values can be a float,
                an int or other Distribution instances.
        probs: A list of probabilities or a distribution this one depends on.
               Probabilities need not be normalized.
        distribution_variable:   Source variable's name. Default: None.
        is_discrete: Indicate that the variable is discrete. Default: False.

    Attributes:
        _name: Distribution's name
        _var: Name of source variable
        _is_discrete: is this discrete or histogram distribution
        _values: bin values
        _probs: probabilities or distributions for bins
        _is_pdf: is this PDF or more complicated distribution?
    """

    def __init__(
        self,
        name: int,
        values: ArrayLike | list[Distribution],
        probs: ArrayLike | Distribution,
        distribution_variable: str | None = None,
        is_discrete: bool = False,
    ) -> None:
        self._name = name
        self._var = distribution_variable
        Distribution.check_distr(values, len(probs), is_discrete)
        self._is_discrete = is_discrete
        self._values = np.asarray(values)
        if isinstance(probs, Distribution):
            self._probs: ArrayLike | Distribution = probs
        else:
            self._probs = np.asarray(probs)
        self._is_pdf = (
            isinstance(self._probs, np.ndarray)
            and len(self._probs) == len(values)
            and not is_discrete
            and not isinstance(self._values[0], Distribution)
        )

    @property
    def name(self) -> int:
        """Gets distribution's name."""
        return self._name

    @property
    def size(self) -> int:
        """The distribution's size.

        Returns:
            The number of probability values.
        """
        return len(self._probs)

    @property
    def variable(self) -> str | None:
        """Gets distribution's source variable name."""
        return self._var

    @property
    def has_nested_distributions(self) -> bool:
        """Are there nested (inner) distributions?"""
        return isinstance(self._values[0], Distribution)

    @staticmethod
    def check_distr(
        bins_or_distrs: [ArrayLike | list[Distribution]],
        size: int,
        is_discrete: bool,
    ) -> None:
        """Checks if the distribution is correct.

        Args:
            bins_or_distrs: List of variable values.
            size: The length of intensity matrix along variable dimension.
            is_discrete:  True <=> the distribution is discrete.

        Raises:
            ValueError: if the distribution is neither discrete, nor pdf, nor histogram.
        """
        discrete_or_pdf = len(bins_or_distrs) == size
        histogram = len(bins_or_distrs) == size + 1 and not is_discrete
        if not discrete_or_pdf and not histogram:
            raise ValueError("Inconsistent size of values.")
        _check_all_are_distributions_or_not(bins_or_distrs)

    def mcnp_repr(self) -> str:
        """Returns a string representation of corresponding MCNP card."""
        bin_tokens = self._bin_tokens_repr()

        prob_tokens = self._prob_tokens_repr(bin_tokens)

        card = print_card(separate(bin_tokens))

        if prob_tokens:
            card += "\n" + print_card(separate(prob_tokens))

        return card

    def get_inner(self) -> set[Distribution]:
        """Gets nested distributions this one depends on.

        If values of this distribution are distributions themselves,
        then they are returned.

        Returns:
            Set:  A set of nested distributions, if any, empty set otherwise.
        """
        return set(self._values) if self.has_nested_distributions else set()

    def depends_on(self) -> Distribution | None:
        """Gets distribution this one depends on.

        Returns:
            Distribution|None:  Distribution this one depends on, if any. None otherwise.
        """
        if isinstance(self._probs, Distribution):
            return self._probs
        return None

    def _mcnp_distribution_tag(self):
        if self._is_discrete:
            return "L"
        if self._is_pdf:
            return "A"
        return "H"

    def _prob_tokens_repr(self, bin_tokens):
        if isinstance(self._probs, Distribution):
            bin_tokens.insert(0, f"DS{self._name}")
            prob_tokens = None
        else:
            bin_tokens.insert(0, f"SI{self._name}")
            prob_tokens = [f"SP{self._name}"]

            if not self._is_pdf:
                prob_tokens.append("D")

            if len(self._values) == len(self._probs) + 1:
                prob_tokens.append("0")

            prob_tokens.extend(str(p) for p in self._probs)
        return prob_tokens

    def _bin_tokens_repr(self):
        bin_tokens = []
        if self.has_nested_distributions:
            bin_tokens.append("S")
            bin_tokens.extend(str(v.name) for v in self._values)
        else:
            bin_tokens.append(self._mcnp_distribution_tag())

            if isinstance(self._values[0], np.ndarray):
                values_repr = np.concatenate(self._values)
            else:
                values_repr = self._values

            bin_tokens.extend(str(v) for v in values_repr)
        return bin_tokens

    def __len__(self) -> int:
        """Size of distribution."""
        return len(self._probs)


def _check_all_are_distributions_or_not(bins_or_distrs):
    expect_distributions = isinstance(bins_or_distrs[0], Distribution)
    if not all(expect_distributions == isinstance(x, Distribution) for x in bins_or_distrs):
        raise TypeError("Distribution bins should be either all Distributions or all not")


def create_bin_distributions(
    bins: list[float], start_name: int = 1
) -> tuple[int, list[Distribution]]:
    """Creates bin distributions for specified bins.

    A list of distributions created. Index in the list corresponds to the  index of bin.

    Args:
        bins:   A list of bin boundaries.
        start_name:  Starting name for distributions.
                     For every new distribution the name is incremented by 1.

    Returns:
        free_name, list of distributions
    """
    distributions = []
    for low, high in pairwise(bins):
        distributions.append(Distribution(start_name, [low, high], [1]))
        start_name += 1
    return start_name, distributions


class Source:
    """Represents particle source.

    Args:
        variables:
            A dictionary of source variables. var_name -> var_value. The value
            can be either float (int) value or Distribution instance.
    """

    def __init__(self, **variables: dict[int, int | float | Distribution]) -> None:
        self._variables = variables

    def mcnp_repr(self) -> str:
        """Gets a string representation of corresponding MCNP card."""
        tokens = ["SDEF"]
        cards = []
        extra_cards = []

        for k, v in self._variables.items():
            tokens.append(f"{k}={_var_repr(v)}")
            if isinstance(v, Distribution):
                cards.append(v.mcnp_repr())
                for ec in sorted(v.get_inner(), key=lambda x: x.name):
                    extra_cards.append(ec.mcnp_repr())
        cards.insert(0, print_card(separate(tokens)))
        cards.extend(extra_cards)
        return "\n".join(cards)


def _var_repr(distribution) -> str:
    if isinstance(distribution, Distribution):
        dep = distribution.depends_on()
        text = f"D{distribution.name}"
        if dep:
            text = f"F{dep.variable} " + text
    else:
        text = str(distribution)
    return text
