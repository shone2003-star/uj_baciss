"""Tools the Routing Agent can call. They read data/knowledge_base/directory.json."""

import json

from langchain.tools import tool

from community_voice.core.config import PROJECT_ROOT

_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "directory.json"
_PLACES_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "places.json"
_DIRECTORY = json.loads(_PATH.read_text(encoding="utf-8"))
_AREAS = {name.lower(): muni for name, muni in _DIRECTORY["areas"].items()}
_MUNICIPALITIES = {name.lower(): name for name in _DIRECTORY["municipalities"]}
_PLACES = json.loads(_PLACES_PATH.read_text(encoding="utf-8"))
_MORE_PLACES = {  # keys starting with "_" are notes, not places
    name.lower() for key, names in _PLACES.items() if key[0] != "_" for name in names
}


def known_places() -> set[str]:
    """Lower-case names of places the privacy filter must keep.

    The directory (what routing knows) plus a wider list of South African places.
    """
    return set(_AREAS) | set(_MUNICIPALITIES) | _MORE_PLACES


@tool
def find_municipality(area: str) -> str:
    """Find the municipality for an area. Known names inside the text also match."""
    text = area.lower()
    for name, municipality in _AREAS.items():
        if name in text:
            return municipality
    return f"Area '{area}' not found in the directory."


@tool
def lookup_department(municipality: str, category: str) -> str:
    """Find the department and phone number for a service category in a municipality.

    Categories: water, electricity, roads, sanitation, waste, other.
    """
    name = _MUNICIPALITIES.get(municipality.strip().lower())
    department = _DIRECTORY["departments"].get(category.strip().lower())
    if not name:
        return f"Municipality '{municipality}' not found in the directory."
    if not department:
        return f"Category '{category}' not found in the directory."
    phone = _DIRECTORY["municipalities"][name]["phone"]
    return f"{name} {department} department, phone {phone}"
