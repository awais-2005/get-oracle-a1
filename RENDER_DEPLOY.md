# Deploy to Render - Step by Step Guide

This guide will help you deploy the Oracle A1.Flex automation dashboard to Render.

## Prerequisites

1. A Render account (https://render.com) - **Free tier is sufficient!**
2. Your Oracle Cloud credentials ready
3. A GitHub repository (Render deploys from GitHub)
4. (Optional) Gmail account for email notifications

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Oracle A1.Flex dashboard"
git remote add origin https://github.com/YOUR_USERNAME/get_oracle_a1.git
git branch -M main
git push -u origin main
```

## Step 2: Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Fill in the service details:
   - **Name**: `oracle-a1-dashboard`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install poetry && poetry install`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan**: Free (or paid if you want uptime guarantee)

## Step 3: Configure Environment Variables

In Render dashboard, go to **Environment** and add these variables:

### Required Configuration

```
FLASK_ENV=production
FLASK_SECRET_KEY=[auto-generate by leaving blank]
OCI_CONFIG_FILE=~/.oci/config
PYTHONUNBUFFERED=true
```

### OCI Credentials (Required)

These must be set as **Secrets** (not regular env vars) for security:

1. **OCI_USER** - Your Oracle user OCID
   - Find at: Oracle Console → Profile → User settings
   - Format: `ocid1.user.oc1..xxxxx`

2. **OCI_FINGERPRINT** - Your API key fingerprint
   - Find at: Oracle Console → Profile → API Keys
   - Format: `aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99`

3. **OCI_TENANCY** - Your tenancy OCID
   - Find at: Oracle Console → Tenancy Details
   - Format: `ocid1.tenancy.oc1..xxxxx`

4. **OCI_REGION** - Your default region
   - Example: `ap-hyderabad-1`

5. **OCI_PRIVATE_KEY** - Your private key content (full PEM text)
   - Get from: The private key file you downloaded from Oracle
   - Copy the entire content including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`

### Email Configuration (Optional)

For email notifications on successful instance creation:

1. **SMTP_USER** - Your Gmail address
   - Example: `your-email@gmail.com`

2. **SMTP_PASSWORD** - Gmail App Password (NOT your regular password!)
   - Follow: https://support.google.com/accounts/answer/185833
   - Generate a 16-character app password
   - Use this instead of your Gmail password

3. **SMTP_SERVER** - (optional, default is `smtp.gmail.com`)

4. **SMTP_PORT** - (optional, default is `587`)

## Step 4: Add OCI Credentials to Render

### Simple Method (Copy-Paste):

1. Go to Render Dashboard → Your Service → Environment
2. Click **Add Environment Variable**
3. For each credential above, add them as **Secret** (use lock icon)

### Example adding OCI_PRIVATE_KEY:

```
Key: OCI_PRIVATE_KEY
Value: [Paste full content of id_rsa.pem, including BEGIN and END lines]
Secret: Yes ✓
```

## Step 5: Deploy

1. Click **Deploy** button in Render dashboard
2. Watch the build logs
3. Once deployed, you'll get a URL like: `https://oracle-a1-dashboard.onrender.com`

## Step 6: Access Your Dashboard

1. Open: `https://oracle-a1-dashboard.onrender.com`
2. Fill in the form fields:
   - **Display Name**: Name for your instance
   - **OCPUs**: Number of CPU cores
   - **Memory**: RAM in GB
   - **Availability Domain**: Get from `list_availability_domain` locally first
   - **Subnet ID**: Get from `list_available_subnet` locally first
   - **SSH Key Path**: Your SSH public key file path
   - **Email**: (Optional) Email for notifications

3. Click **Create Instance**
4. Check **Recent Executions** for status and logs

## Getting Oracle IDs Before Deployment

Since you can't run CLI commands on Render, get your Availability Domain and Subnet ID locally first:

```bash
# On your local machine
poetry run get_oracle_a1 list_availability_domain
poetry run get_oracle_a1 list_available_subnet
```

Then fill these into the dashboard form.

## Troubleshooting

### "Config file not found" error

Render's `preDeployCommand` should create it, but if it fails:
1. Check the build logs in Render dashboard
2. Verify all OCI secrets are set correctly
3. Ensure the private key content is complete (with BEGIN/END lines)

### "Authentication failed" error

- Double-check your OCI credentials in Render
- Verify fingerprint matches the one in Oracle Console
- Make sure the private key is in PEM format
- Check that user, tenancy, and region are correct

### "Email not sending" error

- Verify SMTP_USER and SMTP_PASSWORD are set
- If using Gmail, ensure you generated an App Password (not your regular password)
- Check that SMTP_SERVER and SMTP_PORT are correct

### "Out of host capacity" when creating instance

This is normal for A1.Flex instances - the tool automatically retries. Just wait and it will keep trying.

## Advanced: Using Render Cron Jobs

If you want to automatically attempt to create instances on a schedule:

1. Create a separate Cron Job service in Render
2. Schedule it to run your creation command
3. Use the same environment variables

```bash
# Example cron schedule (run daily at 9 AM UTC)
0 9 * * * poetry run get_oracle_a1 create --display-name daily-instance ...
```

## Cost Considerations

- **Free tier**: Renders free instances spin down after 15 minutes of inactivity
- **Paid tier**: Continuous uptime, recommended for production
- **Recommendation**: Start with free, upgrade if you want guaranteed uptime

## Monitoring & Logs

1. Go to **Logs** tab in Render dashboard to see real-time logs
2. Check **Recent Executions** in the dashboard for task history
3. Email notifications will be sent if configured

## Scaling & Upgrades

After your instance is created, use the **Increase Resources** tab to upgrade:

1. Enter your instance name
2. Set new OCPU and Memory values
3. Check "Incremental" to scale gradually
4. Click **Increase Resources**

## Security Notes

⚠️ **Important**:
- Always use **Secrets** (lock icon) for sensitive data
- Never commit credentials to GitHub
- Rotate your OCI private key periodically
- Use Gmail App Passwords, not your actual password
- Keep your Flask secret key secure

## Support

- Render Support: https://render.com/docs
- Oracle OCI Docs: https://docs.oracle.com/
- GitHub Issues: Create an issue on your repo

---

**Next**: After deployment, open your dashboard URL and try creating an instance!
