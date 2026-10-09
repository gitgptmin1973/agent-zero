# Switch

The small sidebar switch that toggles a display preference such as Autoscroll or Show thoughts.

Static rendition, hand-written from `webui/index.css .switch, .slider (1408–1456, light 2045–2056)`.

## Spec
2.2rem × 1.15rem track in `switch-track` with a 1px `switch-border`; 0.8rem knob in `switch-knob`. On: knob slides 1rem, track `switch-track-on`. 0.4s ease-in-out.

The on and off tracks differ only slightly: the knob position carries the state. Pair every switch with its label in a `config-list` row.
