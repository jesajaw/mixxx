<#
.SYNOPSIS
  Installs the StudioDeck skin and (optionally) the keyboard layout for Mixxx on Windows.

.DESCRIPTION
  .\install\install.ps1                 Link the skin as a junction (no admin rights needed)
  .\install\install.ps1 -Copy           Copy the skin instead
  .\install\install.ps1 -NoKeyboard     Leave the keyboard layout alone
  .\install\install.ps1 -Uninstall      Remove everything
  .\install\install.ps1 -DataDir "D:\Mixxx"   Set the Mixxx data folder manually

  If PowerShell refuses to run the script ("running scripts is disabled on this system"),
  double-click install\install.bat or run:
    powershell -NoProfile -ExecutionPolicy Bypass -File install\install.ps1
#>
param(
  [switch]$Copy, [switch]$NoKeyboard, [switch]$Uninstall,
  [string]$DataDir = ""
)
$ErrorActionPreference = "Stop"

# Remove a folder or a junction/symlink WITHOUT touching the junction's target.
# (Remove-Item -Recurse on a junction can delete the target's contents in Windows PowerShell 5.1.)
function Remove-Folder([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $item = Get-Item -LiteralPath $Path -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($Path) }
  else { Remove-Item -LiteralPath $Path -Recurse -Force }
}

try {
  if (-not $DataDir) {
    if (-not $env:LOCALAPPDATA) { throw "LOCALAPPDATA is not set. Pass -DataDir <Mixxx data folder>." }
    $DataDir = Join-Path $env:LOCALAPPDATA "Mixxx"
  }
  $Repo    = Split-Path -Parent $PSScriptRoot
  $SkinSrc = Join-Path $Repo "skins\StudioDeck"
  $SkinDst = Join-Path $DataDir "skins\StudioDeck"
  $KbdSrc  = Join-Path $Repo "keyboard\Custom.kbd.cfg"
  $KbdDst  = Join-Path $DataDir "Custom.kbd.cfg"

  if (-not (Test-Path -LiteralPath (Join-Path $SkinSrc "skin.xml"))) {
    throw "$SkinSrc\skin.xml not found - is this a complete checkout of the repo?"
  }
  Write-Host "Mixxx data folder: $DataDir"
  if (-not (Test-Path -LiteralPath $DataDir)) {
    Write-Host "Note: that folder does not exist yet (Mixxx has not been started once?). It will be created." -ForegroundColor Yellow
  }

  # Controller mappings (controllers\*.xml, *.js) -> <data folder>\controllers
  $maps = Get-ChildItem (Join-Path $Repo "controllers") -Include *.xml,*.js -Recurse -ErrorAction SilentlyContinue
  foreach ($m in $maps) {
    $dst = Join-Path $DataDir "controllers"
    if ($Uninstall) { Remove-Item (Join-Path $dst $m.Name) -Force -ErrorAction SilentlyContinue }
    else { New-Item -ItemType Directory -Force -Path $dst | Out-Null; Copy-Item $m.FullName $dst -Force; Write-Host "Mapping: $($m.Name)" }
  }

  if ($Uninstall) {
    if (Test-Path -LiteralPath $SkinDst) { Remove-Folder $SkinDst; Write-Host "Skin removed." }
    if ((Test-Path -LiteralPath $KbdDst) -and ((Get-FileHash $KbdDst).Hash -eq (Get-FileHash $KbdSrc).Hash)) {
      Remove-Item $KbdDst -Force
      $bak = Get-ChildItem "$KbdDst.bak.*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
      if ($bak) { Move-Item $bak.FullName $KbdDst; Write-Host "Previous keyboard layout restored." }
      Write-Host "Keyboard layout removed."
    }
    exit 0
  }

  New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "skins") | Out-Null
  Remove-Folder $SkinDst
  $linked = $false
  if (-not $Copy) {
    try {
      New-Item -ItemType Junction -Path $SkinDst -Target $SkinSrc | Out-Null
      $linked = $true
      Write-Host "Skin linked: $SkinDst -> $SkinSrc"
    } catch {
      Write-Host "WARNING: could not create a junction ($($_.Exception.Message)). Copying the skin instead." -ForegroundColor Yellow
      Remove-Folder $SkinDst
    }
  }
  if (-not $linked) {
    Copy-Item -LiteralPath $SkinSrc -Destination $SkinDst -Recurse
    Write-Host "Skin copied: $SkinDst"
  }

  if (-not $NoKeyboard) {
    if ((Test-Path -LiteralPath $KbdDst) -and ((Get-FileHash $KbdDst).Hash -ne (Get-FileHash $KbdSrc).Hash)) {
      Copy-Item $KbdDst "$KbdDst.bak.$(Get-Date -Format yyyyMMdd-HHmmss)"
      Write-Host "Existing Custom.kbd.cfg backed up (.bak.*)"
    }
    Copy-Item $KbdSrc $KbdDst -Force; Write-Host "Keyboard layout: $KbdDst"
  }
  Write-Host "`nDone. In Mixxx: Preferences > Interface > Skin = StudioDeck, Color scheme = Studio."
  Write-Host "Restart Mixxx so the keyboard layout is loaded."
  Write-Host "Note: the skin is derived from Mixxx 2.5.x; older Mixxx versions may not list or load it."
}
catch {
  Write-Host ""
  Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
