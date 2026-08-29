# Macro to get Oracle Cloud A1.Flex instance

![PyPI](https://img.shields.io/pypi/v/oci?label=oci&logo=python&style=flat-square)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/isac322/get_oracle_a1/master?logo=github&style=flat-square)
![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/isac322/get_oracle_a1/ci.yaml?branch=master&logo=github&style=flat-square)
![Dependabpt Status](https://flat.badgen.net/github/dependabot/isac322/get_oracle_a1?icon=github)

## Overview

Automatically create or upgrade A1.Flex instances on Oracle Cloud. This is a pure Python CLI tool that runs directly on your machine.

## Prerequisites

- Python 3.11 or higher
- Oracle Cloud account with API credentials
- Poetry (for dependency management)

### Oracle API Key Setup

You must generate and configure an Oracle API Key. Follow the [Official Instruction](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm#Required_Keys_and_OCIDs).

After generating your key:
1. Place the private key file at `~/.oci/id_rsa.pem`
2. Create `~/.oci/config` with your OCI API credentials
3. Make sure the config file has proper permissions: `chmod 600 ~/.oci/config`

Example `~/.oci/config`:
```
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaa...
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
key_file=~/.oci/id_rsa.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaa...
region=us-phoenix-1
```


## Installation

### 1. Clone or download this repository
```bash
cd get_oracle_a1
```

### 2. Install dependencies using Poetry
```bash
pip install poetry
poetry install
```

Or install directly with pip:
```bash
pip install -r requirements.txt  # if requirements.txt is available
# OR
poetry export --without-hashes -f requirements.txt | pip install -r /dev/stdin
```

### 3. Verify Installation
```bash
get_oracle_a1 --help
```

## Usage

### Command Reference

#### List Availability Domains
```bash
get_oracle_a1 list_availability_domain --help
```

#### List Available Subnets
```bash
get_oracle_a1 list_available_subnet --help
```

#### Create A1.Flex Instance

```bash
get_oracle_a1 create \
  --display-name my-instance \
  --ocpu 4 \
  --memory 24 \
  --availability-domain <AD_NAME> \
  --subnet-id <SUBNET_OCID> \
  --os-name "Canonical Ubuntu" \
  --os-version 22.04 \
  --boot-volume-size 200 \
  --ssh-authorized-keys /path/to/your/ssh/key.pub
```

#### Increase Instance Resources

```bash
get_oracle_a1 increase \
  --display-name my-instance \
  --ocpu 8 \
  --memory 32
```

Use `--incremental` flag to acquire resources gradually:
```bash
get_oracle_a1 increase \
  --display-name my-instance \
  --ocpu 8 \
  --memory 32 \
  --incremental
```

## Examples

### Step 1: Get Your IDs
```bash
# List availability domains
get_oracle_a1 list_availability_domain -p DEFAULT

# List available subnets
get_oracle_a1 list_available_subnet -p DEFAULT
```

### Step 2: Create Instance
```bash
get_oracle_a1 create \
  -p DEFAULT \
  -n my-oracle-instance \
  -a us-phoenix-1-ad-1 \
  -s ocid1.subnet.oc1.phx.xxxxx \
  -c 2 \
  -m 12 \
  --os-name "Canonical Ubuntu" \
  --os-version 22.04 \
  -b 100 \
  --ssh-authorized-keys ~/.ssh/id_rsa.pub
```

### Step 3: Upgrade Resources
```bash
get_oracle_a1 increase \
  -p DEFAULT \
  -n my-oracle-instance \
  -c 4 \
  -m 24
```

## Options

- `-p, --profile`: OCI API profile name (default: DEFAULT)
- `-g, --api-config-file`: Path to OCI config file (default: ~/.oci/config)
- `--verbose`: Enable verbose output for debugging

## Troubleshooting

### "API config file not found"
Make sure your OCI config file is at `~/.oci/config` with proper format and permissions.

### "Unable to access SSH key"
Ensure the SSH key file path is correct and readable by your user.

### Permission denied errors
Run `chmod 600 ~/.oci/config` to set proper file permissions.

## License

MIT
