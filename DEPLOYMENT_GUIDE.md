# IIS Deployment Guide for Splitter Application

This guide will help you deploy the Splitter application (Flask backend + React frontend) to IIS on Windows Server.

## Prerequisites

1. **Windows Server** with IIS installed
2. **Python 3.11** or higher
3. **Node.js 18+** and npm (for building the frontend)
4. **IIS URL Rewrite Module** - Download from: https://www.iis.net/downloads/microsoft/url-rewrite
5. **HttpPlatformHandler** - Download from: https://www.iis.net/downloads/microsoft/httpplatformhandler

## Deployment Steps

### Step 1: Install Required Software on Server

1. **Install Python**
   ```powershell
   # Download Python from python.org
   # Install to C:\Python311 (or update path in web.config)
   # Make sure to check "Add Python to PATH" during installation
   ```

2. **Verify Python Installation**
   ```powershell
   python --version
   pip --version
   ```

3. **Install IIS Components**
   - Open Server Manager
   - Add Roles and Features → Web Server (IIS)
   - Install URL Rewrite Module
   - Install HttpPlatformHandler

### Step 2: Prepare the Application

#### 2.1 Build the React Frontend

On your development machine (or on the server):

```powershell
# Navigate to the React app directory
cd splitter

# Install dependencies (if not already done)
npm install

# Build for production
npm run build
```

This creates a `dist` folder with optimized static files.

#### 2.2 Copy the Built Frontend to Backend

```powershell
# Copy the dist folder to PythonProject2 directory
xcopy /E /I splitter\dist PythonProject2\dist
```

### Step 3: Deploy to IIS Server

1. **Create Application Directory on Server**
   ```powershell
   # Create directory
   mkdir C:\inetpub\wwwroot\SplitterRedo
   
   # Copy your entire project to the server
   # You can use FTP, RDP copy/paste, or other file transfer methods
   ```

2. **Copy Files to Server**
   - Copy the entire `PythonProject2` folder
   - Copy the `web.config` file to the root of your application
   - Ensure the `dist` folder is inside `PythonProject2`

   Directory structure should be:
   ```
   C:\inetpub\wwwroot\SplitterRedo\
   ├── web.config
   └── PythonProject2\
       ├── app.py
       ├── requirements.txt
       ├── routes\
       ├── parsers\
       ├── services\
       ├── uploads\
       └── dist\
           ├── index.html
           └── assets\
   ```

3. **Install Python Dependencies on Server**
   ```powershell
   cd C:\inetpub\wwwroot\SplitterRedo\PythonProject2
   pip install -r requirements.txt
   ```

### Step 4: Configure IIS

1. **Create a New Application Pool**
   - Open IIS Manager
   - Right-click on "Application Pools" → "Add Application Pool"
   - Name: `SplitterAppPool`
   - .NET CLR Version: `No Managed Code`
   - Click OK

2. **Configure Application Pool Settings**
   - Right-click `SplitterAppPool` → Advanced Settings
   - Set the following:
     - `Start Mode`: AlwaysRunning
     - `Idle Time-out (minutes)`: 0 (or higher value)
     - `Maximum Worker Processes`: 1 (or more for scaling)

3. **Create Website or Application**

   **Option A: New Website**
   - Right-click "Sites" → "Add Website"
   - Site name: `Splitter`
   - Application pool: `SplitterAppPool`
   - Physical path: `C:\inetpub\wwwroot\SplitterRedo`
   - Binding: 
     - Type: http
     - Port: 80 (or your preferred port)
     - Host name: (optional, e.g., splitter.yourdomain.com)
   - Click OK

   **Option B: Application under Default Website**
   - Right-click "Default Web Site" → "Add Application"
   - Alias: `splitter`
   - Application pool: `SplitterAppPool`
   - Physical path: `C:\inetpub\wwwroot\SplitterRedo`
   - Click OK

4. **Set Permissions**
   ```powershell
   # Give IIS permission to read/write to the application directory
   icacls "C:\inetpub\wwwroot\SplitterRedo" /grant "IIS_IUSRS:(OI)(CI)F" /T
   icacls "C:\inetpub\wwwroot\SplitterRedo\PythonProject2\uploads" /grant "IIS_IUSRS:(OI)(CI)F" /T
   ```

### Step 5: Update Frontend API URL

Update the frontend to point to the production server:

