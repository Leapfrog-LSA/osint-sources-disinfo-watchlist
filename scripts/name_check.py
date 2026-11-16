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
MIN_ACRONYM = 3

# Letters that are one letter to a reader and have no decomposition for
# `unicodedata` to strip: Polish `ł`, Nordic `ø`, Turkish dotless `ı`.
_NO_DECOMPOSITION = str.maketrans({
    "ł": "l", "Ł": "l", "ø": "o", "Ø": "o", "đ": "d", "Đ": "d",
    "ı": "i", "İ": "i", "ß": "ss",
})
# Characters a browser never shows and that would split a word in two.
_INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\u200c\u200d\u2060\ufeff"))


def fold(text):
    """Lower case, without accents: `Société` and `SOCIETE` are one word."""
    text = text.translate(_INVISIBLE).translate(_NO_DECOMPOSITION)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").casefold()


def words(text):
    """The words of a text, folded.

    A word is a run of letters, digits and the marks that belong to them. The
    marks matter: an Indic vowel sign is not a letter to `\\w`, and splitting
    on it turns one word into fragments that match inside longer words.
    """
    found, current = [], []
    for char in fold(text):
        if unicodedata.category(char)[0] in "LNM":
            current.append(char)
        elif current:
            found.append("".join(current))
            current = []
    if current:
        found.append("".join(current))
    return found


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
    # Only a bracket that *is* an acronym comes off. `Corporate Registry
    # (Yukon)` is not stated by Alberta's Corporate Registry: a qualifier in
    # brackets is part of the name, and CONTRIBUTING.md asks for exactly that
    # kind of qualifier to tell two bodies apart.
    bare = name
    for acronym in acronyms(name):
        bare = bare.replace(f"({acronym})", " ")
    return [w for w in words(bare) if w not in STOPWORDS and (len(w) > 1 or not w.isascii())]


def registrable_label(host):
    """The label a body registered for itself: `inapi` in `www.inapi.gov.dz`.

    One label, the one next to the suffix — not every label. `news` in
    `news.example.com` is a section of someone's site, and a source called
    "News" does not have that site's name as its domain. Without a
    public-suffix list the suffix is approximated: the top-level domain, and
    any generic second level before it. Returns a list, empty or of one.
    """
    generic = {"www", "gov", "gob", "gouv", "govt", "go", "com", "org", "net",
               "co", "ac", "edu", "or", "nic", "gv", "admin", "web", "portal"}
    labels = fold(host).split(":")[0].split(".")
    if len(labels) < 2 or all(label.isdigit() for label in labels):
        return []  # a bare name or an IP address has no registered label
    labels = labels[:-1]  # the top-level domain
    while labels and labels[-1] in generic:
        labels.pop()
    return [labels[-1]] if labels and len(labels[-1]) > 2 else []


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
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")
_CHARSET = re.compile(rb'<meta[^>]+charset=["\']?([\w-]+)', re.I)
# The value runs to the quote that opened it, so `alt="Chambre d'Industrie"`
# is read whole. No `data-content`, no `og:title`-style suffix match.
_SHOWN_ATTR = re.compile(r"""(?<![\w-])(?:content|alt|title)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)


def decode(body, header_charset=""):
    """Bytes to text, honouring the charset the page declares for itself.

    The page's own `<meta charset>` first, then the one the server sent in
    `Content-Type`, then UTF-8. A charset Python does not know, or cannot use
    on text, falls through to the next.
    """
    declared = _CHARSET.search(body[:4000])
    candidates = [declared.group(1).decode("ascii", "replace") if declared else "",
                  header_charset or ""]
    for charset in candidates:
        if not charset:
            continue
        try:
            return body.decode(charset, errors="replace")
        except (LookupError, UnicodeError):
            continue
    return body.decode("utf-8", errors="replace")


def visible_text(markup):
    """What a reader sees: tags, scripts and styles removed, entities read.

    Attribute text counts where it is shown to the reader or names the site —
    `content`, `alt` and `title` — because a body whose name is a logo says
    so only in the image's `alt`.
    """
    # Comments and scripts go first, and the attributes are read from what is
    # left: a name that survives only in commented-out markup, or in a string
    # inside a script, is not on the page.
    markup = _HIDDEN.sub(" ", _COMMENT.sub(" ", markup))
    shown = " ".join(a or b for a, b in _SHOWN_ATTR.findall(markup))
    stripped = _TAG.sub(" ", markup)
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
            text = visible_text(decode(resp.read(400_000),
                                       resp.headers.get_content_charset() or ""))
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
