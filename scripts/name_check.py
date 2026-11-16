#!/usr/bin/env python3
"""
Does a page say it is the body a row claims it is?

    python scripts/name_check.py "Danish Business Authority" https://danishbusinessauthority.dk

A directory is a source of candidates, not of facts: its addresses go stale
and can be wrong while still answering `200` with a full page. Before a
candidate becomes a row, its own page has to state its own name. This module
is that rule, written down so that every import applies the same one.

A page passes in exactly three ways:

* **acronym** — the name carries an acronym in brackets, `(INAPI)`, and the
  page prints it, as a word, in the same capitals;
* **words** — the page prints *every* distinctive word of the name. Not one
  of them: a first version of this rule accepted a single word and passed
  "Business News" on any site about business;
* **domain** — the whole name, or its acronym, is the site's own domain.

Passing is necessary and not sufficient. A server's default page, an error
served with `200` and a ministry's portal standing in for an office it hosts
have all passed a rule like this one. Whatever passes is still read by a
person before it is merged — see CONTRIBUTING.md, "Adding sources in bulk".

Failing means "not confirmed", never "wrong": a page written in a language
the name is not, or drawn by a script in the browser, fails without being
anyone else's page.

Standard library only — no dependencies to install.
"""

import argparse
import html
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

# Words that identify nothing: articles, prepositions and conjunctions in the
# languages names in this catalogue are written in. Deliberately short. A word
# such as "national" or "office" is generic too, but dropping it would let
# "National Office of Statistics" pass on the word "statistics" alone.
STOPWORDS = {
    "a", "an", "and", "the", "of", "for", "in", "on", "to", "at", "by",
    "de", "del", "della", "delle", "dei", "degli", "di", "da", "do", "dos",
    "das", "du", "des", "le", "la", "les", "el", "los", "las", "lo", "il",
    "gli", "e", "y", "et", "und", "der", "die", "das", "den", "dem", "für",
    "fur", "van", "het", "en", "per", "con", "pour", "para", "por", "sur",
    "au", "aux", "al", "na", "no", "nas", "nos", "em", "i", "o", "os", "as",
}

ACRONYM = re.compile(r"\(([A-Z][A-Za-z&.\-]{1,11})\)")
WORD = re.compile(r"[^\W_]+", re.UNICODE)
MIN_ACRONYM = 3


def fold(text):
    """Lower case, without accents: `Société` and `SOCIETE` are one word."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def words(text):
    return WORD.findall(fold(text))


def acronyms(name):
    """Acronyms a name carries in brackets, three letters or more.

    Two letters are not enough to mean anything: `(KG)` is on every page of
    every site under `.kg`.
    """
    found = []
    for match in ACRONYM.findall(name):
        letters = re.sub(r"[^A-Za-z]", "", match)
        if len(letters) >= MIN_ACRONYM and sum(c.isupper() for c in letters) >= 2:
            found.append(match)
    return found


def distinctive(name):
    """The words of a name that could tell it from another, in order."""
    bare = ACRONYM.sub(" ", name)
    return [w for w in words(bare) if w not in STOPWORDS and (len(w) > 1 or not w.isascii())]


def registrable_label(host):
    """The label a body chose for itself: `inapi` in `www.inapi.gov.dz`.

    Without a public-suffix list this cannot be exact, so it returns every
    label that is not a generic second level or a country code, and the
    caller asks whether the name is *one* of them.
    """
    generic = {"www", "gov", "gob", "gouv", "govt", "go", "com", "org", "net",
               "co", "ac", "edu", "or", "nic", "gv", "admin", "web", "portal"}
    labels = fold(host).split(":")[0].split(".")
    if len(labels) > 1:
        labels = labels[:-1]  # the top-level domain
    return [label for label in labels if label not in generic and len(label) > 2]


def states_name(name, page_text, host=""):
    """How the page states `name`: 'acronym', 'words', 'domain', or ''.

    `page_text` is whatever of the page a reader sees — title, headings,
    body — with markup already removed.
    """
    name = (name or "").strip()
    if not name:
        return ""
    text = html.unescape(page_text or "")

    for acronym in acronyms(name):
        if re.search(rf"(?<![^\W_]){re.escape(acronym)}(?![^\W_])", text):
            return "acronym"

    wanted = distinctive(name)
    if wanted:
        present = set(words(text))
        if all(word in present for word in wanted):
            return "words"

    labels = registrable_label(host) if host else []
    if labels:
        joined = "".join(wanted)
        candidates = {joined} | {fold(re.sub(r"[^A-Za-z]", "", a)) for a in acronyms(name)}
        candidates.discard("")
        if any(label.replace("-", "") in candidates for label in labels):
            return "domain"
    return ""


# --------------------------------------------------------------------------
# Reading a page
# --------------------------------------------------------------------------

_HIDDEN = re.compile(r"<(script|style|noscript|svg|template)\b[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_CHARSET = re.compile(rb'<meta[^>]+charset=["\']?([\w-]+)', re.I)


def decode(body):
    """Bytes to text, honouring the charset the page declares for itself."""
    declared = _CHARSET.search(body[:4000])
    if declared:
        try:
            return body.decode(declared.group(1).decode("ascii"), errors="replace")
        except LookupError:
            pass
    return body.decode("utf-8", errors="replace")


def visible_text(markup):
    """What a reader sees: tags, scripts and styles removed, entities read.

    Attribute text counts where it is shown to the reader or names the site —
    `content`, `alt` and `title` — because a body whose name is a logo says
    so only in the image's `alt`.
    """
    shown = " ".join(re.findall(r'\b(?:content|alt|title)=["\']([^"\']*)', markup, re.I))
    stripped = _TAG.sub(" ", _HIDDEN.sub(" ", markup))
    return re.sub(r"\s+", " ", html.unescape(f"{stripped} {shown}")).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Check that a page states the name a row would give it.")
    parser.add_argument("name", help="the name the row would carry")
    parser.add_argument("url", help="the address to read")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_links as cl  # noqa: E402 — same opener as the link check

    try:
        with cl.OPENER.open(cl._request(args.url, cl.USER_AGENTS[0]), timeout=25) as resp:
            final = resp.geturl()
            text = visible_text(decode(resp.read(400_000)))
    except Exception as error:  # noqa: BLE001 — any failure means "not read"
        print(f"not read — {type(error).__name__}: {error}")
        print("That says nothing about the source: it was not seen.")
        return 2

    how = states_name(args.name, text, urlparse(final).netloc)
    if how:
        print(f"states its name ({how}) at {final}")
        print("Necessary, not sufficient: read the page before adding the row.")
        return 0
    print(f"does not state {args.name!r} at {final}")
    print("Not confirmed — which is not the same as wrong.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
