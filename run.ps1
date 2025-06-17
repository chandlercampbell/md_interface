# Get the directory where this script is located
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDirectory

# Define the virtual environment directory name
$VenvName = "venv"
$VenvPath = Join-Path $ScriptDirectory $VenvName


function python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @args
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 @args
    } else {
        Write-Error "Neither python nor python found in PATH"
    }
}

function pip {
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        & pip @args
    } elseif (Get-Command pip3 -ErrorAction SilentlyContinue) {
        & pip3 @args
    } else {
        Write-Error "Neither pip nor pip3 found in PATH"
    }
}

# Check if virtual environment already exists
if (-Not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv $VenvName
    
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


pip install -r requirements.txt

python main.py