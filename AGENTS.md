# AGENTS.md — guide for contributors and coding agents

A short orientation for humans and AI coding agents (GitHub Copilot, Claude,
Cursor, …) working in **statewave-examples** — runnable quickstarts (LangChain,
CrewAI, AutoGen, …), the support-agent eval suites, and the support-workflow
benchmark.

## Setup, build, test

See the [README](README.md); setup is per-example. The eval suites under
`eval-support-agent/` run with `pytest` against a live Statewave instance, e.g.
`pytest --collect-only eval-support-agent/` to list tests.

## Conventions

- **This repo is the *source* of the published proof figures.** The eval
  assertion/test counts (`eval-support-agent/`) and the support-workflow
  benchmark score (`benchmark-support-agent/`) are mirrored across the docs and
  the marketing site. If you add/remove a test or assertion, the figures in
  `statewave-docs` must be updated — a release-time check
  (`check-proof-figures.py`) fails on drift.
- **Keep claims accurate and modest;** every figure must trace to a
  reproducible source in this repo.

## Pull requests

Keep PRs focused, make sure the eval suites still pass, and update the mirrored
figures in `statewave-docs` if your change moves a count.

## Optional: give your agent memory of this repo (with Statewave)

This project dogfoods Statewave. The easiest way to give your assistant a
queryable project brain for this repo is the **Statewave IDE Companion**
extension for **VS Code / Cursor** (publisher `statewavedev`) — install it from
your editor's extensions marketplace. It exposes your workspace, docs, git
state, and structure to Copilot / Cursor / Claude over MCP and **registers the
MCP server for you** (no manual config); it just needs a Statewave server to
talk to (a one-file `docker compose up`). See the
[extension README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/vscode-extension/README.md).

Prefer to wire it up by hand, or use another MCP client? Run the
[Statewave MCP server](https://github.com/smaramwbc/statewave-docs/blob/main/connectors/mcp.md)
(`@statewavedev/mcp-server`) directly and query subject `repo:smaramwbc/statewave-examples`.
