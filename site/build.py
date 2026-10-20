#!/usr/bin/env python3
"""Build the V3R1T4S static site into site/public/ from this repository checkout.

    python3 site/build.py [--out site/public] [--offline]

Standard library only, Python 3.8+. Cloudflare Pages runs it on every push to main (see site/README.md).

Everything shown on the page is derived from the checkout at build time:
  - counts: TROPHY_CASE.md "All rows", package INDEX.csv files, bank/targets.json;
  - daily discoveries: result packages known-knowns/<family>/<YYYY-MM-DD>-<credit>-<hash8>/, newest merge first,
    each mapped to its pull request through git history (squash commits end in "(#NNN)");
  - leaderboard: merged result packages per credit name, the name in the folder (anonymous credits stay anonymous);
  - votes: thumbs-up reactions on each pull request, read from the public GitHub API (optional GITHUB_TOKEN);
  - known unknowns: every target in bank/targets.json.

Repository content is untrusted input (contributors write package READMEs, INDEX.csv files and folder names):
  - nothing from the repository is executed or imported; the only programs run are git (log, rev-parse, fetch);
  - symlinks are never followed, files are size-capped, bad UTF-8 is replaced, control and bidi characters are
    stripped, every string is length-capped;
  - names that become URL path segments must match strict patterns, otherwise the item is skipped;
  - from INDEX.csv only the value and table_value columns are used, and only when both parse as numbers (so a
    formula such as =HYPERLINK(...) is never shown); the page never exports CSV;
  - data.json carries ids, never URLs: app.js builds every link from fixed github.com/elder-plinius/V3R1T4S
    prefixes and re-checks the ids, and renders text with textContent only.
"""
import argparse
import csv
import datetime
import html
import http.client
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src")
OWNER_REPO = "elder-plinius/V3R1T4S"
GH = "https://github.com/" + OWNER_REPO
API = "https://api.github.com/repos/" + OWNER_REPO

# ------------------------------------------------------------------ limits
MAX_MD = 512 * 1024          # a README or TROPHY_CASE.md
MAX_CSV = 512 * 1024         # one INDEX.csv
MAX_JSON = 16 * 1024 * 1024  # bank/targets.json (1.7 MB today)
MAX_ROWS = 500               # INDEX.csv rows read per package
MAX_PACKAGES = 20000
MAX_TARGETS = 20000
MAX_API_PAGES = 60           # 100 issues per page
MAX_API_BYTES = 16 * 1024 * 1024
API_TIMEOUT = 20
GIT_TIMEOUT = 120

# ------------------------------------------------------------------ name patterns (anything else is skipped)
RE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")                     # family, category, target ids
RE_PKG = re.compile(r"^(\d{4}-\d{2}-\d{2})-([A-Za-z0-9][A-Za-z0-9_.-]{0,63})-([0-9a-f]{8})$")
RE_PR = re.compile(r"\(#(\d{1,7})\)\s*$")

warnings = []


def warn(msg):
    warnings.append(msg)
    print("warn:", msg, file=sys.stderr)


class Unsafe(Exception):
    pass


# ------------------------------------------------------------------ safe file access
def _lstat_chain(rel):
    """lstat every component of rel below REPO; refuse symlinks, '..', empty and NUL parts."""
    parts = rel.split("/")
    cur = REPO
    st = None
    for p in parts:
        if p in ("", ".", "..") or "\x00" in p or "\\" in p:
            raise Unsafe("bad path %r" % rel)
        cur = os.path.join(cur, p)
        st = os.lstat(cur)
        if stat.S_ISLNK(st.st_mode):
            raise Unsafe("symlink %s" % rel)
    return cur, st


def read_bytes(rel, cap):
    path, st = _lstat_chain(rel)
    if not stat.S_ISREG(st.st_mode):
        raise Unsafe("not a regular file: %s" % rel)
    if st.st_size > cap:
        raise Unsafe("too big (%d bytes): %s" % (st.st_size, rel))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Unsafe("not a regular file: %s" % rel)
        with os.fdopen(fd, "rb") as f:
            fd = None
            data = f.read(cap + 1)
    finally:
        if fd is not None:
            os.close(fd)
    if len(data) > cap:
        raise Unsafe("too big: %s" % rel)
    return data


