# Oracle Cloud Instance Automation — Versatile Edition

Create and manage Oracle Cloud instances without fighting Oracle's "Out of host
capacity" errors by hand. The tool keeps retrying in the background until Oracle has
room, then creates the instance for real through the official `oci` Python SDK.

This started as an `A1.Flex`-only tool. It isn't anymore: the dashboard now works with
**any VM shape and any image** in your tenancy — Ampere A1, AMD E-series, Intel Standard,
DenseIO, whatever your account has access to — picked dynamically from your real Oracle
account, not hardcoded.

There are two ways to use it:

- **Web Dashboard** (`app.py`) — a Flask app with upload-first credentials and fully
  dynamic, cascading dropdowns for availability domain, shape series, shape, image,
  image version, and image build. This is the actively developed, versatile interface
  and the one meant for day-to-day use.
- **CLI** (`get_oracle_a1` command) — the original command-line tool, predating the
  versatile rework. It's still hardcoded to `VM.Standard.A1.Flex` under the hood and has
  no shape/image selection of its own. Still useful for `list_availability_domain` /
  `list_available_subnet` / `increase`. **`create` is currently broken on the CLI** —
  see [Known Issues](#known-issues).

## Prerequisites

- Python 3.11 (pinned via `.python-version` / `poetry.toml`)
- [Poetry](https://python-poetry.org/) for dependency management
- An Oracle Cloud account with an API signing key. Follow Oracle's
  [official instructions](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm#Required_Keys_and_OCIDs)
  to generate one if you don't have one yet.

## Installation

```bash
git clone https://github.com/awais-2005/get-oracle-a1.git
cd get-oracle-a1
pip install poetry
poetry install
```

`poetry.toml` in this repo sets `virtualenvs.create = false`, so `poetry install` installs
straight into whatever Python environment is active — no separate venv to remember to
activate before running `gunicorn` or `get_oracle_a1`.

---

## Web Dashboard

### Run it locally

```bash
poetry run gunicorn --bind 0.0.0.0:5000 app:app
# or, for auto-reload during development:
FLASK_ENV=development poetry run python app.py
```

Open `http://localhost:5000`.

### Deploying to Render

1. Create a new **Web Service** from this repo (leave Root Directory blank).
2. **Build Command:**
   ```
   pip install poetry && poetry lock && poetry install --only main --no-interaction --no-ansi
   ```
3. **Start Command:**
   ```
   gunicorn --bind 0.0.0.0:$PORT app:app
   ```
4. No `OCI_*` environment variables are needed — the dashboard takes credentials as file
   uploads per request (see below), not server-side config. Optionally set:
   - `FLASK_SECRET_KEY` — set this in production; the app falls back to an insecure
     default otherwise.
   - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` — only needed if you want
     the "send email when complete" option to actually send mail.

**Free-tier caveat:** Render's free web services spin down after ~15 minutes of no
inbound HTTP traffic. This kills any in-progress retry loop and its logs (both live only
in memory), regardless of whether Oracle still hasn't found capacity. A paid plan avoids
this; on the free tier, treat a spin-down as "creation didn't finish" and start again.

### Using the dashboard

**1. Upload credentials.** Three files, all required:

- **OCI Config File** — your `~/.oci/config`, in standard ini format, *plus* one extra
  line: `subnetId`. The dashboard has no separate subnet field — it reads the subnet to
  use directly out of this file. Example:

  ```ini
  [DEFAULT]
  user=ocid1.user.oc1..aaaaaaaa...
  fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
  tenancy=ocid1.tenancy.oc1..aaaaaaaa...
  region=ap-hyderabad-1
  subnetId=ocid1.subnet.oc1.ap-hyderabad-1.aaaaaaaa...
  ```

  Do **not** include `key_file=` — the private key is uploaded separately below.

- **OCI Private Key File** — your `id_rsa.pem`, matching the config above.
- **SSH Public Key File** — your `id_rsa.pub`, installed onto the new instance.

None of these are stored server-side between requests — they're read into memory,
used for that request, and the SSH key's temp file on disk is deleted immediately after.

**2. The form builds itself from your real Oracle account.** Once credentials are
accepted, the rest of the form renders and cascades automatically, top choice
pre-selected at each step:

`Availability Domain` → `Shape Series` → `Shape` → `Image` → `Image Version` →
`Image Build`

Changing a selection re-fetches and re-populates everything below it — e.g. picking a
different Availability Domain refetches the shapes actually available there; picking a
different Shape refetches the images actually compatible with it. Instance type is fixed
to VM (bare-metal shapes are excluded).

**3. Fill in the rest:** Instance Name, OCPUs, Memory (GB), Boot Volume Size (GB), and
optionally an email address to notify on completion.

**4. Submit, then watch it live.** The Recent Executions panel at the bottom polls every
2 seconds and shows every attempt as it happens — including each `Out of host capacity`
retry, rate-limit hits, and the eventual success or hard failure. A **Terminate** button
lets you stop an in-progress retry loop without waiting for it to eventually succeed.

**5. Increase Resources** — the form exists but the backend for it is still a stub
("coming soon"); submitting it won't actually change anything yet.

---

## CLI

The CLI reads credentials from a real OCI config file (standard format, no `subnetId`
hack needed — subnet is a normal flag) via Oracle's own config loader.

```bash
get_oracle_a1 --help
```

```bash
get_oracle_a1 list_availability_domain -p DEFAULT
get_oracle_a1 list_available_subnet -p DEFAULT
```

```bash
get_oracle_a1 increase \
  -p DEFAULT \
  -n my-oracle-instance \
  -c 4 \
  -m 24 \
  --incremental
```

Common flags (`-p/--profile`, `-g/--api-config-file`, `--verbose`) work on every
subcommand; run `get_oracle_a1 <subcommand> --help` for the full flag list.

---

## Known Issues

- **`get_oracle_a1 create` currently crashes.** `usecases.create()` now requires a
  `stop_event` argument (added for the dashboard's Terminate button), but the CLI's
  `main()` still calls it with the old two-argument form. Running `get_oracle_a1 create
  ...` will raise `TypeError: create() missing 1 required positional argument:
  'stop_event'` immediately. Use the dashboard for creating instances until this is
  fixed; `list_availability_domain`, `list_available_subnet`, and `increase` are
  unaffected.
- **No authentication on the dashboard.** Anyone with the deployed URL can create
  instances or upload credentials through it. Don't deploy it somewhere publicly
  reachable without adding your own access control in front of it (e.g. a reverse proxy
  with basic auth).
- **Execution logs and retry state are in-memory only.** A restart, redeploy, or
  Render free-tier spin-down loses all history and kills any in-progress retry loop.
- **Increase Resources (dashboard)** is UI-only right now; the backend logs "coming
  soon" and does nothing else.

## Security Notes

- Treat your OCI config, private key, and any `subnetId`/OCID values as sensitive.
  Don't commit real credentials to this repo, even in example/scratch files.
- If a private key is ever pasted somewhere it shouldn't be (a chat log, a public issue,
  a committed file), rotate it in the Oracle Console (Profile → User Settings → API
  Keys) rather than continuing to use it.

## License

MIT
