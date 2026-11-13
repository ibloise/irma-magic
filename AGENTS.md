# AGENTS.md — IRMagic

## Project principles

IRMagic is a Python project providing utilities for CDC-IRMA execution and post-processing of bioinformatics results.

Prioritize correctness, simplicity, maintainability, reproducibility, and predictable behavior. Avoid unnecessary abstraction and premature generalization.

## Git workflow

- `main`: stable branch. Only tested and reviewed changes should be merged here.
- `develop`: integration and active development branch.
- `codex/<feat>`: branches for agentic development, created from `develop`. Use short, descriptive names such as `codex/fastq-pairing` or `codex/cli-packaging`.
- Never commit directly to `main` or `develop` during agentic development.
- Keep changes focused and avoid mixing unrelated features or refactors.
- Merge agentic branches into `develop` through pull requests. Promote `develop` to `main` only after validation and review.
- Do not merge, release, or publish packages without explicit authorization.
- Use conventional commits

## Architecture and code quality

- Follow Python conventions (PEP 8) and prefer readable, idiomatic code.
- Apply object-oriented programming pragmatically. Use classes when they represent meaningful entities, encapsulate state, or simplify responsibilities.
- Apply SOLID principles where beneficial, not mechanically.
- Prefer composition over inheritance when it reduces coupling and complexity.
- Avoid unnecessary design patterns, layers, interfaces, factories, and speculative extensibility.
- Keep functions and classes cohesive, with clear responsibilities.
- Use type hints and explicit exceptions where they improve clarity.
- Preserve existing public interfaces unless a change has been explicitly approved.

## Dependencies and external tools

- Do not add, replace, or upgrade third-party dependencies without explicit authorization.
- Never invent packages, APIs, command-line options, or external tool capabilities.
- Verify external interfaces against actual code, installed tools, or authoritative documentation.
- Prefer the Python standard library when sufficient.
- Do not introduce frameworks, infrastructure, containers, or external services without a demonstrated need and authorization.
- Keep CDC-IRMA integration separate from IRMagic's own Python functionality.

## Correctness and bioinformatics

- Never silently discard, mismatch, or overwrite biological data.
- Validate sample identifiers, FASTQ pairing, input formats, and output paths.
- Fail explicitly on invalid or ambiguous inputs.
- Do not silently ignore failed subprocess executions.
- Ensure deterministic behavior whenever possible.
- Preserve traceability between input samples, executed commands, and generated outputs.
- Do not claim biological or clinical validation without supporting evidence.

## Testing and validation

- Add or update tests for new functionality and bug fixes.
- Include relevant edge cases, especially malformed inputs, incomplete paired reads, duplicate identifiers, and execution failures.
- Prefer small, deterministic tests using synthetic datasets.
- Avoid requiring large reference databases or a complete CDC-IRMA installation for unit tests.
- Run relevant tests and checks before proposing integration.
- Clearly distinguish tests executed successfully from checks not performed.
- Never report unverified behavior as tested.

## Documentation and changes

- Keep documentation concise, accurate, and synchronized with implementation.
- Document user-facing changes and important behavioral decisions.
- Do not create unnecessary documentation or architectural decision records for trivial changes.
- Avoid unrelated modifications and cosmetic refactors.
- Do not remove functionality or change established behavior without justification and authorization.
- Identify uncertainties and assumptions explicitly rather than guessing.

## Agent operating rules

Before implementing:

1. Inspect the relevant code and existing project conventions.
2. Identify the scope, dependencies, and potential compatibility implications.
3. Prefer the smallest solution that correctly addresses the requirement.

During implementation:

1. Stay within the agreed scope.
2. Avoid introducing dependencies or significant architectural changes without approval.
3. Add appropriate tests and maintain existing behavior unless changes are intentional.

After implementation:

1. Summarize the changes made.
2. Report tests executed and their results.
3. Identify remaining limitations, risks, and unverified assumptions.
4. Leave integration, releases, and publication decisions to the maintainer.

**Guiding principle:** Build the simplest correct solution for the current requirements, while keeping the code understandable and maintainable. Do not engineer for hypothetical future needs.
