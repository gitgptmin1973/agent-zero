# Toast

A full-width bar that slides up from under the composer to confirm or report an action.

Static rendition, hand-written from `webui/css/toast.css (1–100)`.

## Spec
Padding .6rem .9rem, `shadow-toast`, Rubik. Title 0.6rem at 70%, a 1px 15%-white separator, then the message. Grounds: `toast-bg` (neutral), `toast-success`, `toast-error`, `toast-info`; text `on-fill`. Slide in with `transform` 0.4s cubic-bezier(0.19, 0.86, 0.47, 1).

## Don't
White on `toast-success` is 2.8:1 in the source; prefer the neutral toast with a "Saved" message for new success states.
