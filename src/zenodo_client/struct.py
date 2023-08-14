# -*- coding: utf-8 -*-

"""Data structures for Zenodo."""

import datetime
from typing import Optional, Sequence

from pydantic import BaseModel, Field
from typing_extensions import Literal

__all__ = [
    "Creator",
    "Metadata",
]


# https://developers.zenodo.org/#rest-api


class Creator(BaseModel):
    """A creator, see https://developers.zenodo.org/#representation."""

    name: str = Field(
        ..., description="Name of the creator in the format Family name, given names", example="Hoyt, Charles Tapley"
    )
    affiliation: Optional[str] = Field(
        default=None, 
        description="affiliation of the creator", 
        example="Harvard Medical School",
    )
    orcid: Optional[str] = Field(
        default=None, 
        description="ORCID identifier of the creator",
        example="0000-0003-4423-4370",
    )
    gnd: Optional[str] = Field(
        default=None,
        description="German National Library identifier of the creator. "
        "See also https://www.wikidata.org/wiki/Property:P227."
    )

    @property
    def orcid_url(self) -> Optional[str]:
        """Get the ORCID identifier as a URL."""
        return f"https://orcid.org/{self.orcid}" if self.orcid else None

    @property
    def gnd_url(self) -> Optional[str]:
        """Get the GND identifier as a URL."""
        return f"https://d-nb.info/gnd/{self.gnd}" if self.gnd else None

    def __post_init__(self):  # noqa:D105
        if "," not in self.name:
            raise ValueError("name should be in format Family name, given names")


UploadType = Literal[
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
]

PublicationType = Literal[
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
]

ImageType = Literal[
    "figure",
    "plot",
    "drawing",
    "diagram",
    "photo",
    "other",
]
AccessRight = Literal[
    "open",
    "embargoed",
    "restricted",
    "closed",
]


def _today_str() -> str:
    return datetime.datetime.today().strftime("%Y-%m-%d")


class Metadata(BaseModel):
    """Metadata for the Zenodo deposition API."""

    title: str
    upload_type: UploadType
    description: str
    creators: Sequence[Creator]
    access_right: AccessRight = "open"
    language: Optional[str] = "eng"
    version: Optional[str] = Field(default_factory=_today_str)
    license: Optional[str] = "CC0-1.0"
    publication_type: Optional[PublicationType] = None
    image_type: Optional[ImageType] = None

    def __post_init__(self):  # noqa:D105
        if self.upload_type == "publication":
            if self.publication_type is None:
                raise ValueError("missing publication_type")
        elif self.upload_type == "image":
            if self.image_type is None:
                raise ValueError("missing image_type")
        if self.access_right in {"open", "embargoed"}:
            if self.license is None:
                raise ValueError(f"need a license for access_right={self.access_right}")
