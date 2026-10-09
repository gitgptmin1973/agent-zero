# Message

A chat bubble whose colour names who is speaking: the user, the agent, a tool, a subordinate, or the system.

Static rendition, hand-written from `webui/index.css .message, .message-* (lines 573–712, light 1941–1999)`.

## When to use
Every entry in the chat history is one Message. Pick the type from the event that produced it; never pick a type for its colour.

| type class | event | tokens |
|---|---|---|
| `a0-msg-user` | the person's prompt, right-aligned, tail bottom-right | `msg-user-bg` / `msg-user-fg` |
| `a0-msg-default` | plain agent output | `msg-default-*` |
| `a0-msg-agent` | agent thinking / headline + kvps | `msg-agent-*` |
| `a0-msg-response` | final answer to the user (0.9rem, min 255px) | `msg-response-*` |
| `a0-msg-delegation` | call to a subordinate agent | `msg-delegation-*` |
| `a0-msg-tool` | tool call and its arguments | `msg-tool-*` |
| `a0-msg-code` / `a0-msg-browser` | code execution / browser agent | `msg-code-*`, `msg-browser-*` |
| `a0-msg-info` | system notice | `msg-info-*` |
| `a0-msg-warning` / `a0-msg-error` | recoverable / fatal problem | `msg-warning-*`, `msg-error-*` |

## Anatomy
- Radius `border-radius` (18px) on three corners; the corner nearest the speaker uses `radius-tail` (5px): bottom-left for the agent, bottom-right for the user.
- Padding `0.9rem spacing-md 0.7rem`; gap between messages `spacing-sm`.
- Agent messages open with a heading line (`A0: Generating…` at 0.8rem, 70% opacity), then an optional key/value table (`.a0-kvps`, rules in `kvps-rule`), then content. Code goes in `.a0-pre` (Roboto Mono 0.75rem).
- In dark the type colours the **ground**; in light every type sits on `#f3f3f3` and the type colours the **text**. Use the token pair; never hard-code either strategy.

## Consumer provides
The type, the heading text, kvps rows and markdown body. Copy action appears on hover at 12px, 60% opacity.

## Don't
- Don't put white or `color-text` on `msg-warning-bg` in new work: the source pair is 2.5:1.
- Don't nest a Message inside a Message.
