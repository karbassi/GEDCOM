from __future__ import annotations

import pytest

from gedcom7 import (
    Document,
    Individual,
    Note,
    NoteTranslation,
    PersonalName,
    SharedNote,
    ValidationError,
    dumps,
)


def _indi(**kw: object) -> Individual:
    return Individual(names=[PersonalName("X //")], **kw)  # type: ignore[arg-type]


def test_inline_note_with_translation() -> None:
    note = Note(
        "Named after his grandfather.",
        language="en",
        translations=[NoteTranslation("Benannt nach...", language="de")],
    )
    out = dumps(Document(records=[_indi(notes=[note])]))
    assert (
        "1 NOTE Named after his grandfather.\n2 LANG en\n2 TRAN Benannt nach...\n3 LANG de\n" in out
    )


def test_multiline_note_uses_cont() -> None:
    note = Note("first line\nsecond line")
    out = dumps(Document(records=[_indi(notes=[note])]))
    assert "1 NOTE first line\n2 CONT second line\n" in out


def test_shared_note_record_and_pointer() -> None:
    shared = SharedNote('"Gordon" is a traditional Scottish surname.')
    indi = _indi(notes=[shared])
    out = dumps(Document(records=[indi, shared]))
    assert '0 @N1@ SNOTE "Gordon" is a traditional Scottish surname.\n' in out
    assert "1 SNOTE @N1@\n" in out


def test_note_translation_requires_mime_or_lang() -> None:
    note = Note("x", translations=[NoteTranslation("y")])
    with pytest.raises(ValidationError, match="note TRAN requires a MIME and/or a LANG"):
        dumps(Document(records=[_indi(notes=[note])]))
