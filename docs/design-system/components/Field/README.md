# Field

A settings row: bold title and description on the left 60%, the control on the right, grouped in a bordered Section.

Static rendition, hand-written from `webui/css/settings.css .field, .field-label, inputs (1–76); modals.css .section (237–256)`.

## Spec
- Section: 1px `color-border`, `radius-section`, padding 1rem; title 1.25rem bold `color-primary`.
- Field: grid `60% 1fr`, margin-block 1rem. Title bold `color-primary`; description 0.875rem at 80%.
- Text inputs: `color-background` fill, 1px `color-secondary` border, `radius-btn`, padding 0.5rem, Rubik.

## Consumer provides
Title, description, control (input, select, Toggle, range).
