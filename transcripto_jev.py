"""Optional network correction detector: TypeSafe Jev via OpenRouter.

OFF unless a run passes `--detector jev`. Nothing here is imported, and no
socket is opened, on the default path. There is no environment variable and
no config file that turns it on: the flag is the consent, per run.

What leaves the machine, and only after the privacy filter below:
  - the typed turn text (at most MAX_CHARS characters per turn), redacted;
  - the fixed question wording (INSTRUCTIONS, CHOICE_CRITERIA).
Where it goes: URL, authorised by OPENROUTER_API_KEY. Nothing else is sent:
no file paths, no session ids, no agent output, no tool results.

The question and the threshold come from the jev-experiment lane (2 Oct 2026):
185 privacy-cleared, model-labelled turns, Choice formulation picked on split A
and reported on split B (F1 0.769 at 0.5). P(correction) at 0.30 to 0.35 beat
0.5 in both split directions, so the default threshold is 0.30. Labels were
made by one model rater, so these are agreement numbers, not accuracy.

Stdlib only, like the rest of Transcripto.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
MAX_CHARS = 2000
DEFAULT_THRESHOLD = 0.30
DEFAULT_BATCH = 1
DEFAULT_MAX_USD = 1.00
DEFAULT_WORKERS = 4
TIMEOUT_S = 60
RETRIES = 3

# ---------------------------------------------------------------------------
# the question, verbatim from experiments/jev_corrections.py (jev-experiment)
# ---------------------------------------------------------------------------
INSTRUCTIONS = (
    "The message was typed by a person to an AI coding agent, in a session where "
    "the agent had just done some work or given an answer. Is this message "
    "correcting the agent's previous work? That means the person is telling the "
    "agent that what it just did or said was wrong, not what they wanted, or must "
    "be redone or changed.")

CHOICE_CRITERIA = {
    "correction": (
        "The person tells the agent its previous work or answer was wrong, "
        "misunderstood, broken, not what was asked, or must be redone, undone, "
        "fixed or changed. Includes mild critiques and challenges phrased as "
        "questions about whether the agent's output is right."),
    "new_request": "The person asks for a new task or adds a requirement without "
                   "saying the agent got anything wrong.",
    "continue_or_approve": "The person tells the agent to go on, confirms, approves, "
                           "or answers a question the agent asked.",
    "information_or_question": "The person provides information or asks a question "
                               "about the world or the code, not a critique of the "
                               "agent's work.",
    "other": "None of the above, or the message is empty or unreadable.",
}

# ---------------------------------------------------------------------------
# privacy filter: runs on every turn BEFORE any request is built
# ---------------------------------------------------------------------------
# Order matters and matches the experiment: exclusion checks first (a hit drops
# the whole turn, it is never sent), then redaction, then truncation.
#
# EXCLUDE (the turn is not sent at all):
#   1. the local account name as a whole word (identifies the person);
#   2. a numbered personal-note path: two digits, a space, a capitalised
#      folder name, then a .md file (the shape of a notes vault);
#   3. private topics, whole word, case-insensitive;
#   4. an email address or a phone-like digit run.
# REDACT (the turn is sent with the span replaced):
#   5. secrets: OpenAI/Anthropic-style sk- keys, GitHub tokens, AWS key ids,
#      private-key headers, 40-hex 0x addresses;
#   6. home directory paths, plain and in Claude's dash-encoded project form.
_TOPIC_RE = re.compile(
    r"\b(money|finance|finances|financial|wallet|wallets|seed|seeds|key|keys|"
    r"password|passwords|token|tokens|salary|salaries|bank|banks|banking|"
    r"journal|journals|health|family)\b", re.I)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?<!\d)\+?\d[\d \-()]{8,}\d(?!\d)")
_NOTE_PATH_RE = re.compile(r"(?:^|[^0-9])[0-9]{2} [A-Z][A-Za-z ]*/[^\n]*?\.md\b")
_SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{8,}"
    r"|gh[pousr]_[A-Za-z0-9_]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"
    r"|0x[0-9a-fA-F]{40}")
_HOME_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s\"']+|-(?:Users|home)-[A-Za-z0-9_.]+")


def _account_name(home=None):
    name = os.path.basename((home or os.path.expanduser("~")).rstrip("/"))
    return name if len(name) >= 4 else None


def privacy(text, home=None):
    """(clean_text or None, exclusion_reason or None, n_redactions).

    PURE. A None text means the turn must not leave the machine."""
    name = _account_name(home)
    # A home path is redacted below, so it must not count as naming the person.
    if name and re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])",
                          _HOME_PATH_RE.sub("~", text), re.I):
        return None, "account-name", 0
    if _NOTE_PATH_RE.search(text):
        return None, "note-path", 0
    m = _TOPIC_RE.search(text)
    if m:
        return None, "topic:" + m.group(1).lower(), 0
    if _EMAIL_RE.search(text):
        return None, "email", 0
    if _PHONE_RE.search(text):
        return None, "phone", 0
    clean, n1 = _SECRET_RE.subn("[REDACTED]", text)
    clean, n2 = _HOME_PATH_RE.subn("~", clean)
    return clean[:MAX_CHARS], None, n1 + n2


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------
class JevError(Exception):
    """A request failed; the turns in it get no verdict."""


class JevAuthError(JevError):
    """The key was refused (401/402/403). The run stops: retrying cannot help."""


def _post(body, key, urlopen=None, timeout=TIMEOUT_S):
    urlopen = urlopen or urllib.request.urlopen
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "X-Title": "transcripto"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 402, 403):
            raise JevAuthError(
                "OpenRouter refused the request with HTTP %d (401/403: key not "
                "accepted, 402: no credit left). Check OPENROUTER_API_KEY." % e.code)
        raise JevError("HTTP %d" % e.code)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise JevError(type(e).__name__)


def build_body(texts):
    """One request for one or more turns.

    One turn: exactly the experiment's request ({"message": text}, question
    "kind"). Several turns: each turn under its own state key m0, m1, ... and
    one Choice question per key, told which key to read."""
    if len(texts) == 1:
        return {"model": MODEL, "state": {"message": texts[0]},
                "questions": {"kind": {"type": "choice", "instructions": INSTRUCTIONS,
                                       "criteria": CHOICE_CRITERIA}}}
    state, questions = {}, {}
    for i, t in enumerate(texts):
        k = "m%d" % i
        state[k] = t
        questions[k] = {"type": "choice",
                        "instructions": ("Read only the message in the state field "
                                         "\"%s\". " % k) + INSTRUCTIONS,
                        "criteria": CHOICE_CRITERIA}
    return {"model": MODEL, "state": state, "questions": questions}


def parse_answers(resp, n):
    """[P(correction) or None] * n, in input order."""
    answers = resp.get("answers") or {}
    names = ["kind"] if n == 1 else ["m%d" % i for i in range(n)]
    out = []
    for name in names:
        a = answers.get(name) or {}
        p = (a.get("probabilities") or {}).get("correction")
        try:
            out.append(float(p) if p is not None else None)
        except (TypeError, ValueError):
            out.append(None)
    return out


# ---------------------------------------------------------------------------
# the detector
# ---------------------------------------------------------------------------
def default_notice(line):
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


class JevDetector(object):
    """score(texts) -> [True / False / None], one per text, plus self.stats.

    None means no verdict: the turn was excluded by the privacy filter, its
    request failed, or the spend cap stopped the run. It is never backfilled
    with the regex."""

    def __init__(self, key, threshold=DEFAULT_THRESHOLD, batch=DEFAULT_BATCH,
                 max_usd=DEFAULT_MAX_USD, workers=DEFAULT_WORKERS, urlopen=None,
                 notice=default_notice, sleep=time.sleep, home=None):
        if not key:
            raise JevAuthError("OPENROUTER_API_KEY is not set.")
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if batch < 1:
            raise ValueError("batch must be at least 1")
        self._key = key
        self.threshold, self.batch, self.max_usd = threshold, batch, max_usd
        self.workers = max(1, workers)
        self._urlopen, self._notice, self._sleep, self._home = urlopen, notice, sleep, home
        self.stats = {}

    def _call(self, texts):
        last = None
        for i in range(RETRIES):
            try:
                resp = _post(build_body(texts), self._key, self._urlopen)
                cost = (resp.get("usage") or {}).get("cost")
                return parse_answers(resp, len(texts)), cost, resp.get("model")
            except JevAuthError:
                raise
            except JevError as e:
                last = e
                self._sleep(2 * (i + 1))
        return [None] * len(texts), None, "error: %s" % last

    def score(self, texts):
        n = len(texts)
        verdicts, probs = [None] * n, [None] * n
        excluded, redactions, send = {}, 0, []
        for i, t in enumerate(texts):
            clean, why, nred = privacy(t, self._home)
            if clean is None:
                excluded[why] = excluded.get(why, 0) + 1
            else:
                redactions += nred
                send.append((i, clean))
        st = self.stats = {
            "model": MODEL, "url": URL, "threshold": self.threshold, "batch": self.batch,
            "turns": n, "excluded": sum(excluded.values()),
            "excluded_reasons": dict(sorted(excluded.items())),
            "redactions": redactions, "sent": len(send), "scored": 0, "errors": 0,
            "requests": 0, "cost_usd": 0.0, "priced_requests": 0,
            "budget_stopped": False, "budget_unsent": 0,
            "auth_error": None, "auth_unsent": 0, "served_by": None}
        self.probabilities = probs
        self._notice(
            "transcripto: --detector jev sends %d of %d typed turns (privacy filter "
            "excluded %d, redacted %d spans, max %d chars each) to %s, model %s. "
            "Nothing else leaves this machine." % (
                len(send), n, st["excluded"], redactions, MAX_CHARS, URL, MODEL))
        if not send:
            return verdicts
        chunks = [send[j:j + self.batch] for j in range(0, len(send), self.batch)]

        def apply(chunk, result):
            ps, cost, served = result
            st["requests"] += 1
            if cost is not None:
                st["cost_usd"] += float(cost)
                st["priced_requests"] += 1
            if served and not str(served).startswith("error") and not st["served_by"]:
                st["served_by"] = served
            for (i, _), p in zip(chunk, ps):
                probs[i] = p
                if p is None:
                    st["errors"] += 1
                else:
                    verdicts[i] = p >= self.threshold
                    st["scored"] += 1

        # First request alone: a refused key stops the run before anything else is sent.
        apply(chunks[0], self._call([t for _, t in chunks[0]]))
        rest = chunks[1:]
        with ThreadPoolExecutor(self.workers) as ex:
            for w in range(0, len(rest), self.workers):
                if st["cost_usd"] >= self.max_usd:
                    st["budget_stopped"] = True
                    st["budget_unsent"] = sum(len(c) for c in rest[w:])
                    break
                wave = rest[w:w + self.workers]
                futs = [ex.submit(self._call, [t for _, t in c]) for c in wave]
                for chunk, fut in zip(wave, futs):
                    try:
                        apply(chunk, fut.result())
                    except JevAuthError as e:
                        # Refused mid-run (credit ran out): keep what was scored.
                        st["auth_error"] = str(e)
                        st["errors"] += len(chunk)
                if st["auth_error"]:
                    st["auth_unsent"] = sum(len(c) for c in rest[w + self.workers:])
                    break
        st["cost_usd"] = round(st["cost_usd"], 6)
        return verdicts
