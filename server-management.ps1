# IIS Application Management Script
# Run this on the IIS server to manage the Splitter application

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('start','stop','restart','status','logs','install')]
    [string]$Action = 'status'
)

$AppPoolName = "SplitterAppPool"
$SiteName = "Splitter"
$AppPath = "C:\inetpub\wwwroot\SplitterRedo"
$LogPath = "$AppPath\logs\python.log"

function Show-Status {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Splitter Application Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Check Application Pool
    $pool = Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue
    if ($pool) {
        Write-Host "Application Pool: " -NoNewline
        if ($pool.Value -eq "Started") {
            Write-Host "RUNNING" -ForegroundColor Green
        } else {
            Write-Host "STOPPED" -ForegroundColor Red
        }
    } else {
        Write-Host "Application Pool: NOT FOUND" -ForegroundColor Yellow
    }
    
    # Check Website
    $site = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
    if ($site) {
        Write-Host "Website: " -NoNewline
        if ($site.State -eq "Started") {
            Write-Host "RUNNING" -ForegroundColor Green
        } else {
            Write-Host "STOPPED" -ForegroundColor Red
        }
    } else {
        Write-Host "Website: NOT FOUND" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Start-Application {
    Write-Host "Starting Splitter Application..." -ForegroundColor Yellow
    Start-WebAppPool -Name $AppPoolName -ErrorAction SilentlyContinue
    Start-Website -Name $SiteName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Show-Status
}

function Stop-Application {
    Write-Host "Stopping Splitter Application..." -ForegroundColor Yellow
    Stop-Website -Name $SiteName -ErrorAction SilentlyContinue
    Stop-WebAppPool -Name $AppPoolName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Show-Status
}

function Restart-Application {
    Write-Host "Restarting Splitter Application..." -ForegroundColor Yellow
    Stop-Application
    Start-Sleep -Seconds 2
    Start-Application
}

function Show-Logs {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Recent Logs (Last 50 lines)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    if (Test-Path $LogPath) {
        Get-Content $LogPath -Tail 50
    } else {
        Write-Host "Log file not found at: $LogPath" -ForegroundColor Yellow
    }
}

function Install-Application {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installing Splitter Application" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Create Application Pool
    Write-Host "`n[1/5] Creating Application Pool..." -ForegroundColor Yellow
    $poolExists = Get-WebAppPoolState -Name $AppPoolName -ErrorAction SilentlyContinue
    if ($poolExists) {
        Write-Host "Application Pool already exists" -ForegroundColor Green
    } else {
        New-WebAppPool -Name $AppPoolName
        Set-ItemProperty IIS:\AppPools\$AppPoolName -name "managedRuntimeVersion" -value ""
        Write-Host "Application Pool created" -ForegroundColor Green
    }
    
    # Create Website
    Write-Host "`n[2/5] Creating Website..." -ForegroundColor Yellow
    $siteExists = Get-Website -Name $SiteName -ErrorAction SilentlyContinue
    if ($siteExists) {
        Write-Host "Website already exists" -ForegroundColor Green
    } else {
        New-Website -Name $SiteName -PhysicalPath $AppPath -ApplicationPool $AppPoolName -Port 80
        Write-Host "Website created" -ForegroundColor Green
    }
    
    # Set Permissions
    Write-Host "`n[3/5] Setting Permissions..." -ForegroundColor Yellow
    icacls $AppPath /grant "IIS_IUSRS:(OI)(CI)F" /T | Out-Null
    Write-Host "Permissions set" -ForegroundColor Green
    
    # Create logs directory
    Write-Host "`n[4/5] Creating logs directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "$AppPath\logs" -Force | Out-Null
    Write-Host "Logs directory created" -ForegroundColor Green
    
    # Install Python dependencies
    Write-Host "`n[5/5] Installing Python dependencies..." -ForegroundColor Yellow
    $requirementsPath = "$AppPath\PythonProject2\requirements.txt"
    if (Test-Path $requirementsPath) {
        Set-Location "$AppPath\PythonProject2"
        pip install -r requirements.txt
        Write-Host "Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "Requirements.txt not found" -ForegroundColor Yellow
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    
    Start-Application
}

# Main script execution
Write-Host ""
switch ($Action) {
    'start' { Start-Application }
    'stop' { Stop-Application }
    'restart' { Restart-Application }
    'status' { Show-Status }
    'logs' { Show-Logs }
    'install' { Install-Application }
}

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 start    - Start the application" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 stop     - Stop the application" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 restart  - Restart the application" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 status   - Show application status" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 logs     - View recent logs" -ForegroundColor Gray
Write-Host "  .\server-management.ps1 install  - Install application in IIS" -ForegroundColor Gray
Write-Host ""

