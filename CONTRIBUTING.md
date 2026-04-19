# Contributing to CleanSchema

Thanks for considering a contribution! This project is small on purpose — it does one job well — but there's plenty of room to make it better. Here's how.

## Quick start

```bash
git clone https://github.com/rjboogey/cleanschema
cd cleanschema
python3 -m venv .venv
source .venv/bin/activate         # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
pip install pytest                # for running tests

python -m pytest -v               # green? you're ready.
streamlit run app.py              # see your changes locally
```

## What we love PRs for

| 🟢 We say "yes please" | 🟡 We discuss first | 🔴 We say "no thanks" |
|---|---|---|
| New detector rules | UI redesigns | Adding cloud sync |
| Locale-specific synthesizers | Adding new file formats | Adding telemetry |
| Bug fixes with a regression test | New CLI subcommands | Adding "freemium" tiers |
| Doc improvements & typos | Caching layers | Adding accounts/login |

The privacy guarantees in [README.md](./README.md#privacy) are non-negotiable. PRs that break "no network, no telemetry, no account" will be declined.

## Adding a new detector

1. Open `detector.py` and add a new entry to the `CATEGORIES` list:

   ```python
   {
       "name": "CRYPTOWALLET",
       "tier": SENSITIVE,
       "hints": ("wallet", "btc_address", "eth_address"),
       "pattern": re.compile(r"^(0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$"),
   },
   ```

2. Add a generator to `synthesizer.py` if the category needs custom replacement logic. Otherwise the default `Faker.word()` is used.

3. Add a test in `tests/test_detector.py`:

   ```python
   def test_crypto_wallet_column(self):
       df = pd.DataFrame({"wallet": ["0x" + "a" * 40]})
       det = classify(df)[0]
       assert det.category == "CRYPTOWALLET"
       assert det.tier == SENSITIVE
   ```

4. Run `python -m pytest -v` — should be green.
5. Open the PR. Reference any spec or RFC if there is one.

## Style

- Format with `ruff format` (or just stay close to PEP-8). The codebase uses 100-char lines.
- Type hints are required for public functions, optional for private helpers.
- Docstrings should explain *why*, not *what*.
- Tests live in `tests/`, mirror the module structure, use `pytest` not `unittest`.

## Code of Conduct

Be kind. Disagree freely on technical merits, never on people. The maintainers reserve the right to remove anything that isn't.

## Questions?

Open an issue or ping [@therealdrjonesy](https://twitter.com/therealdrjonesy).
