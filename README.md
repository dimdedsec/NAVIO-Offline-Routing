# NAVIO GitHub Offline Routing Publisher (FIX4)

1. Create **public** GitHub repository `NAVIO-Offline-Routing` with README and default branch `main`.
2. Upload *the contents of this extracted folder* keeping `.github/workflows/` and `tools/` paths. Use GitHub Desktop if easiest. Commit and push to main.
3. Repository Settings > Actions > General > Workflow permissions: choose Read and write, then Save (if allowed).
4. Actions > NAVIO | Build dan Publikasikan Offline Routing Jambi > Run workflow.
5. A successful run publishes a `jambi-tiles.tar` in Releases and commits `navio-routing-catalog.json`.
6. NAVIO FIX4 Android > Settings > Offline Data > Hubungkan katalog GitHub (sekali): enter `USERNAME/NAVIO-Offline-Routing`. Then Download peta + routing > Jambi.

**WARNING:** This is a workflow/publisher, not a prebuilt Jambi routing graph. It is untested on a live GitHub runner; first successful workflow and Android offline road tests are still required. Pilot coverage only: bbox 100.6,-3.3,105.2,-0.1. See complete ZIP for full Indonesian guide.
