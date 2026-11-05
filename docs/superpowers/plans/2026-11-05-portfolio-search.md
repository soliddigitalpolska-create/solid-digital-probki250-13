# Portfolio Search Implementation Plan

**Goal:** Let visitors find relevant public demonstrations from the current homepage.

**Architecture:** Static homepage, browser search module, public JSON data. Keep existing deep links and the four featured examples. No service, account or dependency.

**Tech Stack:** HTML, CSS, browser JavaScript, Node built-in test runner.

**Spec:** `docs/superpowers/specs/2026-11-05-portfolio-search-design.md`

## Global Constraints

- 764 public sample pages, checked against the repository tree.
- All existing deep URLs and the four existing featured links remain valid.
- Metadata is rendered as text; only canonical portfolio URLs are accepted.
- Public data only. No sales records or correspondence.

## Review Focus

- Polish letters and mixed-case queries must match.
- Multiple words and category filters must combine correctly.
- External, duplicate and traversal URLs must be rejected.
- Invalid shared filter parameters must fall back safely.
- A failed request or disabled JavaScript must preserve the featured links.

## Task 1: Catalogue search and homepage

Files: `assets/catalog-search.mjs`, `assets/portfolio-catalog.json`, `index.html`, `test/catalog-search.test.mjs`.

- [ ] Write and run behaviour tests for normalization, combined search, category filtering, URL validation and shared filters; observe failures with stub functions.
- [ ] Implement the search functions and accessible, responsive homepage. Derive data only from catalogue entries with existing public paths.
- [ ] Run `node --test test/catalog-search.test.mjs` and `node --check assets/catalog-search.mjs`.
- [ ] Check the desktop and phone views, accent-free search, empty results, category selection and existing featured links in a browser.
- [ ] Review the final diff, publish the tested commit, verify the live homepage and a deep sample.
