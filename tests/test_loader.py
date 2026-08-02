"""Tests for award data loader."""

import http.server
import socketserver
import threading

import pytest

from cdfifund.data.loader import load_sample_awards, load_from_cdfi_fund_url
from cdfifund.data.schema import Award
from cdfifund.exceptions import CDFIFundDownloadError, CDFIFundTrackerError


@pytest.fixture
def live_http_server():
    """A real local HTTP server returning HTTP 200 with arbitrary bytes.

    This is the fixture that distinguishes 0.2.0 from 0.1.0. Tests that only
    exercise unreachable URLs pass against both versions, because 0.1.0's
    except-clause and its success path returned the same sample data.
    """
    payload = b"THIS IS NOT CDFI FUND AWARD DATA."

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{httpd.server_address[1]}/awards.csv"
        httpd.shutdown()
        thread.join(timeout=5)


class TestLoadSampleAwards:
    def test_returns_list(self):
        awards = load_sample_awards()
        assert isinstance(awards, list)

    def test_non_empty(self):
        awards = load_sample_awards()
        assert len(awards) >= 10

    def test_all_are_awards(self):
        for a in load_sample_awards():
            assert isinstance(a, Award)

    def test_multiple_programs_represented(self):
        awards = load_sample_awards()
        programs = {a.program for a in awards}
        assert len(programs) >= 5

    def test_multiple_years(self):
        awards = load_sample_awards()
        years = {a.award_year for a in awards}
        assert len(years) >= 3

    def test_multiple_states(self):
        awards = load_sample_awards()
        states = {a.state for a in awards}
        assert len(states) >= 5

    def test_bgp_award_large(self):
        awards = load_sample_awards()
        bgp = [a for a in awards if a.program == "BGP"]
        assert len(bgp) > 0
        assert all(a.award_amount >= 100_000_000 for a in bgp)

    def test_positive_amounts(self):
        for a in load_sample_awards():
            assert a.award_amount > 0

    def test_exact_sample_count_is_24(self):
        assert len(load_sample_awards()) == 24

    def test_still_works_after_loader_was_made_to_raise(self):
        """The sample path stays reachable -- only through its named function."""
        awards = load_sample_awards()
        assert len(awards) == 24
        assert all(isinstance(a, Award) for a in awards)


class TestLoadFromCDFIFundUrlRaises:
    """0.1.0 returned 24 synthetic awards from every path, including HTTP 200.

    0.2.0 raises unconditionally: there is no CDFI Fund parser, so there is no
    input for which this function can legitimately succeed.
    """

    def test_raises_on_reachable_url_returning_valid_bytes(self, live_http_server):
        """THE mutation-proof test: 0.1.0 returned samples here with HTTP 200."""
        with pytest.raises(CDFIFundDownloadError):
            load_from_cdfi_fund_url(live_http_server)

    def test_raises_on_none_url(self):
        with pytest.raises(CDFIFundDownloadError):
            load_from_cdfi_fund_url(None)

    def test_raises_with_no_argument_at_all(self):
        with pytest.raises(CDFIFundDownloadError):
            load_from_cdfi_fund_url()

    def test_raises_on_unreachable_url(self):
        with pytest.raises(CDFIFundDownloadError):
            load_from_cdfi_fund_url("http://127.0.0.1:1/nope.csv")

    def test_raises_on_malformed_url(self):
        with pytest.raises(CDFIFundDownloadError):
            load_from_cdfi_fund_url("not-a-url-at-all")

    def test_message_names_load_sample_awards(self, live_http_server):
        with pytest.raises(CDFIFundDownloadError) as exc:
            load_from_cdfi_fund_url(live_http_server)
        assert "load_sample_awards" in str(exc.value)

    def test_message_states_no_parser_was_implemented(self, live_http_server):
        with pytest.raises(CDFIFundDownloadError) as exc:
            load_from_cdfi_fund_url(live_http_server)
        assert "parser" in str(exc.value).lower()

    def test_message_discloses_that_0_1_0_returned_sample_data(self, live_http_server):
        with pytest.raises(CDFIFundDownloadError) as exc:
            load_from_cdfi_fund_url(live_http_server)
        msg = str(exc.value)
        assert "0.1.0" in msg
        assert "sample data" in msg.lower()

    def test_message_is_identical_regardless_of_url_reachability(self, live_http_server):
        """No path is more successful than another -- the message must not imply one is."""
        with pytest.raises(CDFIFundDownloadError) as reachable:
            load_from_cdfi_fund_url(live_http_server)
        with pytest.raises(CDFIFundDownloadError) as unreachable:
            load_from_cdfi_fund_url("http://127.0.0.1:1/nope.csv")
        with pytest.raises(CDFIFundDownloadError) as none_url:
            load_from_cdfi_fund_url(None)
        assert str(reachable.value) == str(unreachable.value) == str(none_url.value)

    def test_never_returns_a_list(self, live_http_server):
        """A function that cannot succeed must not have a success-shaped return."""
        for arg in (live_http_server, None, "http://127.0.0.1:1/x", "garbage"):
            with pytest.raises(CDFIFundDownloadError):
                result = load_from_cdfi_fund_url(arg)
                pytest.fail(f"returned {type(result).__name__} for {arg!r}")


