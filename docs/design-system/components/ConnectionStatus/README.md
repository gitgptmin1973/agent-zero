# ConnectionStatus

An 18px dot in the header that beats while the backend is reachable and turns red when it is not.

Static rendition, hand-written from `webui/index.css .status-icon, .connected, .disconnected, @keyframes heartbeat`.

## Spec
`connected` dot with the heartbeat keyframes (1.5s); `disconnected` dot, static. Pair it with a text label or tooltip: colour alone is not enough.
