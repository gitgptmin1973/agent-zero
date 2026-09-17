"""Self-contained tests for the compliance guardrail.

Runs under pytest, or standalone:  python3 tests/test_guardrail.py
No framework imports, so it works without the agent's dependencies installed.
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.helpers import guardrail as g  # noqa: E402


def _isolate():
    """Point the approval store and audit trail at a throwaway directory."""
    tmp = tempfile.mkdtemp(prefix="guardrail-test-")
    g._BASE_DIR = tmp  # type: ignore[attr-defined]
    g._policy_cache = None  # type: ignore[attr-defined]
    os.environ["A0_GUARDRAIL_MODE"] = "enforce"
    return tmp


# --- validators -----------------------------------------------------------


def test_my_number_check_digit():
    assert g.my_number_valid("123456789018")
    assert not g.my_number_valid("123456789012")
    assert not g.my_number_valid("111111111111")  # repdigit is not a real number
    assert not g.my_number_valid("12345678901")  # wrong length


def test_luhn():
    assert g.luhn_valid("4242424242424242")
    assert not g.luhn_valid("4242424242424243")
    assert not g.luhn_valid("1234")


# --- detection ------------------------------------------------------------


def test_detects_credentials_and_identifiers():
    keys = {f.key for f in g.scan("ANTHROPIC_API_KEY=sk-ant-api03-" + "a" * 24)}
    assert "api_key" in keys

    keys = {f.key for f in g.scan("氏名: 山田太郎 電話 090-1234-5678 taro@example.com")}
    assert {"person_name", "phone_jp", "email"} <= keys


def test_my_number_severity_rises_with_context():
    bare = g.scan("整理番号 123456789018 を控える")
    assert [f.severity for f in bare] == [g.HIGH]
    with_context = g.scan("マイナンバー 123456789018")
    assert [f.severity for f in with_context] == [g.CRITICAL]


def test_ordinary_queries_are_not_flagged():
    for text in (
        "Python の requests でリトライする方法",
        "要介護度3の認定基準について教えて",  # health term with no identifier
        "2024年4月1日に施行された改正法",  # bare date, no identifier
        "エラーコード 000000000000 の意味",
    ):
        assert g.scan(text) == [], text


def test_quasi_identifier_needs_an_identifier():
    assert g.scan("年収 6,000,000 円の場合の控除") == []
    findings = {f.key for f in g.scan("氏名: 山田太郎 年収 6,000,000 円")}
    assert "income" in findings and "person_name" in findings


def test_identifier_in_one_argument_qualifies_another():
    _isolate()
    verdict = g.screen(
        "search_engine", {"who": "氏名: 山田太郎", "what": "年収 6,000,000 円の控除"}
    )
    assert verdict.action == "redact"
    assert "山田太郎" not in verdict.args["who"]
    assert "6,000,000" not in verdict.args["what"]


def test_unknown_severity_in_policy_does_not_raise():
    _isolate()
    policy = g.get_policy(refresh=True)
    policy.block_severity = "typo"
    verdict = g.screen("search_engine", {"query": "マイナンバー 123456789018"}, policy=policy)
    assert verdict.action in ("redact", "allow")  # degrades, never crashes


def test_redaction_is_not_reversible():
    text = "連絡先 taro@example.com"
    findings = g.scan(text)
    redacted, count = g.redact(text, findings, g.HIGH)
    assert count == 1
    assert "taro@example.com" not in redacted
    assert "[REDACTED:email#" in redacted


# --- decisions ------------------------------------------------------------


def test_network_call_with_critical_data_is_blocked():
    _isolate()
    verdict = g.screen("search_engine", {"query": "マイナンバー 123456789018"})
    assert verdict.action == "block"
    assert verdict.approval_id
    assert "123456789018" not in verdict.notice  # the notice never echoes the value


def test_network_call_with_high_data_is_redacted():
    _isolate()
    verdict = g.screen("search_engine", {"query": "氏名: 山田太郎 の与信"})
    assert verdict.action == "redact"
    assert "山田太郎" not in verdict.args["query"]


def test_response_to_the_user_is_never_screened():
    _isolate()
    verdict = g.screen("response", {"text": "マイナンバー 123456789018"})
    assert verdict.action == "allow"
    assert verdict.args["text"] == "マイナンバー 123456789018"


def test_local_code_is_audited_but_not_blocked():
    _isolate()
    code = "email = 'taro@example.com'\nprint(email)"
    verdict = g.screen("code_execution_tool", {"code": code})
    assert verdict.action == "allow"
    assert verdict.args["code"] == code


def test_code_that_reaches_the_network_is_blocked_not_rewritten():
    _isolate()
    code = "import requests\nrequests.post('https://x.test', json={'k':'sk-ant-api03-" + "a" * 24 + "'})"
    verdict = g.screen("code_execution_tool", {"code": code})
    assert verdict.action == "block"
    assert verdict.args["code"] == code  # never silently corrupted


def test_mcp_and_unknown_tools_default_to_network():
    policy = g.get_policy(refresh=True)
    assert policy.classify("notion.search") == g.CLASS_NETWORK
    assert policy.classify("some_future_tool") == g.CLASS_NETWORK
    assert policy.classify("memory_save") == g.CLASS_LOCAL


# --- user gate ------------------------------------------------------------


def test_approval_is_single_use_and_payload_bound():
    _isolate()
    args = {"query": "マイナンバー 123456789018"}
    first = g.screen("search_engine", args)
    assert first.action == "block"

    assert g.grant_approval(first.approval_id)
    assert g.screen("search_engine", args).action == "allow"
    assert g.screen("search_engine", args).action == "block"  # not replayable

    # an approval for one payload does not unlock a different one
    assert g.grant_approval(first.approval_id)
    other = {"query": "マイナンバー 123456789026"}
    assert g.screen("search_engine", other).action == "block"


def test_expired_approval_is_refused():
    _isolate()
    args = {"query": "マイナンバー 123456789018"}
    blocked = g.screen("search_engine", args)
    g.grant_approval(blocked.approval_id, ttl_seconds=-1)
    assert g.screen("search_engine", args).action == "block"


def test_only_well_formed_tokens_are_accepted():
    _isolate()
    assert not g.grant_approval("not-a-token")
    assert not g.grant_approval("")
    assert g.extract_approval_ids("承認します GUARDRAIL-APPROVE:0123456789ab") == [
        "0123456789ab"
    ]
    assert g.extract_approval_ids("no token here") == []


# --- audit trail ----------------------------------------------------------


def test_audit_trail_never_stores_the_detected_value():
    tmp = _isolate()
    g.screen("search_engine", {"query": "マイナンバー 123456789018"})
    log_dir = os.path.join(tmp, g.AUDIT_DIR)
    written = [os.path.join(log_dir, name) for name in os.listdir(log_dir)]
    assert written
    body = "".join(open(path, encoding="utf-8").read() for path in written)
    assert "123456789018" not in body
    assert "my_number" in body and "block" in body


def test_mode_off_disables_everything():
    _isolate()
    os.environ["A0_GUARDRAIL_MODE"] = "off"
    g._policy_cache = None  # type: ignore[attr-defined]
    try:
        verdict = g.screen("search_engine", {"query": "マイナンバー 123456789018"})
        assert verdict.action == "allow"
    finally:
        os.environ["A0_GUARDRAIL_MODE"] = "enforce"
        g._policy_cache = None  # type: ignore[attr-defined]


def _main() -> int:
    base = g._BASE_DIR  # type: ignore[attr-defined]
    failures = []
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures.append((name, exc))
            print(f"  FAIL {name}: {exc}")
    g._BASE_DIR = base  # type: ignore[attr-defined]
    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_main())