def read_text(rel, cap=MAX_MD):
    return read_bytes(rel, cap).decode("utf-8", "replace").replace("\r\n", "\n").replace("\x00", "")


def try_text(rel, cap=MAX_MD):
    try:
        return read_text(rel, cap)
    except (OSError, Unsafe) as e:
        warn("skip %s: %s" % (rel, e))
        return None


def read_json(rel, cap=MAX_JSON):
    try:
        return json.loads(read_text(rel, cap))
    except (OSError, Unsafe, ValueError, RecursionError) as e:
        warn("skip %s: %s" % (rel, e))
        return None


def is_file(rel):
    try:
        return stat.S_ISREG(_lstat_chain(rel)[1].st_mode)
    except (OSError, Unsafe):
        return False


def subdirs(rel):
    """Real (non-symlink) subdirectory names of rel, sorted."""
    try:
        path, st = _lstat_chain(rel)
        if not stat.S_ISDIR(st.st_mode):
            return []
        with os.scandir(path) as it:
            return sorted(e.name for e in it if e.is_dir(follow_symlinks=False))
    except (OSError, Unsafe) as e:
        warn("skip dir %s: %s" % (rel, e))
        return []


def files_in(rel):
    try:
        path, st = _lstat_chain(rel)
        if not stat.S_ISDIR(st.st_mode):
            return []
        with os.scandir(path) as it:
            return sorted(e.name for e in it if e.is_file(follow_symlinks=False))
    except (OSError, Unsafe):
        return []


# ------------------------------------------------------------------ text cleaning
# C0/C1 controls, zero-width and bidi controls, BOM, interlinear annotation, specials
_CTRL = re.compile("[\x00-\x1f\x7f-\x9f­؜ᅟᅠ᠎​-‏ -‮"
                   "⁠-⁯ㅤ︀-︎﻿￰-￻\U000e0000-\U000e007f]")


def clean(s, n):
    """Untrusted text -> one line, no control/bidi characters, at most n characters."""
    s = _CTRL.sub(" ", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def strip_md(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"</?[A-Za-z][^>]*>", "", s)
    s = s.replace("**", "").replace("`", "").replace("\\|", "|")
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)\*(?!\w)", r"\1", s)
    return s


_EMOJI_OK = re.compile("^[©®‼-㊙\U0001f000-\U0001faff️‍]{1,8}$")


def emoji_ok(e):
    return e if e and _EMOJI_OK.match(e) else None


# ------------------------------------------------------------------ numbers and margins
_NUM = re.compile(r"^[+\-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def to_num(s):
    s = str(s).strip().replace("−", "-").replace(",", "").replace(" ", "")
    if len(s) > 80 or not _NUM.match(s):
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def margin(value, table):
    """'50 vs 52' from INDEX.csv value and table_value: verbatim when both are short, otherwise rounded to the
    fewest decimals (or significant digits, for huge numbers) that still show the difference."""
    v, t = to_num(value), to_num(table)
    if v is None or t is None or v == t:
        return None
    rv, rt = (str(x).strip().replace("−", "-") for x in (value, table))
    if len(rv) <= 12 and len(rt) <= 12:
        return "%s vs %s" % (rv, rt)
    if max(abs(v), abs(t)) < 1e12:
        for d in range(0, 16):
            a, b = "{:.{}f}".format(v, d), "{:.{}f}".format(t, d)
            if a != b:
                return "%s vs %s" % (a, b)
        return None
    for sig in range(3, 18):
        a, b = "{:.{}e}".format(v, sig - 1), "{:.{}e}".format(t, sig - 1)
        if a != b:
            fa, ea = a.split("e")
            fb, eb = b.split("e")
            return "%s×10^%d vs %s×10^%d" % (fa, int(ea), fb, int(eb))
    return None


# ------------------------------------------------------------------ git
def git(args, timeout=GIT_TIMEOUT):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="true", GIT_OPTIONAL_LOCKS="0")
    cmd = ["git", "-C", REPO, "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
           "-c", "protocol.file.allow=never", "-c", "diff.external="] + args
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError) as e:
        warn("git %s: %s" % (args[0], e))
        return None
    if r.returncode != 0:
        warn("git %s exited %d: %s" % (args[0], r.returncode, clean(r.stderr.decode("utf-8", "replace"), 300)))
        return None
    return r.stdout.decode("utf-8", "replace")


