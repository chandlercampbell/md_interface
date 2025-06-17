# Get the directory where this script is located
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDirectory

# Define the virtual environment directory name
$VenvName = "venv"
$VenvPath = Join-Path $ScriptDirectory $VenvName

# Check if virtual environment already exists
if (-Not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python3 -m venv $VenvName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment. Make sure Python is installed and accessible."
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
$Paths = @(
    Join-Path $VenvPath "Scripts" "Activate.ps1"  # Windows
    Join-Path $VenvPath "bin" "Activate.ps1"          # Linux
    Join-Path $VenvPath "bin" "activate.ps1"        # uv
)
$FoundPath = 0
foreach ($Path in $Paths) {
    if (Test-Path $Path) {
        . $Path
        $FoundPath = 1
        break
    }
}
if ($FoundPath -eq 0) {
    Write-Error "Failed to find activation script for the virtual environment."
    exit 1
}


pip3 install -r requirements.txt

python3 main.py