# RepoDoctify

`RepoDoctify` is a top-level repository knowledge product that turns an unfamiliar
code repository into a structured learning docset.

The repository currently contains:

- the product design spec
- the v1 implementation plan
- the top-level skill contract
- reference documents for repository methodology and rendering rules
- a small Python helper package for shared IR, workspace isolation, repo analysis, planning, composition, and renderers

## Intended Default Behavior

With no explicit subcommand, `RepoDoctify` should behave as:

1. plan the docset structure
2. generate shared intermediate results
3. render the full Markdown docset

The default path should also generate:

- a README-style aggregate overview
- a manifest

All generated artifacts should live outside the analyzed repository by default.

## Runtime Surface

The current v1 helper flow is:

1. analyze the target repository
2. build a default docset plan
3. compose a shared IR
4. render Markdown or HTML, or prepare a Feishu handoff

The main Python entrypoint is `repodoctify.run_repodoctify(...)`.

It always writes into an external workspace with these subdirectories:

- `plan/`
- `ir/`
- `md/`
- `html/`
- `publish/`
- `logs/`

## Local Development

Run tests with:

```bash
pytest -v
```

Install the local skill copy with:

```bash
python3 scripts/install_local_skill.py
```

## Output Targets

`RepoDoctify` is designed to support:

- Markdown
- HTML
- Feishu

Feishu output is optional and depends on an external `lark-mcp` installation.

If `lark-mcp` is unavailable, the runtime raises a clear dependency error instead
of blocking Markdown or HTML output.
