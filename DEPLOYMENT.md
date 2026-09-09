# Semiconductor Fab Operations deployment

The API runs on Render and the command-center frontend runs on Vercel. The copilot has a deterministic fallback, so deployment does not depend on a secret.

1. Create a Render Blueprint from this repository. Keep the service name `semiconductor-fab-operations-api`; `render.yaml` installs the package, starts Uvicorn, and checks `/health`.
2. Confirm `https://semiconductor-fab-operations-api.onrender.com/health` is healthy.
3. Import the repository in Vercel and set Root Directory to `frontend`. Do not add a build command or output-directory override.
4. Open the Vercel URL, verify Mission Control loads, then ask FabOps Copilot about a lot, queue, or tool.
5. Optional: add `GEMINI_API_KEY` only as a Render secret.

The frontend's API URL is declared in `frontend/index.html`; update it if the Render service is renamed.
