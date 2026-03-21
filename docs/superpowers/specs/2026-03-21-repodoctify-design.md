# RepoDoctify Design

## 1. Goal

`RepoDoctify` is a top-level skill product for turning an unfamiliar code repository into a structured learning docset that helps first-time readers:

- understand what the repository does
- build a correct mental model of the main chain
- lower the abstraction cost of hard mechanisms
- locate module ownership and support boundaries
- start developing new features and debugging problems faster

The product should support multiple reading targets without duplicating content generation logic:

- Markdown
- HTML
- Feishu

The same repository knowledge result must be shared across all output modes.

## 2. Product Positioning

`RepoDoctify` is not a Feishu tool and not a single-format doc generator.

It is a top-level repository knowledge product layer that:

1. analyzes a repository
2. plans a docset structure
3. composes a unified intermediate representation
4. renders that representation into one or more output formats

Feishu is only one renderer target. It is not the product identity.

## 3. User-Facing Commands

`RepoDoctify` exposes one top-level skill with four explicit subcommands plus one default no-argument behavior.

### 3.1 Default No-Argument Behavior

Default behavior must be equivalent to:

1. planning the output framework
2. generating the shared intermediate result
3. rendering the full Markdown docset

The default output should include:

- split Markdown docs
- a README-style aggregate overview
- a manifest
- a reusable intermediate-result cache

The default behavior must not:

- publish to Feishu
- require HTML rendering
- depend on `lark-mcp`
- write any result into the current repository by default

### 3.2 Explicit Subcommands

The skill should support these user-visible actions:

1. `规划输出框架`
   - produce the docset structure only
   - do not generate the final full content
2. `以 md 形式输出全部内容`
   - render the full Markdown docset from the shared intermediate result
   - if the intermediate result does not exist yet, create missing prerequisites automatically
3. `以 html 形式输出全部内容`
   - render the full HTML docset from the shared intermediate result
   - if the intermediate result does not exist yet, create missing prerequisites automatically
4. `以飞书形式输出全部内容`
   - publish the full docset to Feishu from the shared intermediate result
   - if the intermediate result does not exist yet, create missing prerequisites automatically

`规划输出框架` is the only command that intentionally stops before content rendering.

## 4. Hard Constraints

### 4.1 Shared Intermediate Result

Markdown, HTML, and Feishu outputs must share the same intermediate result.

The product must not allow three separate content generation paths that drift over time.

### 4.2 Non-Pollution Rule

By default, `RepoDoctify` must treat the target repository as read-only input.

It must not write any of the following into the current repository unless the user explicitly asks:

- planning artifacts
- intermediate representation files
- Markdown outputs
- HTML outputs
- README aggregate outputs
- publish records
- logs
- temporary render files

Default behavior must write all generated artifacts into a repository-external isolated workspace.

### 4.3 Feishu Dependency Rule

`lark-mcp` is not part of `RepoDoctify` itself.

If the user triggers the Feishu output command:

- and `lark-mcp` is available, continue
- and `lark-mcp` is not available, stop with a clear dependency message

Missing `lark-mcp` must never block default Markdown behavior or HTML behavior.

## 5. Internal Architecture

`RepoDoctify` should be structured as four internal stages:

1. `Analyzer`
2. `Planner`
3. `Composer`
4. `Renderers`

The canonical flow is:

`Repository -> Analyzer -> Planner -> Composer -> Docset IR -> Renderer`

### 5.1 Analyzer

Reads the repository as a knowledge source and extracts structured materials such as:

- repo identity and basic profile
- major directories and modules
- candidate main chains
- bridge-topic candidates
- tests and evidence sources
- boundaries and likely maintenance concerns
- existing docs and references

Analyzer output is structured material, not final narrative text.

### 5.2 Planner

Applies the repository knowledge framework and decides:

- which docs should exist
- each doc's role
- recommended reading routes
- which topics should become bridge docs
- which modules deserve deep dives
- how README aggregation should work

Planner output is `Docset Plan`.

### 5.3 Composer

Builds the shared intermediate representation from the `Docset Plan`.

This layer owns the actual repository knowledge content in a renderer-neutral form.

### 5.4 Renderers

Renderers consume the shared IR and produce:

- Markdown
- HTML
- Feishu
- README aggregate output

README is not a separate content generator. It is an aggregate view derived from the same IR.

## 6. Shared Intermediate Representation

