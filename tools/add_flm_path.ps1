$flmDir = "C:\Program Files\flm"
$cur = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($cur -notlike "*$flmDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$cur;$flmDir", "User")
    Write-Host "[OK] Agregado al PATH de usuario: $flmDir"
} else {
    Write-Host "[OK] Ya estaba en PATH."
}
$env:PATH += ";$flmDir"
Write-Host ""
Write-Host "Verificando flm..."
& "$flmDir\flm.exe" --version
