# ClawTasker Control UI

This frontend is organized to mirror the official OpenClaw Control UI shape:
- `ui/package.json` uses the same core toolchain family (`lit`, `vite`, `vitest`)
- `ui/src/main.js` and `ui/src/ui/app-shell.js` provide the app entrypoint and root custom element
- `ui/src/styles.css` splits base, layout, and component styles similarly to OpenClaw

For offline reliability, this repository also ships a prebuilt static bundle in `ui/dist/` that the Python server serves directly.
