# RepoDoctify v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable `RepoDoctify` skill repository so a user can turn a code repository into a structured Markdown docset by default, with shared-IR-based HTML and Feishu handoff paths, while keeping all generated artifacts outside the target repo.

**Architecture:** `RepoDoctify` is a top-level skill plus a small Python helper library. The skill owns repository-docset methodology, command semantics, output-isolation rules, and renderer contracts. Python helpers own the shared IR model, workspace isolation, Markdown / HTML rendering, and Feishu dependency handoff. Feishu-specific publication remains delegated to `feishu-knowledge-ops`.

**Tech Stack:** Skill repo layout, Markdown reference docs, Python 3.11, `dataclasses`, `pathlib`, `json`, `html`, `pytest`

---

## File Structure

### Repo Source Files

- Create: `SKILL.md`
  - top-level `RepoDoctify` skill entrypoint
- Create: `README.md`
  - repository overview and local development notes
- Create: `pyproject.toml`
  - minimal Python project metadata and pytest configuration
- Create: `repodoctify/__init__.py`
  - package marker and public exports
- Create: `repodoctify/models.py`
  - shared IR dataclasses and type helpers
- Create: `repodoctify/workspace.py`
  - repository-external output workspace resolution and path safety checks
- Create: `repodoctify/markdown_renderer.py`
  - Markdown docset and README aggregate rendering
- Create: `repodoctify/html_renderer.py`
  - HTML docset rendering from shared IR
- Create: `repodoctify/feishu_handoff.py`
  - dependency detection and handoff metadata for Feishu output

### Reference Files

- Create: `references/repo-docset-framework.md`
  - repository-docset methodology migrated out of `feishu-knowledge-ops`
- Create: `references/docset-ir.md`
  - formal IR contract
- Create: `references/markdown-rendering-rules.md`
  - Markdown output rules and README aggregate rules
- Create: `references/html-rendering-rules.md`
  - HTML output rules
- Create: `references/feishu-rendering-handoff.md`
  - renderer contract and delegation to `feishu-knowledge-ops`

### Tests

- Create: `tests/test_skill_contract.py`
  - validates skill contract, default behavior, subcommands, and dependency messaging
- Create: `tests/test_workspace.py`
  - validates repository-external output behavior
- Create: `tests/test_markdown_renderer.py`
  - validates split Markdown output and README aggregate output from the same IR
- Create: `tests/test_html_renderer.py`
  - validates HTML output structure from the same IR
- Create: `tests/test_feishu_handoff.py`
  - validates `lark-mcp` dependency checks and handoff behavior

### Optional Local Integration Helper

- Create: `scripts/install_local_skill.py`
  - copies or syncs this repo into the local Codex skill directory for manual testing

## Chunk 1: Skill Shell And Reference Ownership

### Task 1: Bootstrap the repo as a testable skill package

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `repodoctify/__init__.py`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing bootstrap test**

```python
from pathlib import Path


def test_repo_has_basic_project_files():
    assert Path("pyproject.toml").exists()
    assert Path("README.md").exists()
    assert Path("repodoctify/__init__.py").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_contract.py::test_repo_has_basic_project_files -v`
Expected: FAIL with missing file assertions

- [ ] **Step 3: Write minimal project files**

```toml
[project]
name = "repodoctify"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
__all__ = []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_contract.py::test_repo_has_basic_project_files -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md repodoctify/__init__.py tests/test_skill_contract.py
git commit -m "chore: bootstrap repodoctify skill repository"
```

### Task 2: Author the top-level skill contract

**Files:**
- Create: `SKILL.md`
- Modify: `README.md`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing skill-contract test**

```python
from pathlib import Path


def test_skill_declares_default_behavior_and_subcommands():
    text = Path("SKILL.md").read_text(encoding="utf-8")
    assert "RepoDoctify" in text
    assert "默认" in text
    assert "规划输出框架" in text
    assert "以 md 形式输出全部内容" in text
    assert "以 html 形式输出全部内容" in text
    assert "以飞书形式输出全部内容" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_contract.py::test_skill_declares_default_behavior_and_subcommands -v`
Expected: FAIL because `SKILL.md` does not exist yet

- [ ] **Step 3: Write minimal `SKILL.md` and README contract**

```markdown
---
name: RepoDoctify
description: Use when the user wants to turn a source repository into a structured learning docset with Markdown, HTML, or Feishu outputs.
---
```

Add sections covering:

