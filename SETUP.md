# Setup Instructions - Converting to Local Python CLI

This document explains how to convert this project from Docker-based to a pure Python CLI that runs directly on your machine.

## What Changed

- ❌ Removed: `Dockerfile` - No longer needed
- ❌ Removed: `docker-compose.yml` - No longer needed
- ✅ Added: `QUICKSTART.md` - Quick setup guide
- ✅ Added: `cleanup-docker.sh/bat` - Automated cleanup scripts
- ✅ Updated: `README.md` - Local installation instructions

## Step 1: Clean Up Docker Files

### On Windows:
```cmd
cleanup-docker.bat
```

### On macOS/Linux:
```bash
chmod +x cleanup-docker.sh
./cleanup-docker.sh
```

Or manually delete:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore` (if present)

## Step 2: Install Python Requirements

You have two options:

### Option A: Using Poetry (Recommended)
```bash
pip install poetry
poetry install
```

### Option B: Using pip directly
```bash
pip install oci==2.103.0 pydantic==1.10.10
```

## Step 3: Set Up Your Oracle API Credentials

Create the `.oci` directory in your home folder with your credentials:

**Windows:**
```
%USERPROFILE%\.oci\config
%USERPROFILE%\.oci\id_rsa.pem
```

**macOS/Linux:**
```
~/.oci/config
~/.oci/id_rsa.pem
```

See the "Oracle API Key Setup" section in README.md for details.

## Step 4: Verify Installation

```bash
get_oracle_a1 --help
```

If the command is not found, try:
```bash
poetry run get_oracle_a1 --help
```

## Step 5: Get Started

Follow the instructions in `QUICKSTART.md` to create your first instance.

## Project Structure

```
get_oracle_a1/
├── README.md                 # Full documentation
├── QUICKSTART.md            # Quick setup guide
├── SETUP.md                 # This file
├── cleanup-docker.sh        # Unix cleanup script
├── cleanup-docker.bat       # Windows cleanup script
├── pyproject.toml           # Python dependencies
├── get_oracle_a1/
│   ├── __init__.py         # Main entry point
│   ├── __main__.py         # CLI module
│   ├── commands.py         # Command definitions
│   ├── config.py           # Configuration models
│   ├── helpers.py          # Helper functions
│   ├── models.py           # Data models
│   ├── usecases.py         # Business logic
│   └── py.typed            # Type hints marker
```

## Running Commands

### Method 1: Direct command (after `poetry install`)
```bash
get_oracle_a1 create --display-name my-instance --ocpu 2 --memory 12 ...
```

### Method 2: Using Poetry
```bash
poetry run get_oracle_a1 create --display-name my-instance --ocpu 2 --memory 12 ...
```

### Method 3: Using Python module
```bash
python -m get_oracle_a1 create --display-name my-instance --ocpu 2 --memory 12 ...
```

## Available Commands

- `list_availability_domain` - Show available ADs
- `list_available_subnet` - Show available subnets
- `create` - Create new A1.Flex instance
- `increase` - Upgrade instance resources

Run any command with `--help` for options:
```bash
get_oracle_a1 create --help
```

## Troubleshooting

### "Command not found"
- Make sure Poetry has the virtualenv activated
- Try `poetry run get_oracle_a1 --help`
- Or use `python -m get_oracle_a1 --help`

### "Config file not found"
- Verify `.oci/config` exists in your home directory
- Check file permissions (should be readable)
- Use `-g` flag to specify custom config path: `get_oracle_a1 create -g /path/to/config ...`

### API Authentication Errors
- Verify your Oracle credentials in `~/.oci/config`
- Ensure the key file path is correct
- Check that the private key file exists and is readable
- Verify your fingerprint matches the one in Oracle Cloud Console

## Next Steps

1. Read [QUICKSTART.md](QUICKSTART.md) for step-by-step examples
2. Check [README.md](README.md) for full command reference
3. Review the source code in `get_oracle_a1/` to understand how it works

## Support

For issues with Oracle Cloud API credentials, see:
- [Oracle API Documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm)
- [OCI Python SDK Documentation](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/)
