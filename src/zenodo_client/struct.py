# -*- coding: utf-8 -*-

"""Data structures for Zenodo."""

import datetime
from dataclasses import dataclass, field
from typing import Optional, Sequence

from dataclasses_json import DataClassJsonMixin

__all__ = [
    "Creator",
    "Metadata",
]


@dataclass
class Creator(DataClassJsonMixin):
    """A creator."""

    #: Name of the creator in the format Family name, given names
    name: str
    #: Affiliation of the creator
    affiliation: Optional[str] = None
    #: ORCID identifier of the creator
    orcid: Optional[str] = None

    #: GND identifier of creator
    # gnd: Optional[str] = None

    def __post_init__(self):  # noqa:D105
        if "," not in self.name:
            raise ValueError("name should be in format Family name, given names")


ALLOWED_TYPES = {
    "publication",
    "poster",
    "presentation",
    "dataset",
    "image",
    "video",
    "software",
    "lesson",
    "physicalobject",
    "other",
}

ALLOWED_PUBLICATION_TYPES = {
    "annotationcollection",
    "book",
    "section",
    "conferencepaper",
    "datamanagementplan",
    "article",
    "patent",
    "preprint",
    "deliverable",
    "milestone",
    "proposal",
    "report",
    "softwaredocumentation",
    "taxonomictreatment",
    "technicalnote",
    "thesis",
    "workingpaper",
    "other",
}

VALID_IMAGE_TYPES = {
    "figure",
    "plot",
    "drawing",
    "diagram",
    "photo",
    "other",
}
ALLOWED_ACCESS_RIGHT = {
    "open",
    "embargoed",
    "restricted",
    "closed",
}


@dataclass
class Metadata(DataClassJsonMixin):
    """Metadata for the Zenodo deposition API."""

    title: str
    upload_type: str
    description: str
    creators: Sequence[Creator]
    access_right: str = "open"
    language: Optional[str] = "eng"
    version: Optional[str] = field(default_factory=lambda: datetime.datetime.today().strftime("%Y-%m-%d"))
    license: Optional[str] = "CC0-1.0"
    publication_type: Optional[str] = None
    image_type: Optional[str] = None

    def __post_init__(self):  # noqa:D105
        if self.upload_type not in ALLOWED_TYPES:
            raise ValueError(f"invalid upload_type: {self.upload_type}")
        if self.upload_type == "publication":
            if self.publication_type is None:
                raise ValueError("missing publication_type")
            if self.publication_type not in ALLOWED_PUBLICATION_TYPES:
                raise ValueError(f"invalid publication_type: {self.publication_type}")
        elif self.upload_type == "image":
            if self.image_type is None:
                raise ValueError("missing image_type")
            if self.image_type not in VALID_IMAGE_TYPES:
                raise ValueError(f"invalid image_type: {self.image_type}")
        if self.access_right in {"open", "embargoed"}:
            if self.license is None:
                raise ValueError(f"need a license for access_right={self.access_right}")