def git_history():
    """{package folder name: (merge date YYYY-MM-DD, PR number or None)} from the commits that added each package.

    Returns None when history is unavailable (no git, or a shallow clone that cannot be deepened)."""
    if git(["rev-parse", "--git-dir"], 30) is None:
        return None, None
    head = (git(["log", "-1", "--format=%H"], 30) or "").strip()
    shallow = (git(["rev-parse", "--is-shallow-repository"], 30) or "").strip()
    if shallow == "true":
        print("shallow clone: trying git fetch --unshallow", file=sys.stderr)
        git(["fetch", "--unshallow", "--quiet", "--no-tags", "--no-recurse-submodules"], GIT_TIMEOUT)
        shallow = (git(["rev-parse", "--is-shallow-repository"], 30) or "").strip()
        if shallow != "false":
            warn("history unavailable (shallow clone); dates come from folder names and votes are skipped")
            return None, head
    out = git(["log", "--no-renames", "--diff-filter=A", "--name-only", "--no-textconv", "--no-ext-diff",
               "--format=%x1e%cI%x1f%s", "--", "known-knowns"])
    if out is None:
        return None, head
    first = {}
    for chunk in out.split("\x1e"):
        if not chunk.strip():
            continue
        header, _, body = chunk.partition("\n")
        date, _, subject = header.partition("\x1f")
        m = RE_PR.search(subject)
        pr = int(m.group(1)) if m else None
        day = date[:10] if re.match(r"^\d{4}-\d{2}-\d{2}T", date) else None
        names = set()
        for line in body.split("\n"):
            parts = line.split("/")
            if len(parts) >= 3 and parts[0] == "known-knowns" and RE_PKG.match(parts[2]):
                names.add(parts[2])
        for n in names:
            # log is newest first: the last commit seen is the oldest. Prefer the oldest commit that names a PR.
            old = first.get(n)
            if old is None or pr is not None or old[1] is None:
                first[n] = (day, pr)
    return first, head


# ------------------------------------------------------------------ GitHub API (read only)
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None  # never follow a redirect (it could carry the token elsewhere)


_opener = urllib.request.build_opener(_NoRedirect)


