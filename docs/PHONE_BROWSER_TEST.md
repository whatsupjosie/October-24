# Phone browser test instance

This branch adds a Codespaces configuration for the full PubCast app. It does
not change the production camera or Control Room implementation.

1. While signed in to GitHub, create a Codespace from this branch.
2. Wait for the Python runtime dependencies to install and PubCast to start.
3. Open the **Ports** panel and open port **8000**, labeled **PubCast test app**.
4. Keep port visibility **Private**. Open its generated HTTPS link on the phone,
   signed in to the same GitHub account. This private GitHub gate is separate
   from PubCast's own login.
5. Open `/login` and create a test owner on first use. Do not reuse a password.
6. Open `/control` for the operator station or `/walk` for the walkable studio.
7. Stop the Codespace when finished. Account quotas and billing apply according
   to your GitHub account; no paid plan is selected by these files.

The startup helper uses `run_reach.py` with authentication enabled, a separate
test data folder outside the repository, and the optional Node sidecar disabled.
Its log is `~/.local/share/pubcast-phone-test/server.log`.

Private forwarding is intended for the owner phone test. It does not grant
another browser or an assistant GitHub authentication. Sharing access requires
a separate deliberate choice. Never make an uninitialized test host public.

Verified locally: dependency installation, launcher health and auth checks on
the same pinned source; Python syntax and configuration checks. The hosted
Codespaces provisioning and phone access must be verified after account sign-in.
Camera browser regression results are documented separately and do not imply
physical-camera, Android, or rendered-stage integration readiness.
