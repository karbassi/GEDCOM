from __future__ import annotations

from gedcom7 import (
    VOID,
    CallNumber,
    Document,
    Individual,
    PersonalName,
    Repository,
    Source,
    SourceCitation,
    SourceRepositoryCitation,
    dumps,
)
from gedcom7.enums import MediaType, Quality


def test_source_with_repository_citation() -> None:
    repo = Repository("National Archives")
    source = Source(
        author="Jane Historian",
        title="Parish Register",
        repository_citations=[
            SourceRepositoryCitation(
                repo, call_numbers=[CallNumber("MS 42", medium=MediaType.BOOK)]
            )
        ],
    )
    out = dumps(Document(records=[source, repo]))
    assert "0 @S1@ SOUR\n1 AUTH Jane Historian\n1 TITL Parish Register\n" in out
    assert "1 REPO @R1@\n2 CALN MS 42\n3 MEDI BOOK\n" in out
    assert "0 @R1@ REPO\n1 NAME National Archives\n" in out


def test_individual_cites_source() -> None:
    source = Source(title="Birth Record")
    indi = Individual(
        names=[PersonalName("X //")],
        source_citations=[SourceCitation(source, page="p. 12", quality=Quality.DIRECT)],
    )
    out = dumps(Document(records=[indi, source]))
    assert "1 SOUR @S1@\n2 PAGE p. 12\n2 QUAY 3\n" in out


def test_void_source_citation() -> None:
    indi = Individual(
        names=[PersonalName("X //")],
        source_citations=[SourceCitation(VOID, page="family bible")],
    )
    out = dumps(Document(records=[indi]))
    assert "1 SOUR @VOID@\n2 PAGE family bible\n" in out
