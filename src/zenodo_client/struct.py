"""Data structures for Zenodo."""

import datetime
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "AccessRight",
    "Community",
    "Creator",
    "ImageType",
    "Metadata",
    "PublicationType",
    "UploadType",
]


# https://developers.zenodo.org/#rest-api


class Creator(BaseModel):
    """A creator, see https://developers.zenodo.org/#representation."""

    name: str = Field(
        ...,
        description="Name of the creator in the format Family name, given names",
        examples=["Hoyt, Charles Tapley"],
    )
    affiliation: str | None = Field(
        default=None,
        description="affiliation of the creator",
        examples=["Harvard Medical School"],
    )
    orcid: str | None = Field(
        default=None,
        description="ORCID identifier of the creator",
        examples=["0000-0003-4423-4370"],
    )
    gnd: str | None = Field(
        default=None,
        description="German National Library identifier of the creator. "
        "See also https://www.wikidata.org/wiki/Property:P227.",
    )

    @property
    def orcid_url(self) -> str | None:
        """Get the ORCID identifier as a URL."""
        return f"https://orcid.org/{self.orcid}" if self.orcid else None

    @property
    def gnd_url(self) -> str | None:
        """Get the GND identifier as a URL."""
        return f"https://d-nb.info/gnd/{self.gnd}" if self.gnd else None

    @field_validator("name")
    def comma_in_name(cls, v: str) -> str:  # noqa:N805
        """Check that a comma appears in the name."""
        if "," not in v:
            raise ValueError("name should be in format Family name, given names")
        return v


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


class Community(BaseModel):
    """A simple model representing a community."""

    identifier: str


class Metadata(BaseModel):
    """Metadata for the Zenodo deposition API."""

    title: str
    upload_type: UploadType
    description: str
    creators: Sequence[Creator]
    access_right: AccessRight = "open"
    language: str | None = "eng"
    version: str | None = Field(default_factory=_today_str)
    license: str | None = "CC0-1.0"
    publication_type: PublicationType | None = None
    image_type: ImageType | None = None
    communities: list[Community] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    notes: str | None = None
    embargo_date: str | None = None

    def __post_init__(self) -> None:
        if self.upload_type == "publication":
            if self.publication_type is None:
                raise ValueError("missing publication_type")
        if self.publication_type is not None and self.upload_type != "publication":
            raise ValueError(
                f"Can't use publication_type with upload_type={self.upload_type}. Need publication."
            )
        elif self.upload_type == "image":
            if self.image_type is None:
                raise ValueError("missing image_type")
        if self.access_right in {"open", "embargoed"}:
            if self.license is None:
                raise ValueError(f"need a license for access_right={self.access_right}")
        if self.access_right == "embargoed" and self.embargo_date is None:
            raise ValueError("Missing embargo date")
