"""Governance artifacts, and the number they both state.

The comment period appears in GOVERNANCE.md and in the proposal template. Two
artifacts asserting one value is the shape that has drifted repeatedly in this
repository, so it is checked rather than trusted.
"""
from __future__ import annotations

import re

import pytest

from conftest import ROOT

yaml = pytest.importorskip("yaml")

GOVERNANCE = ROOT / "GOVERNANCE.md"
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"

WORDS = {"seven": 7, "fourteen": 14, "thirty": 30, "one": 365}


def stated_period(text: str) -> set[int]:
    """Periods stated in days or in years, however written.

    Both artifacts state the ordinary period and the expedited recording
    deadline, so the comparison is over sets rather than a single value.
    """
    found = {int(m) for m in re.findall(r"(\d+)[ -]day", text, re.I)}
    found |= {
        WORDS[m.lower()] for m in re.findall(r"([A-Za-z-]+) day", text)
        if m.lower() in WORDS
    }
    found |= {
        365 * WORDS.get(m.lower(), 0) or 365
        for m in re.findall(r"([A-Za-z-]+|\d+)[ -]year", text, re.I)
    }
    return found


def test_every_template_is_valid_yaml():
    """A malformed issue form does not error; GitHub falls back to a blank
    issue, so the questions simply stop being asked."""
    for path in sorted(TEMPLATES.glob("*.yml")):
        yaml.safe_load(path.read_text(encoding="utf-8"))


def test_the_window_is_long_enough_for_an_annual_review():
    """The stated reason for the length. An adopter on an annual cycle has to be
    able to see a proposal within one of them."""
    assert 365 in stated_period(GOVERNANCE.read_text(encoding="utf-8"))


def test_additive_changes_are_not_gated_by_the_window():
    """The distinction the whole mechanism rests on. Gating a change nobody has
    to migrate for would make the process an obstacle rather than a protection.
    """
    text = GOVERNANCE.read_text(encoding="utf-8")
    section = text[text.index("## Two kinds of change"):text.index("## The collection window")]
    assert "Additive changes land whenever they are ready" in section
    assert "unclear" in section, "the tie-breaking rule is not stated"


def test_a_late_proposal_rolls_rather_than_squeezing_in():
    """Without this, the deadline becomes the only thing that matters and a
    proposal raised days before it ships unexamined."""
    for text in (GOVERNANCE.read_text(encoding="utf-8"), (ROOT / "docs" / "proposals" / "OPEN.md").read_text(encoding="utf-8")):
        assert "sixty days" in text


def test_the_comment_period_agrees_across_artifacts():
    governance = stated_period(GOVERNANCE.read_text(encoding="utf-8"))
    proposal = stated_period((TEMPLATES / "specification-change.yml").read_text(encoding="utf-8"))
    assert governance, "GOVERNANCE.md states no comment period"
    assert proposal, "the proposal template states no comment period"
    assert proposal <= governance, (
        f"the template says {sorted(proposal)} and GOVERNANCE.md says "
        f"{sorted(governance)}"
    )


def test_the_proposal_template_asks_whether_the_contract_breaks():
    """The one question that decides whether a change waits for a designated
    release. A proposal that does not answer it cannot be triaged."""
    form = yaml.safe_load((TEMPLATES / "specification-change.yml").read_text(encoding="utf-8"))
    fields = {item.get("id") for item in form["body"]}
    assert {"change", "why", "contract", "affected"} <= fields
    contract = next(i for i in form["body"] if i.get("id") == "contract")
    assert contract["validations"]["required"]


def test_registration_captures_who_to_notify():
    """Silence counts as assent only if the people whose assent matters were
    told, so the registry has to record how to tell them."""
    form = yaml.safe_load((TEMPLATES / "adopter-registration.yml").read_text(encoding="utf-8"))
    notify = next(i for i in form["body"] if i.get("id") == "notify")
    assert notify["validations"]["required"]


