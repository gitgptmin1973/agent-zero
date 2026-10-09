# StatusBadge

A small capitalised pill showing a scheduled task's state: idle, running, disabled or error.

Static rendition, hand-written from `webui/index.css .scheduler-status-badge (2682–2735)`.

## Spec
12px Rubik 500, padding 4px 8px, `radius-btn`, a 1px border in the state colour at 30%, a tinted ground (`status-*-bg`) and text in `status-*`. The word always carries the state, so the badge is safe for colour-blind readers.