- product purpose
- default no-argument behavior
- four explicit subcommands
- repository-external output rule
- `lark-mcp` dependency note for Feishu output

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_contract.py::test_skill_declares_default_behavior_and_subcommands -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add SKILL.md README.md tests/test_skill_contract.py
git commit -m "feat: define repodoctify top-level skill contract"
```

### Task 3: Migrate repository-docset methodology into RepoDoctify references

**Files:**
- Create: `references/repo-docset-framework.md`
- Create: `references/docset-ir.md`
- Create: `references/markdown-rendering-rules.md`
- Create: `references/html-rendering-rules.md`
- Create: `references/feishu-rendering-handoff.md`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing reference-ownership test**

```python
from pathlib import Path


def test_repo_owns_reference_set():
    for rel in [
        "references/repo-docset-framework.md",
        "references/docset-ir.md",
        "references/markdown-rendering-rules.md",
        "references/html-rendering-rules.md",
        "references/feishu-rendering-handoff.md",
    ]:
        assert Path(rel).exists(), rel
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_contract.py::test_repo_owns_reference_set -v`
Expected: FAIL with missing reference file assertions

- [ ] **Step 3: Write the five reference documents**

Use the approved spec as source of truth. Ensure:

- `repo-docset-framework.md` owns repository-docset methodology
- `docset-ir.md` defines `RepositoryProfile`, `DocsetPlan`, `DocumentSpec`, `SectionNode`, `CrossLinkMap`
- `markdown-rendering-rules.md` defines split-doc and README aggregation rules
- `html-rendering-rules.md` defines navigation and HTML structure rules
- `feishu-rendering-handoff.md` defines delegation to `feishu-knowledge-ops`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skill_contract.py::test_repo_owns_reference_set -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add references tests/test_skill_contract.py
git commit -m "feat: add repodoctify reference set"
```

## Chunk 2: Shared IR And Repository-External Output

### Task 4: Implement the shared IR model

**Files:**
- Create: `repodoctify/models.py`
- Modify: `references/docset-ir.md`
- Test: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Write the failing IR-model test**

```python
from repodoctify.models import DocumentSpec, RepositoryProfile, SectionNode


def test_ir_models_capture_basic_docset_structure():
    profile = RepositoryProfile(repo_label="demo", source_path="/tmp/demo")
    section = SectionNode(kind="paragraph", title="Intro", body=["hello"])
    doc = DocumentSpec(doc_id="overview", title="Overview", role="overview", sections=[section])
    assert profile.repo_label == "demo"
    assert doc.sections[0].kind == "paragraph"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown_renderer.py::test_ir_models_capture_basic_docset_structure -v`
Expected: FAIL with import error or missing model definitions

- [ ] **Step 3: Write minimal IR dataclasses**

Implement dataclasses for:

- `RepositoryProfile`
- `DocsetPlan` with doc list, doc roles, reading routes, and README aggregation strategy
- `DocumentSpec`
- `SectionNode`
- `CrossLinkMap` with homepage links, next-read links, reading-route links, and aggregate README links

Update `references/docset-ir.md` in the same task so it documents:

- each dataclass
- each v1 field group
- the intent of the shared IR contract
- how renderer-neutral links and README aggregation are represented

Keep v1 fields minimal and aligned with the spec.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown_renderer.py::test_ir_models_capture_basic_docset_structure -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repodoctify/models.py references/docset-ir.md tests/test_markdown_renderer.py
git commit -m "feat: add shared docset ir models"
```

### Task 5: Implement repository-external workspace resolution

**Files:**
- Create: `repodoctify/workspace.py`
- Test: `tests/test_workspace.py`

- [ ] **Step 1: Write the failing workspace-isolation tests**

```python
from pathlib import Path

from repodoctify.workspace import ensure_external_workspace


def test_workspace_defaults_outside_target_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = ensure_external_workspace(repo)
    assert repo not in workspace.parents
    assert workspace != repo
    for name in ["plan", "ir", "md", "html", "publish", "logs"]:
        assert (workspace / name).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workspace.py::test_workspace_defaults_outside_target_repo -v`
Expected: FAIL with import error or missing function

- [ ] **Step 3: Write minimal workspace helper**

Implement:

- default external workspace root resolution
- per-run directory creation
- path-safety checks that reject repo-internal default outputs
- required subdirectories: `plan/`, `ir/`, `md/`, `html/`, `publish/`, `logs/`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workspace.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repodoctify/workspace.py tests/test_workspace.py
git commit -m "feat: enforce repository-external output workspace"
```

## Chunk 3: Markdown And HTML Rendering

### Task 6: Implement Markdown docset rendering and README aggregation

**Files:**
- Create: `repodoctify/markdown_renderer.py`
- Test: `tests/test_markdown_renderer.py`

