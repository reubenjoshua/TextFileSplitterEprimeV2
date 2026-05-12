# PowerShell Deployment Script for Splitter Application
# Run this script on your development machine to prepare for deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Splitter Application Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Frontend
Write-Host "[Step 1/4] Building React Frontend..." -ForegroundColor Yellow
Set-Location -Path "splitter"

if (Test-Path "node_modules") {
    Write-Host "Dependencies already installed, skipping npm install..." -ForegroundColor Green
} else {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Building production bundle..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Frontend built successfully!" -ForegroundColor Green
Set-Location -Path ".."

# Step 2: Copy dist to PythonProject2
Write-Host ""
Write-Host "[Step 2/4] Copying dist folder to PythonProject2..." -ForegroundColor Yellow

if (Test-Path "PythonProject2\dist") {
    Remove-Item -Path "PythonProject2\dist" -Recurse -Force
}

Copy-Item -Path "splitter\dist" -Destination "PythonProject2\dist" -Recurse
Write-Host "Dist folder copied successfully!" -ForegroundColor Green

# Step 3: Create deployment package
Write-Host ""
Write-Host "[Step 3/4] Creating deployment package..." -ForegroundColor Yellow

$deployFolder = "deployment_package"
if (Test-Path $deployFolder) {
    Remove-Item -Path $deployFolder -Recurse -Force
}

New-Item -ItemType Directory -Path $deployFolder | Out-Null
New-Item -ItemType Directory -Path "$deployFolder\PythonProject2" | Out-Null

# Copy necessary files
Write-Host "Copying files..." -ForegroundColor Yellow
Copy-Item -Path "web.config" -Destination $deployFolder
Copy-Item -Path "PythonProject2\*" -Destination "$deployFolder\PythonProject2" -Recurse -Exclude "__pycache__","*.pyc"

# Create logs directory
New-Item -ItemType Directory -Path "$deployFolder\logs" -Force | Out-Null

Write-Host "Deployment package created in '$deployFolder' folder!" -ForegroundColor Green

# Step 4: Display next steps
Write-Host ""
Write-Host "[Step 4/4] Deployment Package Ready!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Copy the '$deployFolder' folder to your IIS server" -ForegroundColor White
Write-Host "   Recommended path: C:\inetpub\wwwroot\SplitterRedo" -ForegroundColor Gray
Write-Host ""
Write-Host "2. On the server, install Python dependencies:" -ForegroundColor White
Write-Host "   cd C:\inetpub\wwwroot\SplitterRedo\PythonProject2" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Update web.config with correct Python path" -ForegroundColor White
Write-Host "   (Default: C:\Python311\python.exe)" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Update .env.production with your server URL" -ForegroundColor White
Write-Host "   (Located in splitter/.env.production)" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Follow DEPLOYMENT_GUIDE.md for IIS configuration" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Files ready for deployment!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