class TestExceptionHierarchy:
    def test_download_error_subclasses_tracker_error(self):
        assert issubclass(CDFIFundDownloadError, CDFIFundTrackerError)

    def test_tracker_error_subclasses_exception(self):
        assert issubclass(CDFIFundTrackerError, Exception)

    def test_both_exported_from_package_root(self):
        import cdfifund

        assert cdfifund.CDFIFundTrackerError is CDFIFundTrackerError
        assert cdfifund.CDFIFundDownloadError is CDFIFundDownloadError
        assert "CDFIFundTrackerError" in cdfifund.__all__
        assert "CDFIFundDownloadError" in cdfifund.__all__

    def test_catchable_as_base_class(self, live_http_server):
        with pytest.raises(CDFIFundTrackerError):
            load_from_cdfi_fund_url(live_http_server)


class TestSampleDataIsReachableOnlyByName:
    """The correction is the separation: fixtures come only from the function
    whose name says they are fixtures. A future silent fallback would have to
    call load_sample_awards() from inside the package to reintroduce the bug.
    """

    @staticmethod
    def _package_sources():
        import pathlib

        import cdfifund

        root = pathlib.Path(cdfifund.__file__).resolve().parent
        return sorted(root.rglob("*.py"))

    def test_no_module_in_the_package_calls_load_sample_awards(self):
        import re

        offenders = []
        for path in self._package_sources():
            if path.name == "loader.py":
                continue  # defines it
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                code = line.split("#", 1)[0]
                if re.search(r"\bload_sample_awards\s*\(", code):
                    offenders.append(f"{path.name}:{lineno}: {line.strip()}")
        assert not offenders, (
            "package code calls load_sample_awards() internally -- that is how a "
            "silent sample-data fallback gets reintroduced:\n" + "\n".join(offenders)
        )

    def test_loader_module_never_calls_it_either(self):
        """load_from_cdfi_fund_url must not reach the fixtures by any route."""
        import inspect

        from cdfifund.data import loader

        source = inspect.getsource(loader.load_from_cdfi_fund_url)
        assert "load_sample_awards(" not in source

    def test_package_defines_no_other_zero_arg_award_source(self):
        """Only load_sample_awards() may hand back awards with no input."""
        import inspect

        import cdfifund

        producers = []
        for name in cdfifund.__all__:
            obj = getattr(cdfifund, name)
            if not inspect.isfunction(obj) or name == "load_sample_awards":
                continue
            params = inspect.signature(obj).parameters
            if all(p.default is not inspect.Parameter.empty for p in params.values()):
                try:
                    result = obj()
                except Exception:
                    continue  # raising is the correct behavior
                if isinstance(result, list) and any(
                    isinstance(x, Award) for x in result
                ):
                    producers.append(name)
        assert not producers, f"undeclared zero-arg award sources: {producers}"
