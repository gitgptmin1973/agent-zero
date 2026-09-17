"""Compliance guardrail for outbound tool calls.

The guardrail sits between the agent's decision to call a tool and the tool
actually running. It screens the payload for personal data (APPI 個人情報 /
GDPR personal data) and for credentials, then allows, redacts or blocks the
call according to a policy.

Design rules:
  * never write detected values to disk - the audit trail stores categories,
    counts and a salted digest only (APPI 安全管理措置 / GDPR art.32).
  * never silently rewrite code that is about to be executed - redacting a
    source file would corrupt it, so code payloads are blocked instead.
  * blocking is a USER GATE: the call resumes only after the human approves
    that exact payload once, with a token that expires.

Configuration:
  env A0_GUARDRAIL_MODE = enforce | redact | audit | off   (default: enforce)
  file conf/guardrail.json overrides any policy field (see conf/guardrail.example.json)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

# no imports from the rest of the framework: the guardrail must stay importable
# on its own so it can be unit tested and audited without booting the agent
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _abs_path(*relative_paths: str) -> str:
    return os.path.join(_BASE_DIR, *relative_paths)

# --------------------------------------------------------------------------
# severities and modes
# --------------------------------------------------------------------------

CRITICAL = "critical"
HIGH = "high"
LOW = "low"

_SEVERITY_ORDER = {LOW: 0, HIGH: 1, CRITICAL: 2}

MODE_ENFORCE = "enforce"  # block critical, redact high
MODE_REDACT = "redact"  # redact everything possible, never block
MODE_AUDIT = "audit"  # log only, never change the payload
MODE_OFF = "off"  # disabled

APPROVAL_PREFIX = "GUARDRAIL-APPROVE:"
APPROVAL_TOKEN_RE = re.compile(rf"{APPROVAL_PREFIX}\s*([0-9a-f]{{12}})", re.IGNORECASE)

AUDIT_DIR = "logs/compliance"
STATE_DIR = "tmp/guardrail"
POLICY_FILE = "conf/guardrail.json"


# --------------------------------------------------------------------------
# validators
# --------------------------------------------------------------------------


def _digits(value: str) -> list[int]:
    return [int(c) for c in re.sub(r"\D", "", value)]


def my_number_valid(value: str) -> bool:
    """個人番号 (Japanese My Number) check digit, 12 digits, mod 11."""
    d = _digits(value)
    if len(d) != 12 or len(set(d)) == 1:
        return False
    total = 0
    for n, digit in enumerate(reversed(d[:11]), start=1):
        q = n + 1 if n <= 6 else n - 5
        total += digit * q
    rest = total % 11
    expected = 0 if rest <= 1 else 11 - rest
    return d[11] == expected


def luhn_valid(value: str) -> bool:
    """Payment card number check (ISO/IEC 7812 Luhn)."""
    d = _digits(value)
    if not 13 <= len(d) <= 19 or len(set(d)) == 1:
        return False
    total = 0
    for i, digit in enumerate(reversed(d)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


# --------------------------------------------------------------------------
# detectors
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Detector:
    key: str
    label: str
    severity: str
    pattern: re.Pattern
    group: int = 0
    validator: Callable[[str], bool] | None = None
    context: re.Pattern | None = None
    context_severity: str | None = None
    context_required: bool = False
    window: int = 48


def _re(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE | re.UNICODE)


# identifiers - on their own they point at a natural person
IDENTIFIER_KEYS = {
    "my_number",
    "email",
    "phone_jp",
    "person_name",
    "address_jp",
    "passport",
    "drivers_license",
    "bank_account",
    "credit_card",
}

# quasi-identifiers - only meaningful together with an identifier, otherwise
# they produce noise on ordinary research queries
CONDITIONAL_KEYS = {"health", "income", "birthdate", "postal_jp"}

DETECTORS: list[Detector] = [
    # ---- credentials ----------------------------------------------------
    Detector(
        "private_key",
        "private key block",
        CRITICAL,
        _re(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    ),
    Detector(
        "api_key",
        "API key / access token",
        CRITICAL,
        _re(
            r"(?<![A-Za-z0-9])("
            r"sk-ant-[A-Za-z0-9_\-]{20,}"
            r"|sk-[A-Za-z0-9]{20,}"
            r"|gh[pousr]_[A-Za-z0-9]{20,}"
            r"|github_pat_[A-Za-z0-9_]{20,}"
            r"|AKIA[0-9A-Z]{16}"
            r"|AIza[0-9A-Za-z_\-]{35}"
            r"|xox[abposr]-[A-Za-z0-9-]{10,}"
            r"|hf_[A-Za-z0-9]{30,}"
            r"|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
            r")"
        ),
        group=1,
    ),
    Detector(
        "credential",
        "credential assignment",
        CRITICAL,
        _re(
            r"(?:password|passwd|pwd|secret|api[_\-]?key|access[_\-]?token|"
            r"client[_\-]?secret|パスワード|認証キー|秘密鍵)"
            r"\s*[:=]\s*[\"']?([^\s\"',;]{6,})"
        ),
        group=1,
    ),
    # ---- direct identifiers ---------------------------------------------
    Detector(
        "my_number",
        "個人番号 (My Number)",
        HIGH,
        _re(r"(?<![0-9-])\d{4}[-\s]?\d{4}[-\s]?\d{4}(?![0-9-])"),
        validator=my_number_valid,
        context=_re(r"マイナンバー|個人番号|my\s*number|通知カード"),
        context_severity=CRITICAL,
    ),
    Detector(
        "credit_card",
        "payment card number",
        CRITICAL,
        _re(r"(?<![0-9-])(?:\d[ -]?){12,18}\d(?![0-9-])"),
        validator=luhn_valid,
    ),
    Detector(
        "bank_account",
        "bank account number",
        CRITICAL,
        _re(r"(?:口座番号|口座No|普通預金|当座預金|account\s*number)\D{0,12}(\d{6,8})"),
        group=1,
    ),
    Detector(
        # a bare "XX1234567" is far too common to flag on its own, so the
        # keyword has to be nearby before this counts as a finding
        "passport",
        "passport number",
        CRITICAL,
        _re(r"(?<![A-Z0-9])[A-Z]{2}\d{7}(?![A-Z0-9])"),
        context=_re(r"パスポート|旅券|passport"),
        context_required=True,
    ),
    Detector(
        # same reasoning as passport: 12 bare digits alone are just noise
        "drivers_license",
        "driver's licence number",
        CRITICAL,
        _re(r"(?<![0-9])\d{12}(?![0-9])"),
        context=_re(r"免許証|運転免許|licence|license"),
        context_required=True,
    ),
    Detector(
        "email",
        "email address",
        HIGH,
        _re(r"(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    ),
    Detector(
        "phone_jp",
        "phone number",
        HIGH,
        _re(
            r"(?<![0-9])(?:"
            r"0[789]0[-\s]?\d{4}[-\s]?\d{4}"
            r"|0\d{1,4}[-\s]\d{1,4}[-\s]\d{4}"
            r"|\+81[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4}"
            r")(?![0-9])"
        ),
    ),
    Detector(
        "person_name",
        "person name field",
        HIGH,
        _re(r"(?:氏名|お名前|代表者名|申込者|契約者名)\s*[:：]?\s*([^\s,、。\n]{2,16})"),
        group=1,
    ),
    Detector(
        "address_jp",
        "postal address",
        HIGH,
        _re(r"(?:住所|所在地|現住所|お届け先)\s*[:：]?\s*([^\n,、\s]{4,48})"),
        group=1,
    ),
    # ---- quasi identifiers ----------------------------------------------
    Detector(
        "postal_jp",
        "postal code",
        HIGH,
        _re(r"〒?\s?(?<![0-9])\d{3}-\d{4}(?![0-9])"),
    ),
    Detector(
        "birthdate",
        "date of birth",
        HIGH,
        _re(
            r"(?:生年月日|誕生日|date\s*of\s*birth|DOB)\s*[:：]?\s*"
            r"((?:19|20)\d{2}\s*[年/\-.]\s*\d{1,2}\s*[月/\-.]\s*\d{1,2}\s*日?)"
        ),
        group=1,
    ),
    Detector(
        "income",
        "income / tax amount",
        HIGH,
        _re(
            r"(?:年収|所得金額|課税所得|給与収入|源泉徴収|手取り)\D{0,12}"
            r"([0-9][0-9,]{2,}\s*(?:万円|円|万))"
        ),
        group=1,
    ),
    Detector(
        "health",
        "health information (要配慮個人情報)",
        HIGH,
        _re(
            r"(?:病名|診断名|通院歴|入院歴|服薬|要介護度|障害等級|健康保険証番号)"
            r"\s*[:：]?\s*[^\n]{0,24}"
        ),
    ),
]

DETECTORS_BY_KEY = {d.key: d for d in DETECTORS}


# --------------------------------------------------------------------------
# tool classification
# --------------------------------------------------------------------------

CLASS_NETWORK = "network"  # payload leaves the machine
CLASS_LOCAL_EXEC = "local_exec"  # code runs locally, may open a socket
CLASS_LOCAL = "local"  # stays inside this machine
CLASS_SKIP = "skip"  # never screened (messages to the data subject)

DEFAULT_SKIP_TOOLS = ["response", "task_done", "input"]
DEFAULT_LOCAL_TOOLS = [
    "call_subordinate",
    "memory_save",
    "memory_load",
    "memory_delete",
    "memory_forget",
    "behaviour_adjustment",
    "scheduler",
    "vision_load",
    "unknown",
]
DEFAULT_LOCAL_EXEC_TOOLS = ["code_execution_tool"]
DEFAULT_NETWORK_TOOLS = [
    "knowledge_tool",
    "search_engine",
    "webpage_content_tool",
    "browser_agent",
    "browser",
    "document_query",
]

# code that is about to reach the network
EGRESS_HINTS = re.compile(
    r"(?i)(https?://|\bcurl\b|\bwget\b|\bscp\b|\brsync\b|\bftp\b|\bnc\b|\bnetcat\b"
    r"|requests\.(?:get|post|put|patch|delete)|urllib|httpx|aiohttp|websocket"
    r"|smtplib|sendmail|boto3|paramiko|git\s+push|gh\s+(?:pr|issue|release))"
)


# --------------------------------------------------------------------------
# policy
# --------------------------------------------------------------------------


@dataclass
class Policy:
    mode: str = MODE_ENFORCE
    block_severity: str = CRITICAL
    redact_severity: str = HIGH
    approval_ttl_seconds: int = 1800
    allowlist: list[str] = field(default_factory=list)
    disabled_detectors: list[str] = field(default_factory=list)
    skip_tools: list[str] = field(default_factory=lambda: list(DEFAULT_SKIP_TOOLS))
    local_tools: list[str] = field(default_factory=lambda: list(DEFAULT_LOCAL_TOOLS))
    local_exec_tools: list[str] = field(
        default_factory=lambda: list(DEFAULT_LOCAL_EXEC_TOOLS)
    )
    network_tools: list[str] = field(default_factory=lambda: list(DEFAULT_NETWORK_TOOLS))
    audit: bool = True

    def classify(self, tool_name: str) -> str:
        name = (tool_name or "").strip()
        if name in self.skip_tools:
            return CLASS_SKIP
        if name in self.local_exec_tools:
            return CLASS_LOCAL_EXEC
        if name in self.local_tools:
            return CLASS_LOCAL
        if name in self.network_tools:
            return CLASS_NETWORK
        # MCP tools are addressed as "<server>.<tool>" and are remote by nature
        if "." in name:
            return CLASS_NETWORK
        # fail closed: an unknown tool is treated as if it could egress
        return CLASS_NETWORK


_policy_cache: tuple[float, Policy] | None = None


def get_policy(refresh: bool = False) -> Policy:
    """Policy from conf/guardrail.json, overridden by A0_GUARDRAIL_MODE."""
    global _policy_cache
    now = time.time()
    if not refresh and _policy_cache and now - _policy_cache[0] < 10:
        return _policy_cache[1]

    policy = Policy()
    path = _abs_path(POLICY_FILE)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            for key, value in data.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
        except Exception as exc:
            # a broken policy file must not silently disable the guardrail,
            # but it must not pass unnoticed either
            audit({"action": "policy_error", "file": POLICY_FILE, "error": str(exc)})

    env_mode = os.getenv("A0_GUARDRAIL_MODE", "").strip().lower()
    if env_mode in (MODE_ENFORCE, MODE_REDACT, MODE_AUDIT, MODE_OFF):
        policy.mode = env_mode

    _policy_cache = (now, policy)
    return policy


# --------------------------------------------------------------------------
# findings
# --------------------------------------------------------------------------


@dataclass
class Finding:
    key: str
    label: str
    severity: str
    start: int
    end: int
    value: str

    @property
    def token(self) -> str:
        return f"[REDACTED:{self.key}#{_short_digest(self.value)}]"


def _short_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:4]


def _max_severity(findings: Iterable[Finding]) -> str | None:
    best = None
    for finding in findings:
        if best is None or _SEVERITY_ORDER[finding.severity] > _SEVERITY_ORDER[best]:
            best = finding.severity
    return best


def _at_least(severity: str, threshold: str) -> bool:
    # unknown names in a hand-edited policy must not raise inside the agent loop
    return _SEVERITY_ORDER.get(severity, 0) >= _SEVERITY_ORDER.get(threshold, 99)


def scan(
    text: str,
    policy: Policy | None = None,
    has_identifier_context: bool = False,
) -> list[Finding]:
    """Return the sensitive spans found in `text`, highest severity first."""
    if not text:
        return []
    policy = policy or get_policy()
    allowlist = [item for item in policy.allowlist if item]
    findings: list[Finding] = []

    for detector in DETECTORS:
        if detector.key in policy.disabled_detectors:
            continue
        for match in detector.pattern.finditer(text):
            try:
                value = match.group(detector.group)
            except IndexError:
                value = match.group(0)
            if not value:
                continue
            if detector.validator and not detector.validator(value):
                continue
            if any(allowed in value for allowed in allowlist):
                continue

            severity = detector.severity
            if detector.context is not None:
                start = max(0, match.start() - detector.window)
                end = min(len(text), match.end() + detector.window)
                has_context = bool(detector.context.search(text[start:end]))
                if not has_context and detector.context_required:
                    continue
                if has_context and detector.context_severity:
                    severity = detector.context_severity

            findings.append(
                Finding(
                    key=detector.key,
                    label=detector.label,
                    severity=severity,
                    start=match.start(detector.group),
                    end=match.end(detector.group),
                    value=value,
                )
            )

    findings = _drop_conditional(findings, has_identifier_context)
    return _drop_overlaps(findings)


def _drop_conditional(
    findings: list[Finding], has_identifier_context: bool = False
) -> list[Finding]:
    """Quasi-identifiers count only next to a direct identifier.

    `has_identifier_context` carries that fact across arguments: a name in one
    tool argument still qualifies an income figure in another.
    """
    if not has_identifier_context and not any(
        f.key in IDENTIFIER_KEYS for f in findings
    ):
        return [f for f in findings if f.key not in CONDITIONAL_KEYS]
    return findings


def _drop_overlaps(findings: list[Finding]) -> list[Finding]:
    """Keep the strongest finding on overlapping spans."""
    ordered = sorted(
        findings,
        key=lambda f: (-_SEVERITY_ORDER[f.severity], -(f.end - f.start), f.start),
    )
    kept: list[Finding] = []
    for finding in ordered:
        if any(finding.start < k.end and k.start < finding.end for k in kept):
            continue
        kept.append(finding)
    return sorted(kept, key=lambda f: f.start)


def redact(
    text: str, findings: list[Finding], threshold: str = HIGH
) -> tuple[str, int]:
    """Replace findings at or above `threshold` with non-reversible tokens."""
    targets = [f for f in findings if _at_least(f.severity, threshold)]
    if not targets:
        return text, 0
    out = text
    for finding in sorted(targets, key=lambda f: f.start, reverse=True):
        out = out[: finding.start] + finding.token + out[finding.end :]
    return out, len(targets)


def summarize(findings: list[Finding]) -> str:
    counts: dict[str, int] = {}
    for finding in findings:
        label = f"{finding.label} [{finding.severity}]"
        counts[label] = counts.get(label, 0) + 1
    return ", ".join(f"{label} x{count}" for label, count in sorted(counts.items()))


# --------------------------------------------------------------------------
# approvals (USER GATE)
# --------------------------------------------------------------------------


def fingerprint(tool_name: str, args: Any) -> str:
    payload = json.dumps(
        {"tool": tool_name, "args": args}, ensure_ascii=False, sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _approvals_path() -> str:
    return _abs_path(STATE_DIR, "approvals.json")


def _load_approvals() -> dict[str, dict[str, Any]]:
    path = _approvals_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _save_approvals(data: dict[str, dict[str, Any]]) -> None:
    os.makedirs(_abs_path(STATE_DIR), exist_ok=True)
    with open(_approvals_path(), "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def grant_approval(approval_id: str, ttl_seconds: int | None = None) -> bool:
    """Register a single-use approval for one payload fingerprint."""
    approval_id = (approval_id or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{12}", approval_id):
        return False
    ttl = ttl_seconds or get_policy().approval_ttl_seconds
    data = _load_approvals()
    data[approval_id] = {
        "granted_at": time.time(),
        "expires_at": time.time() + ttl,
        "used": False,
    }
    _save_approvals(_prune(data))
    return True


def consume_approval(approval_id: str) -> bool:
    """Spend an approval. Returns False when missing, spent or expired."""
    data = _load_approvals()
    entry = data.get(approval_id)
    if not entry or entry.get("used"):
        return False
    if entry.get("expires_at", 0) < time.time():
        data.pop(approval_id, None)
        _save_approvals(data)
        return False
    entry["used"] = True
    entry["used_at"] = time.time()
    _save_approvals(_prune(data))
    return True


def extract_approval_ids(text: str) -> list[str]:
    if not text:
        return []
    return [match.group(1).lower() for match in APPROVAL_TOKEN_RE.finditer(text)]


def _prune(data: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    now = time.time()
    return {
        key: value
        for key, value in data.items()
        if value.get("expires_at", 0) > now - 86400
    }


# --------------------------------------------------------------------------
# audit trail - categories only, never the detected value
# --------------------------------------------------------------------------


def audit(event: dict[str, Any]) -> None:
    try:
        directory = _abs_path(AUDIT_DIR)
        os.makedirs(directory, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        with open(
            os.path.join(directory, f"guardrail-{day}.jsonl"), "a", encoding="utf-8"
        ) as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        # auditing must never break the agent loop
        pass


# --------------------------------------------------------------------------
# verdict
# --------------------------------------------------------------------------


@dataclass
class Verdict:
    action: str  # allow | redact | block
    args: dict[str, Any]
    payload_message: str
    findings: list[Finding] = field(default_factory=list)
    notice: str = ""
    approval_id: str = ""
    tool_class: str = CLASS_LOCAL
    redactions: int = 0

    @property
    def blocked(self) -> bool:
        return self.action == "block"


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _map_strings(value: Any, fn: Callable[[str], str]) -> Any:
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, dict):
        return {key: _map_strings(item, fn) for key, item in value.items()}
    if isinstance(value, list):
        return [_map_strings(item, fn) for item in value]
    if isinstance(value, tuple):
        return tuple(_map_strings(item, fn) for item in value)
    return value


def screen(
    tool_name: str,
    args: Any,
    message: str = "",
    policy: Policy | None = None,
    context_id: str = "",
    agent_name: str = "",
) -> Verdict:
    """Screen one tool call. Pure function over the payload - no agent needed."""
    policy = policy or get_policy()
    args = args if isinstance(args, dict) else {}
    tool_class = policy.classify(tool_name)

    if policy.mode == MODE_OFF or tool_class == CLASS_SKIP:
        return Verdict("allow", args, message, tool_class=tool_class)

    joined = "\n".join(_walk_strings(args))
    findings = scan(joined, policy)

    if not findings:
        return Verdict("allow", args, message, tool_class=tool_class)

    worst = _max_severity(findings) or LOW
    approval_id = fingerprint(tool_name, args)

    # local execution only matters once the code reaches out to the network
    if tool_class == CLASS_LOCAL_EXEC and not EGRESS_HINTS.search(joined):
        tool_class = CLASS_LOCAL

    audit_event = {
        "context": context_id,
        "agent": agent_name,
        "tool": tool_name,
        "tool_class": tool_class,
        "mode": policy.mode,
        "severity": worst,
        "categories": sorted({f.key for f in findings}),
        "counts": {
            key: sum(1 for f in findings if f.key == key)
            for key in sorted({f.key for f in findings})
        },
        "payload_sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        "fingerprint": approval_id,
    }

    # audit-only classes and modes: record and pass through untouched
    if tool_class == CLASS_LOCAL or policy.mode == MODE_AUDIT:
        if policy.audit:
            audit({**audit_event, "action": "audit"})
        return Verdict("allow", args, message, findings=findings, tool_class=tool_class)

    blocking = policy.mode == MODE_ENFORCE and _at_least(worst, policy.block_severity)

    if blocking and consume_approval(approval_id):
        if policy.audit:
            audit({**audit_event, "action": "allow_approved"})
        return Verdict(
            "allow",
            args,
            message,
            findings=findings,
            tool_class=tool_class,
            approval_id=approval_id,
        )

    if blocking:
        if policy.audit:
            audit({**audit_event, "action": "block"})
        return Verdict(
            "block",
            args,
            message,
            findings=findings,
            notice=_block_message(tool_name, tool_class, findings, approval_id),
            approval_id=approval_id,
            tool_class=tool_class,
        )

    # redaction path - never applied to code that is about to be executed
    if tool_class == CLASS_LOCAL_EXEC:
        if policy.audit:
            audit({**audit_event, "action": "block_code"})
        return Verdict(
            "block",
            args,
            message,
            findings=findings,
            notice=_block_message(tool_name, tool_class, findings, approval_id),
            approval_id=approval_id,
            tool_class=tool_class,
        )

    threshold = LOW if policy.mode == MODE_REDACT else policy.redact_severity
    total = 0

    has_identifier = any(f.key in IDENTIFIER_KEYS for f in findings)

    def _apply(text: str) -> str:
        nonlocal total
        local_findings = scan(text, policy, has_identifier_context=has_identifier)
        redacted, count = redact(text, local_findings, threshold)
        total += count
        return redacted

    new_args = _map_strings(args, _apply)
    new_message = _apply(message) if message else message

    if total == 0:
        return Verdict("allow", args, message, findings=findings, tool_class=tool_class)

    if policy.audit:
        audit({**audit_event, "action": "redact", "redactions": total})

    return Verdict(
        "redact",
        new_args,
        new_message,
        findings=findings,
        notice=_redact_message(tool_name, findings, total),
        tool_class=tool_class,
        redactions=total,
    )


def _block_message(
    tool_name: str, tool_class: str, findings: list[Finding], approval_id: str
) -> str:
    reason = summarize([f for f in findings if _at_least(f.severity, HIGH)] or findings)
    code_note = (
        "\nThis payload is source code, so it is blocked rather than redacted - "
        "masking it would corrupt the program.\n"
        if tool_class == CLASS_LOCAL_EXEC
        else ""
    )
    return (
        "## COMPLIANCE GUARDRAIL - CALL BLOCKED\n\n"
        f"Tool `{tool_name}` was NOT executed.\n"
        f"Detected in the outbound payload: {reason}\n"
        f"{code_note}\n"
        "Policy: personal data (APPI 個人情報 / GDPR personal data) and credentials "
        "must not leave this machine without the user's explicit approval "
        "(USER GATE).\n\n"
        "Do this now:\n"
        "1. Use the `response` tool to tell the user which CATEGORIES were detected. "
        "Never repeat the detected values themselves.\n"
        "2. Offer the safe option first: remove or mask the sensitive part and retry.\n"
        "3. If the user wants the original payload sent anyway, they must reply with "
        f"the exact token `{APPROVAL_PREFIX}{approval_id}`.\n\n"
        "That approval is single-use, time limited, and bound to this exact payload - "
        "you cannot grant it yourself and you must not invent the token."
    )


def _redact_message(tool_name: str, findings: list[Finding], count: int) -> str:
    return (
        "## COMPLIANCE GUARDRAIL - PAYLOAD REDACTED\n\n"
        f"{count} value(s) were masked before `{tool_name}` ran: "
        f"{summarize(findings)}\n"
        "The tool saw `[REDACTED:<category>#<digest>]` placeholders instead of the "
        "originals. If the result is unusable, tell the user which categories were "
        "masked and ask how to proceed - do not try to work around the mask."
    )


# --------------------------------------------------------------------------
# agent facing entry point
# --------------------------------------------------------------------------


def screen_tool_call(agent: Any, tool_name: str, args: Any, message: str = "") -> Verdict:
    context_id = ""
    agent_name = ""
    try:
        context_id = getattr(getattr(agent, "context", None), "id", "") or ""
        agent_name = getattr(agent, "agent_name", "") or ""
    except Exception:
        pass
    return screen(
        tool_name=tool_name,
        args=args,
        message=message,
        context_id=context_id,
        agent_name=agent_name,
    )


def register_approvals_from_text(text: str) -> list[str]:
    """Called on every user message - grants the tokens the human typed."""
    granted = []
    for approval_id in extract_approval_ids(text):
        if grant_approval(approval_id):
            granted.append(approval_id)
            audit({"action": "approval_granted", "fingerprint": approval_id})
    return granted


def status() -> dict[str, Any]:
    policy = get_policy(refresh=True)
    return {
        "mode": policy.mode,
        "detectors": len(DETECTORS) - len(policy.disabled_detectors),
        "block_severity": policy.block_severity,
        "redact_severity": policy.redact_severity,
        "audit_dir": AUDIT_DIR,
        "policy_file": POLICY_FILE if os.path.isfile(_abs_path(POLICY_FILE)) else None,
    }
