# Get the directory where this script is located
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDirectory

# Define the virtual environment directory name
$VenvName = "venv"
$VenvPath = Join-Path $ScriptDirectory $VenvName




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
    (Join-Path $VenvPath "Scripts" | Join-Path -ChildPath "Activate.ps1")  # Windows
    (Join-Path $VenvPath "bin" | Join-Path -ChildPath "Activate.ps1")      # Linux
    (Join-Path $VenvPath "bin" | Join-Path -ChildPath "activate.ps1")      # uv
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
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

pip install -r requirements.txt

python main.py