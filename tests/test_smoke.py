from __future__ import annotations

import gedcom7


def test_version_is_exposed() -> None:
    assert isinstance(gedcom7.__version__, str)
    assert gedcom7.__version__
