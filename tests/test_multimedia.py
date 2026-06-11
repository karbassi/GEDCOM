from __future__ import annotations

import pytest

from gedcom7 import (
    Crop,
    Document,
    File,
    Individual,
    Multimedia,
    MultimediaLink,
    PersonalName,
    ValidationError,
    dumps,
)
from gedcom7.enums import Medium


def test_multimedia_record_with_file() -> None:
    obje = Multimedia(
        files=[File("media/photo.jpg", "image/jpeg", medium=Medium.PHOTO, title="Portrait")]
    )
    out = dumps(Document(records=[obje]))
    assert (
        "0 @O1@ OBJE\n1 FILE media/photo.jpg\n2 FORM image/jpeg\n3 MEDI PHOTO\n2 TITL Portrait\n"
        in out
    )


def test_multimedia_link_with_crop() -> None:
    obje = Multimedia(files=[File("media/p.jpg", "image/jpeg")])
    indi = Individual(
        names=[PersonalName("X //")],
        media_links=[
            MultimediaLink(obje, crop=Crop(top=10, left=20, height=100, width=80), title="Face")
        ],
    )
    out = dumps(Document(records=[indi, obje]))
    assert (
        "1 OBJE @O1@\n2 CROP\n3 TOP 10\n3 LEFT 20\n3 HEIGHT 100\n3 WIDTH 80\n2 TITL Face\n" in out
    )


def test_empty_multimedia_rejected() -> None:
    with pytest.raises(ValidationError, match="OBJE requires at least one FILE"):
        dumps(Document(records=[Multimedia()]))


def test_file_without_form_rejected() -> None:
    with pytest.raises(ValidationError, match="requires a non-empty FORM"):
        dumps(Document(records=[Multimedia(files=[File("x.jpg", "")])]))
