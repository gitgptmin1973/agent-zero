# ConfigButton

The two-up grid of quiet buttons in the sidebar: New Chat, Reset, Load, Save, Restart, Settings.

Static rendition, hand-written from `webui/index.css .config-button (974–1000, light 2013–2024)`.

## When to use
Sidebar actions only, laid out two per row at `calc(50% - spacing-xs)`.

## Spec
`color-background` fill, `.1rem` `color-border` border, `radius-tail`, Rubik 0.8rem, 80% opacity at rest. Hover: `config-hover` at full opacity. Pressed: 50% opacity (dark) / `config-active` (light). Max height 2.3rem.
