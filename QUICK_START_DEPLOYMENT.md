# Quick Start Deployment Guide

## For Developers (Local Machine)

### Step 1: Run the Deployment Script

```powershell
# Run this in PowerShell from the project root
.\deploy.ps1
```

This script will:
- Build the React frontend
- Copy dist files to PythonProject2
- Create a deployment package

### Step 2: Update Production API URL

Before building for production, create or update `splitter/.env.production`:

```env
VITE_API_BASE_URL=http://yourserver.com/api
```

Replace `yourserver.com` with your actual server address or IP.

Then rebuild:
```powershell
cd splitter
npm run build
cd ..
```

---

## For Server Administrators (IIS Server)

### Prerequisites Installation

1. **Install Python 3.11+**
   - Download from https://www.python.org/downloads/
   - Install to `C:\Python311`
   - ✅ Check "Add Python to PATH"

2. **Install IIS Components**
   - Open PowerShell as Administrator:
   ```powershell
   # Enable IIS
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-ApplicationDevelopment
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-NetFxExtensibility45
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-HealthAndDiagnostics
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpLogging
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-Security
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-RequestFiltering
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-Performance
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerManagementTools
   Enable-WindowsOptionalFeature -Online -FeatureName IIS-ManagementConsole
   ```

3. **Download and Install:**
   - **URL Rewrite Module**: https://www.iis.net/downloads/microsoft/url-rewrite
   - **HttpPlatformHandler**: https://www.iis.net/downloads/microsoft/httpplatformhandler

### Quick Deployment Steps

1. **Copy Files**
   ```powershell
   # Create directory
   mkdir C:\inetpub\wwwroot\SplitterRedo
   
   # Copy deployment_package contents to C:\inetpub\wwwroot\SplitterRedo
   ```

2. **Install Python Dependencies**
   ```powershell
   cd C:\inetpub\wwwroot\SplitterRedo\PythonProject2
   pip install -r requirements.txt
   ```

3. **Update web.config**
   - Open `C:\inetpub\wwwroot\SplitterRedo\web.config`
   - Update Python path if needed (default is `C:\Python311\python.exe`)

4. **Set Permissions**
   ```powershell
   icacls "C:\inetpub\wwwroot\SplitterRedo" /grant "IIS_IUSRS:(OI)(CI)F" /T
   ```

5. **Create Application Pool in IIS**
   ```powershell
   # Open IIS Manager
   %windir%\system32\inetsrv\inetmgr.exe
   ```
   
   - Right-click "Application Pools" → "Add Application Pool"
   - Name: `SplitterAppPool`
   - .NET CLR Version: `No Managed Code`
   - Click OK

6. **Create Website**
   - Right-click "Sites" → "Add Website"
   - Site name: `Splitter`
   - Application pool: `SplitterAppPool`
   - Physical path: `C:\inetpub\wwwroot\SplitterRedo`
   - Port: 80 (or your preferred port)
   - Click OK

7. **Start the Website**
   - In IIS Manager, select your website
   - Click "Start" in the Actions panel

8. **Test**
   - Open browser: `http://localhost/api/health`
   - Should see: `{"status":"healthy",...}`

---

## Testing Checklist

- [ ] Health check works: `http://yourserver/api/health`
- [ ] Frontend loads: `http://yourserver/`
- [ ] Can select payment mode
- [ ] Can upload file
- [ ] Can process file
- [ ] Can export results

---

## Troubleshooting

### Python Not Found Error
- Update `processPath` in web.config with correct Python path
- Run `where python` in PowerShell to find Python location

### 500 Error
- Check logs: `C:\inetpub\wwwroot\SplitterRedo\logs\python.log`
- Ensure all dependencies installed: `pip list`

### Upload Fails
- Check permissions on uploads folder
- Verify `maxAllowedContentLength` in web.config

### API Returns 404
- Ensure URL Rewrite Module is installed
- Check web.config rewrite rules

---

## Production Checklist

- [ ] HTTPS configured with SSL certificate
- [ ] Firewall rules configured
- [ ] Application pool set to "AlwaysRunning"
- [ ] Automatic backups configured
- [ ] Monitoring/logging configured
- [ ] Debug mode disabled in app.py

---

For detailed information, see **DEPLOYMENT_GUIDE.md**

