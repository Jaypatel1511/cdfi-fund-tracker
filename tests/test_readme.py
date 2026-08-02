"""The README is a claim about this package. These tests check it.

A prior release in this portfolio shipped a notebook described as "runs
correctly" in which 8 of 10 cells raised. Documentation that is never executed
is documentation that is never true for long.
"""

import os
import pathlib
import re
import subprocess
import sys

import pytest


def _env_importing_the_package_under_test():
    """Env whose PYTHONPATH points at whichever cdfifund this suite is testing.

    Locally that is the source tree; in the release workflow's wheel-test job it
    is site-packages. The subprocess must exercise the same one, not whatever
    happens to be installed globally.
    """
    import cdfifund

    package_parent = str(pathlib.Path(cdfifund.__file__).resolve().parent.parent)
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        package_parent + os.pathsep + existing if existing else package_parent
    )
    return env


def _find_readme():
    """Locate README.md next to the tests dir or one level up (repo root)."""
    here = pathlib.Path(__file__).resolve().parent
    for candidate in (here / "README.md", here.parent / "README.md"):
        if candidate.is_file():
            return candidate
    return None


def _award(**kw):
    """An otherwise-valid Award, with overrides. See tests/test_schema.py."""
    from cdfifund import Award

    d = dict(
        award_id="A1", recipient_name="X", recipient_type="loan_fund",
        program="CDFI_FA", award_amount=1_000.0, award_date="2024-09-15",
        award_year=2024, state="IL", congressional_district=1,
        intended_use="u", status="active",
    )
    d.update(kw)
    return lambda: Award(**d)


def _recipient(**kw):
    """An otherwise-valid Recipient, with overrides."""
    from cdfifund import Recipient

    d = dict(
        recipient_id="R1", name="X", type="loan_fund",
        certification_status="certified", total_awards=1.0,
        programs_received=["CDFI_FA"], geographic_areas=["IL"],
    )
    d.update(kw)
    return lambda: Recipient(**d)


def _record(**kw):
    """An otherwise-valid ComplianceRecord, with overrides."""
    from cdfifund import ComplianceRecord

    d = dict(
        recipient_id="R1", program="CDFI_FA", deployment_pct=0.5,
        deadline="2026-12-01", status="on_track",
        last_reporting_date="2025-01-01",
    )
    d.update(kw)
    return lambda: ComplianceRecord(**d)


README = _find_readme()

readme_required = pytest.mark.skipif(
    README is None,
    reason="README.md not present (test tree copied without it)",
)


