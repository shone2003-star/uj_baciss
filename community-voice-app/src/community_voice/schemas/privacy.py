"""Contracts for the privacy filter."""

from pydantic import BaseModel, Field


class PiiSpans(BaseModel):
    """What the local model finds. Code does the replacing."""

    # No defaults: required fields stop the model answering with an empty {}.
    names: list[str] = Field(
        description="Names of people, exactly as written in the text.",
    )
    addresses: list[str] = Field(
        description=(
            "Street addresses (street and number, house, stand or erf number), "
            "exactly as written. Never suburbs, towns or cities."
        ),
    )


class RedactionResult(BaseModel):
    """The text that may leave this computer, and what was removed from it."""

    text: str
    counts: dict[str, int] = Field(default_factory=dict)  # kind -> items removed
    model_used: bool = True  # False: the local model was skipped or unreachable
