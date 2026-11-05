# Searchable public portfolio

Make the existing public catalogue discoverable from its current homepage. Keep the four existing featured links and all deep URLs. Use the current catalogue of 764 public sample pages, checked against the repository tree. Describe them as demonstrations, never client deployments.

Use static HTML, a small browser module and a same-origin JSON catalogue. Search Polish words without requiring accents, combine query words, filter by project category, and show results in batches of 24. The page must remain useful when JavaScript or the catalogue request fails. Render metadata as text and accept only canonical portfolio URLs.

Alternatives considered: keeping only four links leaves the catalogue hidden; adding a hosted search service introduces an account and ongoing cost. Static filtering fits the existing GitHub Pages site and needs neither. This implementation choice was delegated by the user's request to choose and deploy an improvement.

Accept when search, categories, empty results, shared query URLs, existing links and phone layout work. No sales records, contact details, credentials or private correspondence belong in the public catalogue.
