# 🎯 Render Deployment - Quick Reference

## Deployment Flow Chart

```
1. Prepare Credentials (5 min)
   ↓
2. Push to GitHub (2 min)
   ↓
3. Create Render Service (3 min)
   ↓
4. Add Secrets in Render (10 min)
   ↓
5. Deploy & Test (5 min)
   ↓
✅ Dashboard Live!
```

## Timeline: 25 minutes total

## Essential Credentials You Need

### From Oracle Cloud Console
| Item | Where to Find | Format |
|------|---------------|--------|
| **User OCID** | Profile → User settings | `ocid1.user.oc1...` |
| **Fingerprint** | Profile → API Keys | `aa:bb:cc:dd:...` |
| **Tenancy OCID** | Tenancy Details | `ocid1.tenancy.oc1...` |
| **Private Key** | Downloaded when created | PEM file content |
| **Region** | Your account settings | `ap-hyderabad-1` |

### From Local CLI Setup
| Item | Command | Format |
|------|---------|--------|
| **Availability Domain** | `poetry run get_oracle_a1 list_availability_domain` | `vMqB:AP-HYDERABAD-1-AD-1` |
| **Subnet ID** | `poetry run get_oracle_a1 list_available_subnet` | `ocid1.subnet.oc1...` |

## Render Environment Variables Checklist

### Regular Env Vars
```
FLASK_ENV=production
OCI_CONFIG_FILE=~/.oci/config
PYTHONUNBUFFERED=true
```

### Secrets (use lock icon 🔒)
```
OCI_USER=ocid1.user.oc1...
OCI_FINGERPRINT=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
OCI_TENANCY=ocid1.tenancy.oc1...
OCI_REGION=ap-hyderabad-1
OCI_PRIVATE_KEY=[FULL PEM CONTENT WITH BEGIN/END LINES]
```

### Optional Email Secrets
```
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=[16-char Gmail App Password]
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## File Reference

| File | Purpose | Read When |
|------|---------|-----------|
| [DEPLOY_SUMMARY.md](DEPLOY_SUMMARY.md) | Overview of what was created | First (you're here!) |
| [RENDER_DEPLOY.md](RENDER_DEPLOY.md) | Detailed step-by-step guide | Need detailed help |
| [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) | Checklist to follow | While deploying |
| [app.py](app.py) | Flask web application | Reference implementation |
| [templates/dashboard.html](templates/dashboard.html) | Web UI | Customize appearance |
| [render.yaml](render.yaml) | Render configuration | Advanced customization |

## Common Tasks

### Task 1: Get Oracle IDs
```bash
# Run these commands locally to get IDs for the dashboard
poetry run get_oracle_a1 list_availability_domain
poetry run get_oracle_a1 list_available_subnet
```

### Task 2: Deploy to Render
1. Go to https://dashboard.render.com
2. New Web Service
3. Connect GitHub repo
4. Set secrets (OCI_USER, OCI_FINGERPRINT, etc.)
5. Click Deploy

### Task 3: Use Dashboard
1. Open https://oracle-a1-dashboard.onrender.com
2. Fill in form (use IDs from Task 1)
3. Click Create Instance
4. View logs in real-time

### Task 4: Scale Instance
1. Go to "Increase Resources" tab
2. Enter instance name
3. Set new OCPU/Memory
4. Click Increase Resources

## Troubleshooting Guide

| Problem | Solution |
|---------|----------|
| **"Config file not found"** | Set OCI_PRIVATE_KEY secret in Render |
| **"Authentication failed"** | Verify OCI_USER, OCI_FINGERPRINT, OCI_TENANCY |
| **"Subnet not found"** | Copy exact Subnet OCID from list command |
| **"Email not sending"** | Use Gmail App Password, not regular password |
| **Deploy keeps failing** | Check Render logs, verify Python 3.11+ |
| **Slow instance creation** | Normal for A1.Flex, tool auto-retries |

## Important Security Notes

🔒 **Do's**
- ✅ Keep GitHub repository PRIVATE
- ✅ Use Render Secrets (lock icon 🔒) for credentials
- ✅ Use Gmail App Passwords (not regular password)
- ✅ Rotate credentials periodically
- ✅ Keep local `.oci/` folder in `.gitignore`

🚫 **Don'ts**
- ❌ Don't commit credentials to GitHub
- ❌ Don't use regular passwords for Gmail
- ❌ Don't share your private key
- ❌ Don't use regular Env Vars for secrets

## URLs & Links

| Service | URL |
|---------|-----|
| **Render Dashboard** | https://dashboard.render.com |
| **Your Dashboard** | https://oracle-a1-dashboard.onrender.com |
| **Oracle Console** | https://console.oracle.com |
| **GitHub Account** | https://github.com/your-username/get_oracle_a1 |

## API Endpoints (for integration)

```
POST /api/create-instance - Create new instance
POST /api/increase-resources - Scale up instance
GET /api/executions - List all executions
GET /api/executions/<id> - Get execution details
GET /api/config - Get configuration options
GET /api/health - Health check
```

## Examples

### Example: Create Instance
```bash
curl -X POST https://oracle-a1-dashboard.onrender.com/api/create-instance \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "my-instance",
    "availability_domain": "vMqB:AP-HYDERABAD-1-AD-1",
    "subnet_id": "ocid1.subnet.oc1...",
    "ocpu": 2,
    "memory": 12,
    "os_name": "Canonical Ubuntu",
    "os_version": "22.04",
    "boot_volume_size": 100,
    "ssh_authorized_keys": "/root/.ssh/id_rsa.pub",
    "send_notification": true,
    "notification_email": "your@email.com"
  }'
```

### Example: Check Status
```bash
curl https://oracle-a1-dashboard.onrender.com/api/executions
```

## Support Matrix

| Issue | Where to Ask |
|-------|-------------|
| Oracle Cloud credentials | Oracle Support / Docs |
| Render deployment | Render Support / Docs |
| Flask/Python code | GitHub Issues / Python Docs |
| OCI SDK | Oracle OCI SDK Docs |

## Next Steps

1. ✅ Read this quick reference (you're done!)
2. ⏭️ Read [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) for step-by-step guide
3. ⏭️ Gather your Oracle credentials
4. ⏭️ Push code to GitHub
5. ⏭️ Create Render service
6. ⏭️ Add secrets
7. ⏭️ Deploy!
8. ⏭️ Open dashboard and create first instance

---

**Ready to deploy?** → Start with [RENDER_CHECKLIST.md](RENDER_CHECKLIST.md) 🚀
