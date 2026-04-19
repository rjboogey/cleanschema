# Security Policy

CleanSchema's whole reason to exist is data safety. We take this seriously.

## Reporting a vulnerability

If you find a security issue — a way data leaves the machine unintentionally, a way the synthesizer leaks information from the original, anything else — please do **not** open a public GitHub issue.

Email **security@drjonesy.com** with:
- A description of the issue
- Steps to reproduce
- The version of CleanSchema affected (`git log -1 --format=%H` works)
- Any suggested mitigation

You should hear back within 72 hours. Confirmed issues will be patched and disclosed coordinately. Reporters get credit in `CHANGELOG.md` if they want it.

## Out of scope

- "Streamlit binds to localhost on port 8501" — yes, by design. CleanSchema doesn't accept inbound connections from the network. If you've put a reverse proxy in front of it, that's your responsibility.
- "Faker isn't cryptographically random" — correct. The replacement values are realistic, not unguessable. Don't use CleanSchema as a key derivation function.
- "Detection misses my custom column type" — that's a feature request, not a security issue. Open a normal PR.

## Supply chain

CleanSchema's dependencies are pinned in [`requirements.txt`](./requirements.txt). We try to minimize the surface area: pandas, openpyxl, Streamlit, Faker. No analytics SDKs, no error reporting, no auto-updaters.