@readme_required
class TestReadmeQuickstart:
    def test_exactly_one_python_block(self):
        blocks = re.findall(r"```python\n(.*?)```", README.read_text(), re.S)
        assert len(blocks) == 1, f"expected 1 python block, found {len(blocks)}"

    def test_quickstart_runs_end_to_end(self, tmp_path):
        """Every line of the quickstart executes. No cell is allowed to raise."""
        block = re.findall(r"```python\n(.*?)```", README.read_text(), re.S)[0]
        script = tmp_path / "quickstart.py"
        script.write_text(block)

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=120,
            env=_env_importing_the_package_under_test(),
        )
        assert result.returncode == 0, (
            f"README quickstart failed (exit {result.returncode}).\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        assert result.stdout.strip(), "quickstart produced no output"

    def test_quickstart_demonstrates_the_loader_raising(self):
        """The README must show the raise, not just describe it."""
        block = re.findall(r"```python\n(.*?)```", README.read_text(), re.S)[0]
        assert "load_from_cdfi_fund_url" in block
        assert "CDFIFundDownloadError" in block
        assert "except" in block

    def test_quickstart_imports_are_all_used(self):
        """0.1.0's README imported track_deployment and by_recipient_type, then
        never used either. An import list is a claim that the names matter."""
        block = re.findall(r"```python\n(.*?)```", README.read_text(), re.S)[0]
        import_block = re.search(r"from cdfifund import \((.*?)\)", block, re.S)
        assert import_block, "no `from cdfifund import (...)` block found"

        names = [
            n.strip().rstrip(",")
            for n in import_block.group(1).split("\n")
            if n.strip().rstrip(",")
        ]
        assert names, "import block is empty"

        body = block[import_block.end():]
        unused = [n for n in names if not re.search(rf"\b{re.escape(n)}\b", body)]
        assert not unused, f"imported in README quickstart but never used: {unused}"


@readme_required
class TestReadmeClaims:
    def test_stated_test_count_matches_collection(self):
        """If the README claims a test count, it must match reality."""
        text = README.read_text()
        claims = re.findall(r"(\d+) tests", text)
        if not claims:
            pytest.skip("README states no test count")

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=str(README.parent),
            timeout=300,
        )
        match = re.search(r"(\d+) tests? collected", proc.stdout)
        assert match, f"could not parse collection output:\n{proc.stdout[-2000:]}"
        actual = int(match.group(1))

        for claim in claims:
            assert int(claim) == actual, (
                f"README claims {claim} tests; pytest collects {actual}"
            )

    def test_declares_no_ingestion_path(self):
        text = README.read_text().lower()
        assert "no cdfi fund ingestion path" in text or "does not load cdfi fund data" in text

    def test_describes_sample_data_as_synthetic_not_realistic(self):
        """0.1.0's README called them "24 realistic awards"."""
        text = README.read_text()
        assert "synthetic" in text.lower()
        assert "24 realistic awards" not in text

    def test_discloses_what_0_1_0_did(self):
        text = README.read_text()
        assert "0.1.0" in text
        assert "load_from_cdfi_fund_url" in text

    def test_documents_all_three_validated_vocabularies(self):
        from cdfifund import CDFI_PROGRAMS, COMPLIANCE_STATUS_CODES, RECIPIENT_TYPES

        text = README.read_text()
        for table in (CDFI_PROGRAMS, RECIPIENT_TYPES, COMPLIANCE_STATUS_CODES):
            for code in table:
                assert f"`{code}`" in text, f"vocabulary code {code!r} undocumented in README"

    def test_documented_vocabularies_actually_validate(self):
        """The README says these raise. Prove it by making them raise.

        This test replaces one that only checked whether the code strings
        appeared in the markdown. That version passed for the entire 0.2.0
        build while `Recipient.type` -- named explicitly in the README's own
        RECIPIENT_TYPES heading -- validated nothing at all. A documentation
        test that never executes the documented behaviour tests the
        documentation's spelling, not its truth.

        Every entry below is a claim the README makes on the page. Each one is
        checked twice: an invalid value must raise, and every valid code must
        be accepted (so the guard cannot be satisfied by rejecting everything).
        """
        from cdfifund import CDFI_PROGRAMS, COMPLIANCE_STATUS_CODES, RECIPIENT_TYPES

        # (vocabulary, factory, field) for every field the README says the
        # vocabulary governs.
        claims = [
            (RECIPIENT_TYPES, _award, "recipient_type"),
            (RECIPIENT_TYPES, _recipient, "type"),
            (CDFI_PROGRAMS, _award, "program"),
            (CDFI_PROGRAMS, _record, "program"),
            (COMPLIANCE_STATUS_CODES, _record, "status"),
        ]

        for vocabulary, factory, field in claims:
            with pytest.raises(ValueError) as exc:
                factory(**{field: "DEFINITELY_NOT_A_VALID_CODE"})()
            assert field in str(exc.value), (
                f"{field}: error message does not name the field"
            )
            for code in vocabulary:
                factory(**{field: code})()

    def test_programs_received_validates_every_element(self):
        """RECIPIENT_TYPES/CDFI_PROGRAMS are list-valued in one place."""
        from cdfifund import CDFI_PROGRAMS

        _recipient(programs_received=list(CDFI_PROGRAMS))()
        with pytest.raises(ValueError, match="programs_received"):
            _recipient(programs_received=["CDFI_FA", "NOT_A_PROGRAM"])()

    def test_readme_constraints_table_names_every_dataclass_field(self):
        """B3: the constraints table read as an exhaustive carve-out while
        omitting Award.state, award_date and award_year. If a field exists, the
        table must say something about it -- including "not validated"."""
        import dataclasses

        from cdfifund import Award, ComplianceRecord, Recipient

        text = README.read_text()
        missing = []
        for cls in (Award, Recipient, ComplianceRecord):
            for f in dataclasses.fields(cls):
                if f"`{cls.__name__}.{f.name}`" not in text:
                    missing.append(f"{cls.__name__}.{f.name}")
        assert not missing, (
            "README constraints table omits these fields: " + ", ".join(missing)
        )

    def test_readme_does_not_claim_malformed_deadlines_are_dropped(self):
        """0.2.0 validates dates at construction, so the silent-drop failure
        mode the build session documented can no longer occur. A caveat that
        describes impossible behaviour is as wrong as a missing one."""
        text = README.read_text().lower()
        assert "malformed deadlines are silently dropped" not in text
        assert "vanishes from every compliance report" not in text

    def test_readme_documents_construction_time_date_validation(self):
        assert "YYYY-MM-DD" in README.read_text()

    def test_documents_recipient(self):
        """Recipient is in __all__ and was absent from the 0.1.0 README."""
        assert "Recipient(" in README.read_text()

    def test_caveats_program_effectiveness_metrics(self):
        text = README.read_text().lower()
        assert "program_effectiveness_metrics" in text
        assert "not measure effectiveness" in text or "not outcome" in text

    def test_discloses_date_today_relativity(self):
        assert "date.today()" in README.read_text()

    def test_discloses_the_deferred_limitations(self):
        """Known-but-unfixed behaviour must be disclosed, not left latent."""
        text = README.read_text()
        assert "recipient_name" in text and "recipient_id" in text, (
            "README must disclose that aggregation keys on recipient_name"
        )
        assert "first_time_recipients" in text, (
            "README must disclose what first_time_recipients actually counts"
        )