def api_get(url, token):
    if not url.startswith("https://api.github.com/"):
        raise ValueError("refusing non-API URL")
    h = {"Accept": "application/vnd.github+json", "User-Agent": "v3r1t4s-site-build",
         "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = "Bearer " + token
    with _opener.open(urllib.request.Request(url, headers=h), timeout=API_TIMEOUT) as r:
        if r.status != 200:
            raise ValueError("HTTP %d" % r.status)
        body = r.read(MAX_API_BYTES + 1)
        if len(body) > MAX_API_BYTES:
            raise ValueError("response too large")
        return json.loads(body.decode("utf-8")), r.headers.get("Link") or ""


def fetch_votes(token):
    """{PR number: thumbs-up count} for all closed issues and PRs, or None if the API is unreachable."""
    url = API + "/issues?state=closed&per_page=100"
    votes = {}
    for _ in range(MAX_API_PAGES):
        try:
            data, link = api_get(url, token)
        except (OSError, ValueError, http.client.HTTPException) as e:
            warn("votes skipped: GitHub API: %s" % clean(e, 200))
            return None
        if not isinstance(data, list):
            warn("votes skipped: unexpected API response")
            return None
        for it in data:
            try:
                if "pull_request" not in it:
                    continue
                n, up = it["number"], it["reactions"]["+1"]
                if isinstance(n, int) and isinstance(up, int) and 0 < n < 10 ** 7 and 0 <= up < 10 ** 7:
                    votes[n] = up
            except (KeyError, TypeError):
                continue
        m = re.search(r'<(https://api\.github\.com/[^>\s]+)>;\s*rel="next"', link)
        if not m:
            return votes
        url = m.group(1)
    warn("votes: stopped after %d pages" % MAX_API_PAGES)
    return votes


def fetch_stars(token):
    try:
        d, _ = api_get(API, token)
        s = d.get("stargazers_count")
        return s if isinstance(s, int) and 0 <= s < 10 ** 9 else None
    except (OSError, ValueError, AttributeError, http.client.HTTPException) as e:
        warn("stars skipped: %s" % clean(e, 200))
        return None


# ------------------------------------------------------------------ repo parsers
def trophy_rows():
    md = try_text("TROPHY_CASE.md")
    if not md:
        return None
    body = md.split("## All rows", 1)
    if len(body) < 2:
        return None
    body = body[1].split("\n## ", 1)[0]
    return sum(1 for line in body.split("\n") if re.match(r"^\|\s*\d+\s*\|", line))


def readme_category_emoji():
    """{category id: emoji} from the README known-unknowns table (categories.json carries no emoji)."""
    md = try_text("README.md") or ""
    out = {}
    for m in re.finditer(r"^\|\s*(\S{1,12})\s+\[[^\]]{1,80}\]\(known-unknowns/([a-z0-9-]{1,100})/README\.md\)",
                         md, re.M):
        e = emoji_ok(m.group(1))
        if e and RE_SLUG.match(m.group(2)):
            out[m.group(2)] = e
    return out


OWNER_NOTE = re.compile(r"has since adopted this code|is now the table value", re.I)


def parse_package(fam, name):
    rel = "known-knowns/%s/%s" % (fam, name)
    m = RE_PKG.match(name)
    readme = try_text(rel + "/README.md") or ""
    h1 = next((l[2:] for l in readme.split("\n")[:40] if l.startswith("# ")), "")
    title = re.sub(r"^\d{4}-\d{2}-\d{2}-[\w.-]+-[0-9a-f]{8}:\s*", "", h1)
    title = clean(strip_md(title), 140) or clean(name, 140)
    notes = [l for l in readme.split("\n") if l.startswith("> **Maintainer note")]
    owner = any(OWNER_NOTE.search(n) for n in notes)
    rows = []
    raw = None
    try:
        raw = read_text(rel + "/INDEX.csv", MAX_CSV)
    except (OSError, Unsafe) as e:
        warn("skip %s/INDEX.csv: %s" % (rel, e))
    if raw:
        try:
            for i, r in enumerate(csv.DictReader(io.StringIO(raw))):
                if i >= MAX_ROWS:
                    break
                rows.append(r)
        except csv.Error as e:
            warn("%s/INDEX.csv: %s" % (rel, e))
    targets = []
    for r in rows:
        t = str(r.get("target_id") or "").strip()
        if RE_SLUG.match(t) and t not in targets:
            targets.append(t)
    mg = None
    if len(rows) == 1:
        mg = margin(rows[0].get("value"), rows[0].get("table_value"))
    elif len(rows) > 1:
        mg = "%d rows" % len(rows)
    return {
        "id": name, "f": fam, "date": m.group(1), "c": m.group(2), "t": title,
        "m": clean(mg, 60) if mg else None, "s": "o" if owner else "v", "rows": len(rows), "targets": targets,
    }


# ------------------------------------------------------------------ build
def valid_site_url(u):
    u = (u or "").strip().rstrip("/")
    if not u:
        return None
    if not re.match(r"^https://[A-Za-z0-9.-]{1,253}(:\d{1,5})?(/[A-Za-z0-9._~/-]*)?$", u):
        warn("SITE_URL ignored (must be https://host[/path]): %r" % clean(u, 120))
        return None
    return u


def collect(offline):
    token = (os.environ.get("GITHUB_TOKEN") or "").strip() or None
    if token and not re.match(r"^[A-Za-z0-9_]{20,255}$", token):
        warn("GITHUB_TOKEN ignored (unexpected format)")
        token = None

    # bank
    bank = read_json("bank/targets.json") or {}
    cats_doc = read_json("bank/categories.json") or {}
    emo = readme_category_emoji()
    cats, cat_ids = [], set()
    for c in (cats_doc.get("categories") or [])[:200] if isinstance(cats_doc, dict) else []:
        if not isinstance(c, dict) or not RE_SLUG.match(str(c.get("id", ""))) or c["id"] in cat_ids:
            continue
        cat_ids.add(c["id"])
        cats.append({"id": c["id"], "name": clean(c.get("name") or c["id"], 40), "e": emo.get(c["id"]) or "◆", "n": 0})
    cat_by_id = {c["id"]: c for c in cats}
    ku, tcat = [], {}
    targets = bank.get("targets") if isinstance(bank, dict) else None
    for t in (targets or [])[:MAX_TARGETS]:
        if not isinstance(t, dict):
            continue
        tid, cid = str(t.get("id", "")), str(t.get("category", ""))
        if not (RE_SLUG.match(tid) and cid in cat_by_id):
            warn("bank target skipped: %r" % clean(tid, 60))
            continue
        if tid in tcat:
            continue
        tcat[tid] = cid
        if not is_file("known-unknowns/%s/%s.md" % (cid, tid)):
            warn("no known-unknowns page for %s/%s" % (cid, tid))
            continue
        tr = t.get("tractability")
        ku.append({"id": tid, "cat": cid, "t": clean(t.get("name") or tid, 180),
                   "k": clean(t.get("kind") or "", 12) or None,
                   "tr": tr if isinstance(tr, int) and 0 <= tr <= 9 else None,
                   "cp": clean(re.split(r"[;(]", str(t.get("compute_profile") or ""))[0], 24) or None})
        cat_by_id[cid]["n"] += 1
    for f in files_in("bank/proposed"):
        if f.endswith(".json") and len(f) < 120:
            p = read_json("bank/proposed/" + f, 1024 * 1024)
            if isinstance(p, dict) and RE_SLUG.match(str(p.get("id", ""))) and p.get("category") in cat_by_id:
                tcat.setdefault(p["id"], p["category"])
    ku.sort(key=lambda k: (-(k["tr"] or 0), k["t"].lower()))

    # packages
    pkgs = []
    for fam in subdirs("known-knowns"):
        if not RE_SLUG.match(fam):
            if not fam.startswith("."):
                warn("family skipped (name): %r" % clean(fam, 60))
            continue
        for name in subdirs("known-knowns/" + fam):
            if not name[:1].isdigit():
                continue
            if not RE_PKG.match(name):
                warn("package skipped (name): %r" % clean(name, 80))
                continue
            if len(pkgs) >= MAX_PACKAGES:
                break
            pkgs.append(parse_package(fam, name))

    # family emoji: the category of the family's bank target(s)
    fam_cat = {}
    for p in pkgs:
        for t in p["targets"]:
            if t in tcat:
                fam_cat.setdefault(p["f"], tcat[t])
        if p["f"] in tcat:
            fam_cat.setdefault(p["f"], tcat[p["f"]])

    hist, head = (None, None) if offline else git_history()
    if offline:
        head = (git(["log", "-1", "--format=%H"], 30) or "").strip()
    votes = None
    stars = None
    if not offline:
        if hist is not None:
            votes = fetch_votes(token)
        stars = fetch_stars(token)

    feed = []
    for p in pkgs:
        day, pr = (hist or {}).get(p["id"], (None, None))
        cid = fam_cat.get(p["f"])
        feed.append({
            "d": day or p["date"], "e": cat_by_id[cid]["e"] if cid in cat_by_id else "🔬", "t": p["t"], "m": p["m"],
            "s": p["s"], "c": p["c"], "p": pr, "v": votes.get(pr, 0) if (votes is not None and pr) else None,
            "f": p["f"], "k": p["id"],
        })
    feed.sort(key=lambda x: (x["d"], x["p"] or 0, x["k"]), reverse=True)

    board = {}
    for p in pkgs:
        k = p["c"].lower()
        b = board.setdefault(k, {"c": p["c"], "n": 0, "first": p["date"]})
        b["n"] += 1
        b["first"] = min(b["first"], p["date"])
    lb = sorted(board.values(), key=lambda b: (-b["n"], b["first"], b["c"].lower()))
    contributed_rows = sum(p["rows"] for p in pkgs)

    counts = {"results": trophy_rows(), "contributed": contributed_rows, "contributors": len(board),
              "known_unknowns": len(ku), "packages": len(pkgs), "categories": len([c for c in cats if c["n"]])}
    data = {
        "schema": "v3r1t4s-site/1",
        "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": head[:12] if head and re.match(r"^[0-9a-f]{40}$", head) else None,
        "history": hist is not None,
        "votes": votes is not None,
        "stars": stars,
        "counts": counts,
        "feed": feed,
        "board": [{"c": b["c"], "n": b["n"]} for b in lb[:10]],
        "cats": [c for c in cats if c["n"]],
        "ku": ku,
    }
    return data


def fmt(n):
    return "{:,}".format(n) if isinstance(n, int) else "–"


def render_index(data, site_url):
    tpl = open(os.path.join(SRC, "index.html"), encoding="utf-8").read()
    c = data["counts"]
    desc = ("Turn your unused tokens into scientific discoveries. %s results, %s contributed rows, %s known "
            "unknowns. Not peer reviewed: every result ships with its own checker."
            % (fmt(c["results"]), fmt(c["contributed"]), fmt(c["known_unknowns"])))
    meta = []
    if site_url:
        meta += ['<link rel="canonical" href="%s/">' % html.escape(site_url),
                 '<meta property="og:url" content="%s/">' % html.escape(site_url),
                 '<meta property="og:image" content="%s/og.png">' % html.escape(site_url),
                 '<meta name="twitter:image" content="%s/og.png">' % html.escape(site_url)]
    else:
        meta += ['<meta property="og:image" content="og.png">', '<meta name="twitter:image" content="og.png">']
    subs = {
        "DESCRIPTION": html.escape(desc),
        "SITE_META": "\n".join(meta),
        "N_RESULTS": html.escape(fmt(c["results"])),
        "N_CONTRIBUTED": html.escape(fmt(c["contributed"])),
        "N_CONTRIBUTORS": html.escape(fmt(c["contributors"])),
        "N_KNOWN_UNKNOWNS": html.escape(fmt(c["known_unknowns"])),
        "STARS": html.escape(fmt(data["stars"])) if data["stars"] is not None else "",
        "BUILT": html.escape(data["built"][:10]),
        "COMMIT": html.escape(data["commit"] or ""),
        "YEAR": html.escape(data["built"][:4]),
    }
    out = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: subs[m.group(1)], tpl)
    assert "{{" not in out
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(HERE, "public"))
    ap.add_argument("--offline", action="store_true", help="no git history and no GitHub API (votes skipped)")
    a = ap.parse_args()
    offline = a.offline or os.environ.get("V3R1T4S_OFFLINE") == "1"
    out = os.path.realpath(a.out)
    default = os.path.join(HERE, "public")
    if out == os.sep or (REPO + os.sep).startswith(out + os.sep) or out == SRC or out.startswith(SRC + os.sep):
        sys.exit("refusing to write to %s" % out)
    if os.path.isdir(out) and out != default and os.listdir(out) and not os.path.exists(os.path.join(out, "data.json")):
        sys.exit("refusing to clear %s: not empty and not a previous build" % out)

    data = collect(offline)
    site_url = valid_site_url(os.environ.get("SITE_URL"))

    if os.path.isdir(out) and not os.path.islink(out):
        shutil.rmtree(out)
    os.makedirs(out)
    # static files from site/src (ours, not contributor content), copied without following symlinks
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for f in files:
            sp = os.path.join(root, f)
            if os.path.islink(sp) or f == "index.html" and root == SRC or f.startswith("."):
                continue
            dp = os.path.join(out, os.path.relpath(sp, SRC))
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copyfile(sp, dp)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(data, site_url))
    with open(os.path.join(out, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, separators=(",", ":"))
    robots = "User-agent: *\nAllow: /\n"
    if site_url:
        robots += "Sitemap: %s/sitemap.xml\n" % site_url
        with open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    "<url><loc>%s/</loc><lastmod>%s</lastmod></url></urlset>\n"
                    % (html.escape(site_url), data["built"][:10]))
    with open(os.path.join(out, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    c = data["counts"]
    print("site/public: %d discoveries, %d on the leaderboard, %d known unknowns in %d categories"
          % (len(data["feed"]), len(data["board"]), len(data["ku"]), len(data["cats"])))
    print("counts: %s" % json.dumps(c))
    print("history: %s, votes: %s, stars: %s, site_url: %s, warnings: %d"
          % (data["history"], data["votes"], data["stars"], site_url, len(warnings)))


if __name__ == "__main__":
    main()
