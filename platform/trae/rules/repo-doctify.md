# RepoDoctify

Use `RepoDoctify` when you need to turn a code repository into a structured
learning docset for first-time readers, maintainers, and feature developers.

Preferred commands:

- `$repo-doctify`
- `$repo-doctify plan`
- `$repo-doctify md`
- `$repo-doctify html`
- `$repo-doctify feishu`

Default behavior:

1. Plan the output framework.
2. Generate the shared intermediate result.
3. Prepare the Markdown prompt bundle.
4. Let the model generate the final Markdown docset from that bundle.

Keep generated artifacts outside the analyzed repository by default.
