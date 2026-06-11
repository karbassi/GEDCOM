# Drop TOML from the authoring dialect

The CLI authoring document is accepted as **YAML or JSON only**. TOML support — a parser branch, an `init` template, and its mention across `schema`/`guide`/help/docs — is removed. This reverses the original CLI design (`.scratch/gedcom-cli/`), which listed TOML as a first-class input alongside YAML and JSON.

## Why

The authoring document is deeply nested and array-heavy: `individuals[] → events[] → place → map`, `names[] → translations[]`, citations, ordinances. TOML is built for shallow configuration, not deep trees — arrays of tables (`[[individuals.events]]`) force every nested list to restate its full path in a header, so the visual hierarchy that makes a hand-authored family tree readable is lost exactly where it matters most. Nobody should reach for TOML to write a genealogy.

TOML's *cost* was low (stdlib `tomllib`, read-only), but so was its *value* for this shape, and it still carried real surface area: a documented format users had to choose between, an extra `init` template, schema/guide copy, and a slice of the test matrix. Trimming it sharpens the recommended path — **YAML for humans, JSON for machines and agents** — both of which fit nested data well (YAML concise and commentable; JSON universal, zero-dependency, the interchange/agent format).

## Consequences

- `read_document` accepts `.yaml`/`.yml`/`.json`; a `.toml` file now raises `LoadError` ("unsupported input extension"). JSON stays dependency-free; YAML remains the optional `gedcom[yaml]` extra.
- `gedcom init` offers `-f yaml|json` (default `yaml`); the TOML template is gone.
- `schema`/`guide`/`--json` surfaces and the README advertise YAML and JSON only.
- Native `date`/`datetime` coercion is now described as a YAML feature (JSON has no native date type).
- The historical `.scratch/gedcom-cli/` PRD and issues are left as the record of the original (since-completed) decision; this ADR is the authoritative reversal.
