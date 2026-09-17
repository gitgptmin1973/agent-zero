# Compliance guardrail

The guardrail sits between the agent's decision to call a tool and the tool
actually running. It screens the payload for personal data and credentials,
then allows, redacts, or blocks the call.

It exists because a policy written in a prompt is advice, not a control: the
model can forget it, and a subordinate agent or an MCP server never read it.
This runs in `agent.py` on every tool call, including MCP tools, and the model
cannot switch it off.

**What it is not:** it is not a certification of APPI, GDPR, or EU AI Act
compliance, and it is not a whole-machine DLP. It covers what Agent Zero sends
through its own tools. Anything you paste into a browser, a desktop chat client,
or a cloud sync folder never passes through it.

## Decision table

| Tool class | Examples | Critical finding | High finding | Low finding |
|---|---|---|---|---|
| `skip` | `response`, `task_done`, `input` | not screened | not screened | not screened |
| `local` | `memory_*`, `call_subordinate`, `scheduler` | audit | audit | audit |
| `local_exec` | `code_execution_tool` with no network call | audit | audit | audit |
| `local_exec` | `code_execution_tool` reaching the network | **block** | **block** | audit |
| `network` | `search_engine`, `webpage_content_tool`, `browser_agent`, any MCP tool | **block** | **redact** | audit |

Unknown tool names default to `network` — the guardrail fails closed.

Two deliberate asymmetries:

- **`response` is never screened.** It is the message to the user, who owns the
  data. Masking it would hide the user's own information from them.
- **Code is blocked, never redacted.** Rewriting a value inside a program would
  corrupt it silently. A block is visible; a corrupted script is not.

## Severities

| Severity | Categories |
|---|---|
| critical | API keys, access tokens, private keys, password assignments, 個人番号 (with context), payment card numbers (Luhn-valid), bank account numbers, passport and licence numbers (with context) |
| high | names, postal addresses, phone numbers, email addresses, postal codes, dates of birth, income and tax figures, health information (要配慮個人情報), 個人番号 without context |
| low | reserved for audit-only signals |

Two rules keep false positives down:

- **Validators, not just patterns.** 個人番号 is checked against its mod-11 check
  digit, payment cards against Luhn. A random 12- or 16-digit number does not
  trip the guardrail.
- **Quasi-identifiers need an identifier.** Dates of birth, income figures,
  health terms and postal codes only count when the same payload also carries a
  direct identifier. `要介護度3の認定基準` is a research question; `氏名: …
  要介護度3` is personal data.

## The USER GATE

When a call is blocked, the agent is told which *categories* were found — never
the values — and is instructed to ask the user. Approval is a token only the
human can supply:

```
GUARDRAIL-APPROVE:37381f317d5d
```

The token is the fingerprint of that exact payload. It is single-use, expires
after 30 minutes by default, and unlocks nothing else. The agent cannot mint one
for itself: it is registered by a `message_loop_start` extension that reads the
user's own message.

## Audit trail

Every decision is appended to `logs/compliance/guardrail-YYYY-MM-DD.jsonl`:

```json
{"ts":"2026-09-17T05:20:40Z","tool":"search_engine","tool_class":"network",
 "mode":"enforce","severity":"critical","categories":["my_number"],
 "counts":{"my_number":1},"payload_sha256":"…","fingerprint":"37381f317d5d",
 "action":"block"}
```

Categories, counts and a digest — never the detected value. Storing the value
would recreate the exposure the guardrail exists to prevent.

## Configuration

Mode, by environment variable (wins over the file):

```bash
A0_GUARDRAIL_MODE=enforce   # block critical, redact high  (default)
A0_GUARDRAIL_MODE=redact    # mask everything, never block
A0_GUARDRAIL_MODE=audit     # log only, change nothing
A0_GUARDRAIL_MODE=off       # disabled
```

Everything else lives in `conf/guardrail.json` — copy `conf/guardrail.example.json`
and edit. Useful fields:

- `allowlist` — literal strings never flagged, e.g. a published company address.
- `disabled_detectors` — detector keys to switch off.
- `network_tools` / `local_tools` / `local_exec_tools` / `skip_tools` — move a
  custom tool into the right egress class.
- `approval_ttl_seconds` — how long a USER GATE token stays valid.

## Tests

```bash
python3 tests/test_guardrail.py     # standalone, no dependencies
pytest tests/test_guardrail.py      # or under pytest
```

## Files

| Path | Role |
|---|---|
| `python/helpers/guardrail.py` | detectors, policy, decisions, approvals, audit |
| `agent.py` (`process_tools`) | the enforcement point |
| `python/extensions/message_loop_start/_09_guardrail_approvals.py` | registers user tokens |
| `python/extensions/system_prompt/_30_compliance_guardrail.py` | tells the agent the rules |
| `prompts/default/agent.system.compliance.md` | the prompt text |
| `conf/guardrail.example.json` | policy template |
