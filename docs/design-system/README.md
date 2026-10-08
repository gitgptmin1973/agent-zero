Agent Zero's web UI is a dark-first, two-panel chat console: a 250px sidebar on `color-panel`, a chat history of rounded message bubbles, and a mono composer pinned to the bottom. The interface stays grey and quiet so that **message colour carries meaning**: every bubble's hue says who or what produced it.

## Content fundamentals

- **Plain, technical, short.** Labels are verbs or nouns in Title Case on buttons ("New Chat", "Reset Chat", "Save Chat", "Restart") and sentence case everywhere else ("Type your message here...").
- **The agent speaks in its own name.** Message headings are prefixed with the agent id: `A0: Generating…`, `A0: Using tool 'code_execution_tool'`, `A0: Responding`. Subordinates are `A1`, `A2`…
- **Machine values stay machine-shaped.** Tool names, paths and code appear verbatim in Roboto Mono (`pre`, `user-meta`), never paraphrased.
- **Status is one word.** Scheduler states are lowercase single words (`idle`, `running`, `disabled`, `error`); toasts give a short title and one sentence.
- No emoji in UI chrome.

## Colour

- Dark is the default theme; light is an alternative. Build for dark first and check light.
- Neutrals: `color-background` behind everything, `color-panel` for the sidebar, input section and modals, `color-message-bg` for neutral bubbles. Text is `color-text`; secondary labels use `color-primary` (bold or 1rem+ only in dark: 4.1:1).
- `color-secondary` is a hover fill, not a text colour in dark.
- `color-accent` means "back out or destroy": btn-cancel only.
- Actions: `send` (and its `send-hover`, `send-active`) is the one saturated action colour. `info-blue` is for secondary filled buttons and the settings Toggle; `danger` for irreversible actions.
- **Message palette.** Use the pair `msg-<type>-bg` + `msg-<type>-fg`. In dark the type colours the ground and the text is `#e0e0e0`; in light every type sits on `#f3f3f3` and the type colours the text. Types: default, agent, response, delegation, tool, code, browser, info, util, warning, error, user.
- Status: `connected` / `disconnected` for the heartbeat dot; `status-*` with `status-*-bg` for scheduler badges.
- Hairlines (`color-border`, `kvps-rule`, `table-stripe`) are decorative and below 3:1: never use them as the only boundary of an input you can type in.

Contrast pairs that miss 4.5:1 in the source are kept exact and flagged in their token notes: `msg-warning` in dark (2.5:1), `msg-response` in light (4.46:1), white on `info-blue` (3.1:1) and on `toast-success` (2.8:1). Don't add new text on those pairs.

## Type

- Rubik (`sans`) for all UI; Roboto Mono (`mono`) for the composer, the user's own message line, code and tool output. Both load from Google Fonts with the weight ranges Rubik 300–900 and Roboto Mono 100–700.
- The UI is small: base text `font-size-small` (0.8rem) in the sidebar and messages, `font-size-smaller` (0.9rem) for final responses, `btn` (0.875rem 500) for buttons, `micro` (0.6rem) for the text-button row.
- Titles inside settings are `section-title` (1.25rem bold) and `field-title` (1rem bold), both in `color-primary`.
- Markdown headings inside messages scale from the message size: h1 1.25em/800, h2 1.2em/700, h3 1.15em/600, h4–h6 1.1–1em/500.

## Space, shape, depth

- Spacing has four steps: `spacing-xs` 5px, `spacing-sm` 10px, `spacing-md` 20px, `spacing-lg` 32px. Panel gutters and bubble side padding are `spacing-md`; the gap between bubbles is `spacing-sm`.
- Bubbles use `border-radius` (18px) with one `radius-tail` (5px) corner pointing at the speaker. Inputs and tabs use `radius-input` (8px), modals `radius-modal` (12px), form buttons and badges `radius-btn` (4px), the send and mic buttons `radius-round`.
- Depth is minimal: `shadow-sidebar` on the panel edge, `shadow-modal`, `shadow-toast`. Everything else is flat.
- Layering follows the zIndex tokens: header 1004, tooltip 1002, modal 2001, drag-and-drop 9999.

## Motion

- Colour, border and background changes ease over 0.3s; switches over 0.4s ease-in-out.
- New messages fade in over 0.5s. The send button scales to 1.05 on hover.
- The connection dot beats (1.5s heartbeat); the progress line uses a 1s shine sweep. Respect `prefers-reduced-motion` in new work.

## Iconography

- Settings and file icons are single-file SVGs in `assets/Icons`, drawn in black (`#000`) line or fill. The UI recolours them with a CSS filter (`--svg-filter`: brightness(0) plus an invert/sepia chain that lands near `color-primary`), so ship new icons black on transparent and let the filter tint them.
- A few file-type icons carry their own fill (`code` amber `#f2b700`, `image` green `#00dd7f`, `archive` and `backup_restore` `#6495ed`, `document`, `file`, `folder` `#a0a0a0`); keep those as is.
- Inline UI glyphs (send, mic, hamburger, arrows) are inline SVGs drawn with `currentColor`.

## Logo

- `favicon.svg` is the mark: a white "A" with a crossbar block on a navy rounded square (`rgb(1,4,26)`). `favicon_round.svg` is the circular cut.
- `darkSymbol.svg` is the bare "A" in `currentColor`; as an `<img>` it renders black, so inline it to tint.
- `splash.jpg` is the header logo (shown at 2.6rem high, `radius-tail` corners); light mode inverts and greys it with a filter.

## Components

Previews here are static renditions of the source CSS (`components/bundle.css`, classes prefixed `a0-`); the app itself is Alpine.js with global stylesheets, not a component library.
