# Instala la skill /video-comic para usarla en CUALQUIER proyecto de Claude Code (Windows).
# Uso (un solo comando en PowerShell):
#   irm https://raw.githubusercontent.com/adrian0659/shorts-animados-claude/main/instalar-video-comic.ps1 | iex
$ErrorActionPreference = "Stop"
$rama = if ($env:RAMA) { $env:RAMA } else { "main" }
$dest = Join-Path $HOME ".claude\skills"
$tmp = Join-Path $env:TEMP ("video-comic-" + [guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $tmp, $dest | Out-Null
Write-Host "==> Descargando la skill video-comic (rama $rama)..."
$zip = Join-Path $tmp "repo.zip"
Invoke-WebRequest "https://codeload.github.com/adrian0659/shorts-animados-claude/zip/refs/heads/$rama" -OutFile $zip
Expand-Archive $zip -DestinationPath $tmp
$src = Get-ChildItem $tmp -Directory | Select-Object -First 1
if (Test-Path (Join-Path $dest "video-comic")) { Remove-Item -Recurse -Force (Join-Path $dest "video-comic") }
Copy-Item -Recurse (Join-Path $src.FullName ".claude\skills\video-comic") (Join-Path $dest "video-comic")
Remove-Item -Recurse -Force $tmp
Write-Host "==> Skill instalada en $dest\video-comic"
Write-Host "==> Revisando herramientas..."
foreach ($c in "ffmpeg", "python") { if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Write-Host "   Falta $c  ->  winget install $c" } }
if (Get-Command python -ErrorAction SilentlyContinue) { python -m pip install -q pillow numpy faster-whisper }
Write-Host "   Para archivos .cbr instala 7-Zip o unar (o usa .cbz / .pdf)."
Write-Host ""
Write-Host "Listo. Abre Claude Code en cualquier carpeta y escribe:"
Write-Host "   /video-comic ¿Sabías que ...? [enlace o archivo del cómic]"