1. Create a `.env.production` file in the `splitter` folder:
   ```
   VITE_API_BASE_URL=http://yourserver.com/api
   ```

2. Rebuild the frontend:
   ```powershell
   cd splitter
   npm run build
   ```

3. Copy the new `dist` folder to the server.

### Step 6: Test the Deployment

1. **Test the Backend**
   - Open browser: `http://yourserver.com/api/health`
   - Should return: `{"status":"healthy","message":"Splitter API is running",...}`

2. **Test the Frontend**
   - Open browser: `http://yourserver.com/`
   - Should display the Splitter application

3. **Test File Upload**
   - Try uploading a file and processing it
   - Check for any errors in the browser console

### Step 7: Check Logs (If Issues Occur)

Logs are stored in: `C:\inetpub\wwwroot\SplitterRedo\logs\python.log`

```powershell
# View logs
type C:\inetpub\wwwroot\SplitterRedo\logs\python.log
```

## Troubleshooting

### Issue: 500 Internal Server Error

1. Check Python path in `web.config` matches your installation
2. Check permissions on the application folder
3. Check logs in `logs\python.log`
4. Ensure all dependencies are installed: `pip list`

### Issue: Application Not Starting

1. Check if HttpPlatformHandler is installed
2. Verify Python path in web.config
3. Check Application Pool settings
4. Look at Windows Event Viewer → Application logs

### Issue: File Upload Fails

1. Check upload directory exists and has write permissions
2. Verify `maxAllowedContentLength` in web.config
3. Check IIS upload limits

### Issue: API Routes Return 404

1. Ensure URL Rewrite module is installed
2. Check web.config rewrite rules
3. Verify Flask routes are registered correctly

## Production Optimizations

### 1. Enable HTTPS

1. Get an SSL certificate
2. In IIS Manager → Bindings → Add
3. Type: https, Port: 443, SSL Certificate: (select your certificate)

### 2. Disable Debug Mode

In `app.py`, ensure debug is set to False:
```python
if __name__ == '__main__':
    app.run(debug=False)  # Ensure this is False
```

### 3. Set Up Application Monitoring

Consider installing:
- **Application Insights** for monitoring
- **New Relic** or similar APM tools
- Enable IIS Failed Request Tracing

### 4. Configure Firewall

```powershell
# Allow HTTP traffic
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# Allow HTTPS traffic
New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
```

### 5. Set Up Automatic Backups

Create scheduled tasks to backup:
- Application files
- Upload directory
- Logs

## Updating the Application

To update the application:

1. Build new frontend: `npm run build`
2. Stop IIS Application Pool
3. Copy new files to server
4. Update Python dependencies if changed: `pip install -r requirements.txt`
5. Start IIS Application Pool

## Alternative: Using wfastcgi Instead of HttpPlatformHandler

If you prefer using wfastcgi:

1. Install wfastcgi:
   ```powershell
   pip install wfastcgi
   wfastcgi-enable
   ```

2. Use the alternative `web.config` (see `web.config.wfastcgi`)

## Support and Maintenance

- Monitor logs regularly
- Set up automated health checks
- Keep Python and dependencies updated
- Regular security patches for Windows Server and IIS

## Useful Commands

```powershell
# Restart Application Pool
%windir%\system32\inetsrv\appcmd recycle apppool /apppool.name:SplitterAppPool

# Stop Application Pool
%windir%\system32\inetsrv\appcmd stop apppool /apppool.name:SplitterAppPool

# Start Application Pool
%windir%\system32\inetsrv\appcmd start apppool /apppool.name:SplitterAppPool

# View IIS logs
Get-Content "C:\inetpub\logs\LogFiles\W3SVC1\*.log" -Tail 50
```

---

## Quick Deployment Checklist

- [ ] Python 3.11+ installed on server
- [ ] HttpPlatformHandler installed
- [ ] URL Rewrite Module installed
- [ ] Frontend built (`npm run build`)
- [ ] Files copied to `C:\inetpub\wwwroot\SplitterRedo`
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] `web.config` updated with correct Python path
- [ ] Application Pool created and configured
- [ ] Website/Application created in IIS
- [ ] Permissions set (IIS_IUSRS has access)
- [ ] Logs directory created
- [ ] Frontend `.env.production` configured
- [ ] Health check endpoint working (`/api/health`)
- [ ] File upload tested
- [ ] HTTPS configured (for production)

---

**Need Help?** Check the logs first, then review the troubleshooting section above.

