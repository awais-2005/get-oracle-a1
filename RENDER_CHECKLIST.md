# Render Deployment Checklist

Follow this checklist to deploy your Oracle A1.Flex automation dashboard to Render.

## Pre-Deployment (Local Setup)

- [ ] Have your Oracle Cloud credentials ready
  - [ ] User OCID (ocid1.user.oc1....)
  - [ ] API Fingerprint (aa:bb:cc:dd:...)
  - [ ] Tenancy OCID (ocid1.tenancy.oc1....)
  - [ ] Private Key file (id_rsa.pem)
  - [ ] Region (e.g., ap-hyderabad-1)

- [ ] Get your Oracle IDs locally:
  ```bash
  poetry run get_oracle_a1 list_availability_domain
  poetry run get_oracle_a1 list_available_subnet
  ```
  - [ ] Copy Availability Domain name (e.g., vMqB:AP-HYDERABAD-1-AD-1)
  - [ ] Copy Subnet OCID (ocid1.subnet.oc1.ap-hyderabad-1....)

- [ ] Generate SSH keys (if not already done):
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
  ```
  - [ ] `~/.ssh/id_rsa` (private key)
  - [ ] `~/.ssh/id_rsa.pub` (public key)

- [ ] Test locally that everything works:
  ```bash
  poetry install
  poetry run get_oracle_a1 create \
    --display-name test-instance \
    --availability-domain "YOUR_AD" \
    --subnet-id "YOUR_SUBNET_ID" \
    --ocpu 2 --memory 12 \
    --os-name "Canonical Ubuntu" \
    --os-version "22.04" \
    --boot-volume-size 100 \
    --ssh-authorized-keys ~/.ssh/id_rsa.pub
  ```

## GitHub Setup

- [ ] Create GitHub repository (https://github.com/new)
  - [ ] Repository name: `get_oracle_a1`
  - [ ] Make it **Private** (for security with credentials)
  - [ ] Create repository

- [ ] Push code to GitHub:
  ```bash
  git init
  git add .
  git commit -m "Add web dashboard for Oracle automation"
  git remote add origin https://github.com/YOUR_USERNAME/get_oracle_a1.git
  git branch -M main
  git push -u origin main
  ```
  - [ ] Verify code is on GitHub

- [ ] Create `.gitignore` to exclude sensitive files:
  ```
  .venv/
  __pycache__/
  .oci/
  *.pyc
  .DS_Store
  .env
  ```
  - [ ] Commit and push `.gitignore`

## Render Dashboard Setup

### 1. Create Web Service

- [ ] Go to https://dashboard.render.com
- [ ] Sign up or log in
- [ ] Click **New +** → **Web Service**
- [ ] Connect GitHub account and select your repository
- [ ] Configure service:
  - [ ] **Name**: `oracle-a1-dashboard`
  - [ ] **Runtime**: `Python 3`
  - [ ] **Root Directory**: (leave blank)
  - [ ] **Build Command**: `pip install poetry && poetry install`
  - [ ] **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
  - [ ] **Instance Type**: Free (or paid if preferred)
  - [ ] Click **Create Web Service**

### 2. Add Environment Variables

Wait for the first deployment to complete (it may fail due to missing secrets, that's OK).

- [ ] Go to your service → **Environment**
- [ ] Add these as regular environment variables:
  - [ ] `FLASK_ENV` = `production`
  - [ ] `OCI_CONFIG_FILE` = `~/.oci/config`
  - [ ] `PYTHONUNBUFFERED` = `true`

### 3. Add OCI Secrets (CRITICAL!)

These must be added as **Secrets** (click lock icon):

- [ ] `OCI_USER` = (your user OCID, e.g., `ocid1.user.oc1...`)
- [ ] `OCI_FINGERPRINT` = (your fingerprint, e.g., `aa:bb:cc:dd...`)
- [ ] `OCI_TENANCY` = (your tenancy OCID, e.g., `ocid1.tenancy.oc1...`)
- [ ] `OCI_REGION` = (your region, e.g., `ap-hyderabad-1`)
- [ ] `OCI_PRIVATE_KEY` = (full content of your private key, including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)

### 4. Add Email Secrets (Optional)

For email notifications:

- [ ] `SMTP_USER` = (your Gmail, e.g., `your-email@gmail.com`)
- [ ] `SMTP_PASSWORD` = (Gmail App Password - NOT your regular password!)
  - [ ] Get from: https://support.google.com/accounts/answer/185833
  - [ ] Generate a 16-character app password
  - [ ] Use that instead of your Gmail password

## Deploy & Verify

- [ ] Click **Deploy** in Render dashboard
- [ ] Watch the build process in the **Logs** tab
- [ ] Wait for "Deploy successful" message
- [ ] Note the URL: `https://oracle-a1-dashboard.onrender.com`

### Test the Dashboard

- [ ] Open your dashboard URL in browser
- [ ] Fill in the form:
  - [ ] **Instance Name**: `test-render`
  - [ ] **OCPUs**: `2`
  - [ ] **Memory**: `12`
  - [ ] **Availability Domain**: (paste from your list)
  - [ ] **Subnet ID**: (paste from your list)
  - [ ] **OS**: `Canonical Ubuntu`
  - [ ] **OS Version**: `22.04`
  - [ ] **Boot Volume Size**: `100`
  - [ ] **SSH Public Key**: `/root/.ssh/id_rsa.pub`
  - [ ] (Optional) Check email notification and enter your email

- [ ] Click **Create Instance**
- [ ] Check **Recent Executions** section
- [ ] Verify logs show successful creation
- [ ] If email enabled, check for notification email

## Post-Deployment

- [ ] Monitor in Render dashboard → **Logs** for any errors
- [ ] Test instance upgrade functionality:
  - [ ] Go to **Increase Resources** tab
  - [ ] Enter your instance name
  - [ ] Set new OCPU and Memory values
  - [ ] Click **Increase Resources**

- [ ] Set up monitoring:
  - [ ] Enable Render email alerts (optional)
  - [ ] Save your dashboard URL

- [ ] Security review:
  - [ ] Verify GitHub repo is Private
  - [ ] Check that secrets are using lock icon in Render
  - [ ] Never commit credentials to GitHub

## Troubleshooting

If deployment fails:

1. **Build error**: Check logs in Render dashboard
   - [ ] Verify Python version is 3.11+
   - [ ] Check Poetry lock file is up to date

2. **Runtime error**: Check Environment secrets
   - [ ] Verify all OCI secrets are set
   - [ ] Check private key has proper formatting
   - [ ] Ensure no extra spaces or newlines in secrets

3. **API error when creating instance**:
   - [ ] Verify Availability Domain and Subnet ID are correct
   - [ ] Check SSH key path is absolute (e.g., `/root/.ssh/id_rsa.pub`)
   - [ ] Ensure OCI credentials are valid

4. **Email not sending**:
   - [ ] Verify Gmail app password was generated correctly
   - [ ] Check SMTP settings match Gmail's requirements
   - [ ] Verify recipient email in form is correct

## Performance Notes

- Free tier instances on Render sleep after 15 minutes of inactivity
- Creates may take 5-15 minutes depending on Oracle's availability
- Check **Recent Executions** for real-time status

## Next Steps

- [ ] Bookmark your dashboard URL
- [ ] Share access with team members
- [ ] Monitor first few instance creations
- [ ] Upgrade to paid Render plan if continuous uptime needed

---

**Deployment Status**: [ ] Complete ✓

**Dashboard URL**: https://oracle-a1-dashboard.onrender.com
