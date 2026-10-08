# ChatInput

The composer: a mono textarea with a round blue send button and a secondary mic button.

Static rendition, hand-written from `webui/index.css #chat-input, .chat-button, #send-button (852–945, 1290–1340)`.

## When to use
Once per chat, pinned in the input section on `color-panel`.

## Anatomy
- Textarea: `color-input` fill, 6px transparent border plus a 1px `color-border` outline, `radius-input` (8px), Roboto Mono 0.9rem, 3.05rem min and 7rem max height. On focus the fill moves to `color-input-focus` and text grows to 0.955rem.
- Send: 2.525rem circle in `send`, hover `send-hover` + scale(1.05), pressed `send-active`. The glyph is `on-fill`.
- Mic: same circle on `color-secondary`.

## Consumer provides
Placeholder text, value, send and mic handlers, attachments row above.