- [ ] **Step 1: Write the failing Markdown-renderer tests**

```python
from repodoctify.markdown_renderer import render_markdown_docset
from repodoctify.models import DocumentSpec, RepositoryProfile, SectionNode


def test_markdown_renderer_emits_split_docs_and_readme():
    docs = [
        DocumentSpec(
            doc_id="overview",
            title="Overview",
            role="overview",
            sections=[SectionNode(kind="paragraph", title="Intro", body=["hello"])],
        )
    ]
    result = render_markdown_docset(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        docs,
    )
    assert "README.md" in result.files
    assert "overview.md" in result.files
    assert "manifest.json" in result.files
    assert "Overview" in result.files["README.md"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown_renderer.py::test_markdown_renderer_emits_split_docs_and_readme -v`
Expected: FAIL with missing renderer implementation

- [ ] **Step 3: Write minimal Markdown renderer**

Implement:

- split-doc Markdown rendering
- README aggregate generation from the same IR
- stable file naming
- manifest generation for the default Markdown path
- manifest-friendly output object

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repodoctify/markdown_renderer.py tests/test_markdown_renderer.py
git commit -m "feat: render markdown docsets from shared ir"
```

### Task 7: Implement HTML rendering from the same IR

**Files:**
- Create: `repodoctify/html_renderer.py`
- Test: `tests/test_html_renderer.py`

- [ ] **Step 1: Write the failing HTML-renderer tests**

```python
from repodoctify.html_renderer import render_html_docset
from repodoctify.models import DocumentSpec, RepositoryProfile, SectionNode


def test_html_renderer_emits_index_and_doc_pages():
    docs = [
        DocumentSpec(
            doc_id="overview",
            title="Overview",
            role="overview",
            sections=[SectionNode(kind="paragraph", title="Intro", body=["hello"])],
        )
    ]
    result = render_html_docset(
        RepositoryProfile(repo_label="demo", source_path="/tmp/demo"),
        docs,
    )
    assert "index.html" in result.files
    assert "overview.html" in result.files
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_html_renderer.py::test_html_renderer_emits_index_and_doc_pages -v`
Expected: FAIL with missing renderer implementation

- [ ] **Step 3: Write minimal HTML renderer**

Implement:

- index page generation
- one page per document
- basic navigation links
- safe HTML escaping and code-block rendering

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_html_renderer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repodoctify/html_renderer.py tests/test_html_renderer.py
git commit -m "feat: render html docsets from shared ir"
```

## Chunk 4: Feishu Handoff And Local Integration

### Task 8: Implement Feishu handoff dependency checks

**Files:**
- Create: `repodoctify/feishu_handoff.py`
- Test: `tests/test_feishu_handoff.py`

- [ ] **Step 1: Write the failing Feishu-handoff tests**

```python
from repodoctify.feishu_handoff import ensure_feishu_dependencies


def test_feishu_handoff_reports_missing_lark_mcp():
    result = ensure_feishu_dependencies(installed_tools=set())
    assert result.ok is False
    assert "lark-mcp" in result.message
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feishu_handoff.py::test_feishu_handoff_reports_missing_lark_mcp -v`
Expected: FAIL with missing module or function

- [ ] **Step 3: Write minimal handoff helper**

Implement:

- `lark-mcp` availability check
- explicit failure message
- handoff payload shape for later integration with `feishu-knowledge-ops`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feishu_handoff.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add repodoctify/feishu_handoff.py tests/test_feishu_handoff.py
git commit -m "feat: add feishu handoff dependency checks"
```

### Task 9: Add a local install helper and full regression suite

**Files:**
- Create: `scripts/install_local_skill.py`
- Modify: `README.md`
- Modify: `tests/test_skill_contract.py`
- Test: `tests/test_skill_contract.py`
- Test: `tests/test_workspace.py`
- Test: `tests/test_markdown_renderer.py`
- Test: `tests/test_html_renderer.py`
- Test: `tests/test_feishu_handoff.py`

- [ ] **Step 1: Write the failing installation-smoke test**

```python
from pathlib import Path


def test_local_install_helper_exists():
    assert Path("scripts/install_local_skill.py").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skill_contract.py::test_local_install_helper_exists -v`
Expected: FAIL because the helper does not exist yet

- [ ] **Step 3: Write minimal install helper and update README**

Implement a local developer helper that:

- copies or syncs the skill repo into the local Codex skills directory
- leaves source-of-truth files in this repo
- documents manual verification steps

- [ ] **Step 4: Run the full regression suite**

Run: `pytest -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/install_local_skill.py README.md tests
git commit -m "chore: add local install flow and regression coverage"
```
