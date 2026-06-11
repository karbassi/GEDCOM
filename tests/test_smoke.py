from __future__ import annotations

import gedcom


def test_version_is_exposed() -> None:
    assert isinstance(gedcom.__version__, str)
    assert gedcom.__version__
