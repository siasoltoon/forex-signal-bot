# Large-File Hotspots

Use this list to avoid unsafe whole-file edits.

## High attention

- Market-data engines and provider orchestration.
- Analysis and signal engines.
- Modules with multiple architectural responsibilities.

## Required handling

For a hotspot:

1. Search the exact symbol first.
2. Read a focused range.
3. Read the relevant caller/callee boundary.
4. Apply the smallest safe patch.
5. Run targeted tests.
6. Run the broader suite before declaring the change verified.

If a hotspot repeatedly requires cross-cutting edits, propose a responsibility-based refactor before performing a large rewrite.
