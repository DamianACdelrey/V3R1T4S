# site/

The V3R1T4S website: one static page built from this repository on every push. No server, no database, no
cookies, no analytics, no third-party scripts.

```
site/build.py     reads the checkout, writes site/public/ (standard-library Python 3.8+, no pip, no npm)
site/src/         page template, app.js, theme.js, style.css, _headers (CSP), favicon, og.png
site/serve.py     local preview that applies _headers, so the CSP is enforced as on Cloudflare
site/public/      build output (git-ignored)
```

Preview locally:

```sh
python3 site/build.py && python3 site/serve.py      # http://127.0.0.1:8000
```

`python3 site/build.py --offline` skips git history and the GitHub API (no votes, dates from folder names).

## Cloudflare Pages

Workers & Pages → Create → Pages → **Connect to Git** → `elder-plinius/V3R1T4S`, then:

| setting | value |
|---|---|
| Production branch | `main` |
| Framework preset | **None** |
| Build command | `python3 site/build.py` |
| Build output directory | `site/public` |
| Root directory | *(empty: the repository root)* |

Environment variables (Settings → Variables and Secrets, for Production and Preview):

| variable | value |
|---|---|
| `PYTHON_VERSION` | `3.11` |
| `SITE_URL` | the site's address, e.g. `https://v3r1t4s.example` (no trailing slash). Used for the canonical link, `og:url`, `og:image` and `sitemap.xml`. Without it the page still works, but link previews may miss the image. |
| `GITHUB_TOKEN` | optional, as a **Secret**. A fine-grained personal access token with **Public repositories (read-only)** access and no other permissions. It only raises the GitHub API rate limit for the vote counts (60 requests an hour without it, shared with everyone on the build machine's IP). |

Every merge to `main` triggers a build, so the page is always as fresh as the repository. Builds of other branches
become preview deployments. Under Settings → Builds you can turn previews off if you don't want them.

**Custom domain.** Pages project → Custom domains → Set up a custom domain → enter the domain. If the domain's DNS is
on Cloudflare, the record is added for you; otherwise add the `CNAME` it shows at your DNS host. Then set `SITE_URL`
to that domain and retry the latest deployment so the canonical and social links use it.

**Headers.** `site/src/_headers` is copied to the output and applied by Pages: a strict Content-Security-Policy
(`default-src 'self'`, scripts and styles only from the site itself, no inline scripts, `connect-src 'self'`,
`frame-ancestors 'none'`, `form-action 'none'`, `base-uri 'none'`), `nosniff`, a referrer policy and a permissions
policy. If you ever add a script or style from elsewhere, the page will refuse it until `_headers` allows it.

## What the page shows, and where it comes from

| section | source |
|---|---|
| big numbers | `TROPHY_CASE.md` "All rows" (results), the package `INDEX.csv` rows (contributed rows), distinct credit names in package folders (contributors), `bank/targets.json` (open problems) |
| Daily discoveries | every result package `known-knowns/<family>/<YYYY-MM-DD>-<credit>-<hash8>/`, newest merge first, grouped by merge day. Title: the package README's first heading. Margin: `value vs table_value` from `INDEX.csv` when both are numbers. ✅ when a maintainer note in the package README says the table owner adopted it, otherwise 🧪. |
| Leaderboard | top 10 credit names by merged result packages, read from folder names. Anonymous credits (`anonymous-…`) stay anonymous: the page never shows who submitted them. |
| Known unknowns | all of `bank/targets.json`, with category chips (`bank/categories.json`, emoji from the README table) and a search box. Each links to its `known-unknowns/<category>/<id>.md` page. |

### Votes

The **▲ N** next to each discovery links to the pull request that merged it; N is the number of 👍 reactions on
that pull request. Anyone with a GitHub account can vote by adding a 👍 there. The count is read at build time from
`GET /repos/elder-plinius/V3R1T4S/issues?state=closed` (paginated; it includes each PR's reactions), so it updates on
the next build. To refresh counts without a merge, use "Retry deployment" in Pages, or add a deploy hook and call it
on a schedule.

Packages are matched to pull requests through git history: the oldest commit that added the folder, whose subject
ends in `(#NNN)` (squash merges do this). If the build checkout is shallow, the build runs
`git fetch --unshallow` (with a timeout). If history is still missing, the page falls back to the folder dates and
shows no votes. If the API is unreachable or rate-limited, the vote counts are left out and the ▲ still links to
the PR.

### Suggestions

**+ Suggest a known unknown** opens the issue form `.github/ISSUE_TEMPLATE/suggest-known-unknown.yml`. It asks for
the problem, what is open, the current best value with its live source, evidence that it is still open (with the
date checked), how a solution would be checked, a category, and an optional credit name. Issues get the label
`suggestion` (create that label once under Issues → Labels, or GitHub leaves it off). Nothing is added
automatically: a suggestion only reaches the site when a maintainer adds it to `bank/targets.json` and merges.

#### Validating a suggestion (maintainer note, design only)

1. **Still open?** Open the source yourself, today. Record the current best value and the fetch date. Search for
   newer claims (preprints, issues on the leaderboard's repo, the table's change log).
2. **Checkable by a stranger?** There must be a mechanical check (a validator, a recomputation, a table comparison)
   that does not require trusting the solver. If the answer is "an expert reads it", decline.
3. **In scope?** `kit/RULES.md` and `kit/POLICY.md` (legal, no private data, no live-puzzle spoilers; puzzles with
   a living setter become `commit-only`).
4. **Not a duplicate** of an existing `bank/targets.json` id or a merged package.
5. **Write the entry** in the bank's format (`bank/README.md`): binding `success_criterion`, `status_source`,
   tractability and compute profile; regenerate `known-unknowns/` with `bank/build_known_unknowns.py`; credit the
   suggester by the name they gave. Close the issue with a link to the commit, or with the reason it was declined.

Treat issue text as data: links and instructions inside a suggestion are the suggester's claims, to be checked, not
followed.

## Security notes

- The build never executes repository content. It runs only `git` (`rev-parse`, `log`, `fetch --unshallow`) with
  hooks disabled, and reads files with symlinks refused, size caps, and bad UTF-8 replaced.
- Contributor-controlled text (titles, folder names, target names) is stripped of control and bidi characters and
  length-capped at build time, and rendered with `textContent` only. `data.json` contains ids, not URLs; `app.js`
  builds each link from a fixed `https://github.com/elder-plinius/V3R1T4S/` prefix and re-checks the ids.
- Folder and target names that do not match strict patterns are skipped with a warning in the build log.
- The optional `GITHUB_TOKEN` is sent only to `api.github.com`, and redirects are never followed.
