# Practice from your phone (GitHub Codespaces)

1. Open github.com in your phone browser (request desktop site) or use the GitHub app.
2. Open this repo → **Code** → **Codespaces** → **Create codespace on main**. Pick the 4-core / 16 GB machine.
3. The Codespace is VS Code in the browser with a terminal. Landscape mode and a Bluetooth keyboard help a lot.
4. In the terminal: `make verify-00`, `ollama serve &`, `ollama pull llama3.2:1b`, then follow the next module.
5. **Stop the Codespace when done** (Codespaces menu → Stop). Free personal accounts get a monthly allowance of core-hours, and a 4-core machine uses them fast.

## Daily 30-minute routine
- 5 min: `python -m tutor quiz NN` on yesterday's module
- 20 min: next lab step
- 5 min: `make verify-NN`, `python -m tutor done NN`, commit and push your notes

If kind is too heavy on your plan, do modules 00–03, 05 (plan only), 06–08 on any size and run 04 on a desktop.

## Daily lab (from a blank file)
`labs/README.md` has a 10-week path. Each day: read one lab README, write your files in `labs/NN-*/work/`, run `make lab-check LAB=NN`, then compare with `solution/` and commit.
