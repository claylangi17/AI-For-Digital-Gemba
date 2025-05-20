# Check if .venv exists, if not create it
if (-Not (Test-Path -Path ".\.venv")) {
    Write-Host "Creating new virtual environment..."
    python -m venv .venv
}
else {
    Write-Host "Virtual environment already exists"
}

# Activate the virtual environment
.\\.venv\Scripts\Activate.ps1

# Check for requirements.txt and install dependencies if it exists
if (Test-Path -Path ".\requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
}
else {
    Write-Host "No requirements.txt found. Skipping dependency installation."
}

Write-Host "Virtual environment is ready!"