`RepoDoctify` needs a formal intermediate model, referred to here as `Docset IR`.

The first version should contain at least these object types:

- `RepositoryProfile`
- `DocsetPlan`
- `DocumentSpec`
- `SectionNode`
- `CrossLinkMap`

### 6.1 `RepositoryProfile`

Captures repository-wide context, such as:

- repository path and public locator
- language or runtime hints
- primary audience
- source authority notes

### 6.2 `DocsetPlan`

Captures the planned docset structure:

- list of docs
- each doc role
- recommended reading routes
- README aggregation strategy

### 6.3 `DocumentSpec`

Captures a single document's identity and purpose:

- title
- role
- question answered
- target reader
- next-read suggestions

### 6.4 `SectionNode`

Captures renderer-neutral content units such as:

- paragraph
- numbered list
- comparison table
- code anchor
- mermaid block
- board placeholder
- callout or summary block

### 6.5 `CrossLinkMap`

Captures document-to-document references:

- homepage links
- next-read links
- reading-route links
- aggregate README links

## 7. Repository Knowledge Methodology Ownership

Repository-level knowledge methodology must belong to `RepoDoctify`, not to `feishu-knowledge-ops`.

That includes:

- the repository docset framework
- doc-type definitions
- bridge-doc selection rules
- module deep-dive split rules
- boundary-guide expectations
- development-guide expectations
- shared IR rules

This methodology is output-medium independent and therefore should not remain coupled to Feishu-specific skill assets.

## 8. Reference Set

`RepoDoctify` should own these references:

1. `repo-docset-framework.md`
   - repository docset methodology
2. `docset-ir.md`
   - intermediate representation model
3. `markdown-rendering-rules.md`
   - Markdown rendering rules
4. `html-rendering-rules.md`
   - HTML rendering rules
5. `feishu-rendering-handoff.md`
   - handoff contract from `RepoDoctify` IR into Feishu-specific rendering and publishing

## 9. Skill Responsibilities

### 9.1 `RepoDoctify`

Owns:

- top-level user interface
- command model
- repository docset methodology
- shared IR model
- Markdown rendering rules
- HTML rendering rules
- README aggregation rules
- repository-external output rules
- Feishu output handoff rules

### 9.2 `feishu-knowledge-ops`

Owns Feishu-specific backend concerns only:

- Feishu doc structure and block mapping
- Feishu table and chart expression details
- Feishu publishing flow
- in-place updates
- readback verification
- Feishu performance optimizations

### 9.3 `lark-mcp`

Remains an external dependency used only for Feishu output mode.

It is not part of `RepoDoctify` itself.

## 10. Output Isolation Model

All generated outputs should live in a repository-external workspace.

The workspace should be organized by run or task instance and should be able to store:

- `plan/`
- `ir/`
- `md/`
- `html/`
- `publish/`
- `logs/`

The current repository remains clean by default.

## 11. v1 Scope

`RepoDoctify v1` should include:

1. one top-level skill
2. the five core references listed above
3. a stable default no-argument Markdown path
4. a repository-external output model
5. a first usable shared IR definition
6. a Markdown renderer as the primary stable renderer
7. a basic HTML renderer
8. a Feishu handoff entry that delegates Feishu-specific work outward
9. explicit dependency messaging for missing `lark-mcp`

## 12. v1 Success Criteria

`RepoDoctify v1` is successful when:

- users only need to remember one top-level skill
- default no-argument behavior reliably produces a Markdown docset outside the current repo
- Markdown, HTML, and Feishu all conceptually depend on the same shared IR
- repository methodology is no longer coupled to Feishu-specific skill ownership
- Feishu output remains possible without redefining repository methodology there

## 13. Non-Goals for v1

The first version should not attempt to do all of the following:

- become a standalone CLI immediately
- support many more output targets beyond Markdown, HTML, and Feishu
- introduce a complex theming system
- add advanced semantic knowledge-graph reasoning layers
- embed `lark-mcp` as a built-in dependency
- write default outputs into the target repository

## 14. Implementation Order Recommendation

Recommended implementation order:

1. create the `RepoDoctify` skill shell
2. migrate repository methodology references into `RepoDoctify`
3. define `Docset IR`
4. implement the default Markdown path
5. add HTML rendering
6. add Feishu handoff behavior

This keeps the primary path stable first and treats HTML and Feishu as renderer extensions over the same core model.
