# Button

Form and modal buttons: btn-ok confirms, btn-cancel backs out, primary and danger cover the rest.

Static rendition, hand-written from `webui/css/modals.css .btn, .btn-ok, .btn-cancel, .btn.primary (258–340); tunnel.css .btn-danger`.

## Variants
- `a0-btn-ok`: the confirming action of a modal or form. `send` fill, white text, hover `send-hover`, pressed `send-active`. One per footer.
- `a0-btn-cancel`: outline in `color-accent` (0.15rem), fills with the accent on hover. Use for Cancel and Close.
- `a0-btn-primary`: `info-blue` fill. Inline field actions (Browse, Test).
- `a0-btn-danger`: `danger` fill. Destructive, irreversible actions (Stop tunnel, Delete).
- Disabled: `disabled` fill; or `.btn-disabled` = 50% opacity.
- `slim`: 0.2em 0.4em padding for in-table actions.

## Spec
Rubik 500 0.875rem, padding 0.5rem 1.5rem, radius `radius-btn`, no border except cancel.

## Don't
White on `info-blue` is 3.1:1: keep primary labels short and 500 weight or heavier.