def test_governance_names_what_is_not_governed():
    """Without the exclusions, every bug fix needs a comment period and the
    process becomes an obstacle to keeping the promises it protects."""
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "Not governed" in text
    for exempt in ("Implementation", "ergonomics", "Documentation"):
        assert exempt in text


def test_the_open_proposal_register_exists_and_is_referenced():
    """A shared deadline is only useful if it is discoverable. Someone doing an
    annual review checks one file rather than filtering issues they were not
    watching when the discussion happened."""
    register = ROOT / "docs" / "proposals" / "OPEN.md"
    assert register.exists()
    text = register.read_text(encoding="utf-8")
    for element in ("Window closes", "Breaks the contract", "Objections"):
        assert element in text, f"the register does not record {element.lower()}"
    assert "OPEN.md" in GOVERNANCE.read_text(encoding="utf-8")
    assert "OPEN.md" in (TEMPLATES / "specification-change.yml").read_text(encoding="utf-8")


def test_the_expedited_bar_names_what_is_not_grounds():
    """With a one-year ordinary period the temptation to reclassify a change as
    urgent is the failure mode that would empty the document of meaning."""
    text = GOVERNANCE.read_text(encoding="utf-8")
    section = text[text.index("## Expedited changes"):]
    for excluded in ("Convenience", "confidence"):
        assert excluded in section
    assert "open to objection" in section, (
        "an expedited change must remain objectable, or shipping first settles it"
    )


def test_the_release_procedure_names_the_irreversible_step():
    """Creating a GitHub release is what publishes to PyPI, and the guard
    permits anything at or above 1.0, so nothing stops a mistake there."""
    text = (ROOT / "RELEASING.md").read_text(encoding="utf-8")
    assert "irreversible" in text
    assert "publish.yml" in text


def test_limitations_are_collected_and_linked():
    """1.0 criterion 4. Scattered across the roadmap is not where someone
    deciding whether to adopt looks."""
    limitations = ROOT / "LIMITATIONS.md"
    assert limitations.exists()
    assert "LIMITATIONS.md" in (ROOT / "README.md").read_text(encoding="utf-8")
    text = limitations.read_text(encoding="utf-8")
    # Substance rather than headings, which move. Each is a limitation an
    # adopter would want to know before committing rather than after.
    for topic in ("Advanced Features", "absolute IRI", "one author", "Scale is untested"):
        assert topic in text, f"LIMITATIONS.md no longer covers {topic!r}"


def test_the_adopter_registry_is_a_file_the_workflow_can_read():
    """A registry living in issue search is enumerable by nothing without API
    access, reviewable in no pull request, and not diffable. Every other
    register here is a file."""
    registry = ROOT / "ADOPTERS.md"
    assert registry.exists()
    text = registry.read_text(encoding="utf-8")
    assert "| GitHub |" in text, "the registry has no table for the workflow to parse"
    assert "GOVERNANCE.md" in text


def test_notification_is_automated_rather_than_remembered():
    """Silence counts as assent across a year-long window. Leaving the
    notification to memory is how that promise stops being kept."""
    workflow = ROOT / ".github" / "workflows" / "notify-adopters.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "specification-change" in text, "the workflow is not triggered by the label"
    assert "ADOPTERS.md" in text, "the workflow does not read the registry"
    assert "OPEN.md" in text, "the closing date should be read, not restated"


def test_the_registration_template_says_closing_is_not_dismissal():
    """An adopter whose issue is closed without explanation reasonably reads
    that as being turned away. Matched on the parsed body rather than the raw
    file, since the sentence wraps and a substring search misses it."""
    form = yaml.safe_load((TEMPLATES / "adopter-registration.yml").read_text(encoding="utf-8"))
    prose = " ".join(
        " ".join(item.get("attributes", {}).get("value", "").split())
        for item in form["body"]
    )
    assert "not a dismissal" in prose
    assert "ADOPTERS.md" in prose
