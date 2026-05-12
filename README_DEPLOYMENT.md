# Splitter Application - IIS Deployment

This folder contains everything you need to deploy the Splitter application to IIS on Windows Server.

## 📋 What's Included

- **web.config** - IIS configuration file (HttpPlatformHandler)
- **web.config.wfastcgi** - Alternative IIS configuration (wfastcgi)
- **deploy.ps1** - Script to prepare deployment package (run on dev machine)
- **server-management.ps1** - Script to manage the app on IIS server
- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment documentation
- **QUICK_START_DEPLOYMENT.md** - Quick reference guide
- **env.production.example** - Template for production environment variables

## 🚀 Quick Start

### On Your Development Machine

1. **Update the API URL**
   ```powershell
   # Copy env.production.example to splitter/.env.production
   copy env.production.example splitter\.env.production
   
   # Edit splitter/.env.production and set your server URL
   # VITE_API_BASE_URL=http://yourserver.com/api
   ```

2. **Run deployment script**
   ```powershell
   .\deploy.ps1
   ```

3. **Transfer files**
   - Copy the `deployment_package` folder to your IIS server

### On Your IIS Server

1. **Prerequisites** (one-time setup)
   - Install Python 3.11+
   - Install URL Rewrite Module
   - Install HttpPlatformHandler

2. **Copy files to server**
   ```powershell
   # Place deployment package in:
   C:\inetpub\wwwroot\SplitterRedo
   ```

3. **Run installation script**
   ```powershell
   # Run as Administrator
   cd C:\inetpub\wwwroot\SplitterRedo
   .\server-management.ps1 install
   ```

4. **Test**
   - Open browser: `http://localhost/api/health`
   - Should see: `{"status":"healthy",...}`

## 📖 Documentation

- **[QUICK_START_DEPLOYMENT.md](QUICK_START_DEPLOYMENT.md)** - Fast deployment guide
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Detailed step-by-step instructions

## 🔧 Server Management

Use the `server-management.ps1` script on the IIS server:

```powershell
# Check status
.\server-management.ps1 status

# Start application
.\server-management.ps1 start

# Stop application
.\server-management.ps1 stop

# Restart application
.\server-management.ps1 restart

# View logs
.\server-management.ps1 logs

# Install/reinstall
.\server-management.ps1 install
```

## 🌐 Default Locations

| Item | Path |
|------|------|
| Application Files | `C:\inetpub\wwwroot\SplitterRedo` |
| Python Files | `C:\inetpub\wwwroot\SplitterRedo\PythonProject2` |
| Uploads | `C:\inetpub\wwwroot\SplitterRedo\PythonProject2\uploads` |
| Logs | `C:\inetpub\wwwroot\SplitterRedo\logs\python.log` |
| Python | `C:\Python311\python.exe` |
| Application Pool | `SplitterAppPool` |

## ✅ Deployment Checklist

- [ ] Python 3.11+ installed on server
- [ ] HttpPlatformHandler installed
- [ ] URL Rewrite Module installed
- [ ] `.env.production` configured with server URL
- [ ] Frontend built (`npm run build`)
- [ ] Files copied to server
- [ ] Python dependencies installed
- [ ] Permissions set
- [ ] Application pool created
- [ ] Website created and started
- [ ] Health check endpoint works
- [ ] File upload tested

## 🆘 Troubleshooting

### Application won't start
1. Check Python path in `web.config`
2. View logs: `.\server-management.ps1 logs`
3. Check permissions: `icacls C:\inetpub\wwwroot\SplitterRedo`

### 500 Internal Server Error
1. Check if HttpPlatformHandler is installed
2. Verify Python dependencies: `pip list`
3. Check application logs

### Upload fails
1. Check file size limits in `web.config`
2. Verify upload folder exists and has write permissions
3. Check IIS request filtering settings

### API returns 404
1. Ensure URL Rewrite Module is installed
2. Check `web.config` rewrite rules
3. Verify Flask routes are registered

## 📊 Monitoring

Monitor these regularly:
- Application logs: `C:\inetpub\wwwroot\SplitterRedo\logs\python.log`
- IIS logs: `C:\inetpub\logs\LogFiles\`
- Event Viewer → Application logs

## 🔒 Security (Production)

For production environments:

1. **Enable HTTPS**
   - Get SSL certificate
   - Configure HTTPS binding in IIS
   - Update API URL to use `https://`

2. **Configure Firewall**
   ```powershell
   New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
   New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
   ```

3. **Disable Debug Mode**
   - Ensure `debug=False` in `app.py`

4. **Regular Updates**
   - Keep Python updated
   - Update Python packages regularly
   - Apply Windows security patches

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Review the troubleshooting section
3. Consult DEPLOYMENT_GUIDE.md for detailed information

---

**Ready to deploy?** Start with [QUICK_START_DEPLOYMENT.md](QUICK_START_DEPLOYMENT.md)!

