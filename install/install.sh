#!/usr/bin/env bash
# Installs the StudioDeck skin and (optionally) the keyboard layout for Mixxx on Linux/macOS.
#
#   bash install/install.sh              Link the skin (symlink -> changes in the repo take effect immediately)
#   bash install/install.sh --copy       Copy the skin instead of linking (automatic for Flatpak)
#   bash install/install.sh --no-keyboard   Leave the keyboard layout alone
#   bash install/install.sh --data-dir D    Set the Mixxx data folder manually
#   bash install/install.sh --uninstall  Remove everything (an existing keyboard layout backup is restored)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="link"; KEYBOARD=1; UNINSTALL=0; DATA=""
usage() { awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "${BASH_SOURCE[0]}"; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy) MODE=copy ;;
    --no-keyboard) KEYBOARD=0 ;;
    --uninstall) UNINSTALL=1 ;;
    --data-dir) DATA="${2:?Path missing}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac; shift
done

FLATPAK=0
detect_data_dir() {
  if [[ "$(uname)" == "Darwin" ]]; then
    echo "$HOME/Library/Containers/org.mixxx.mixxx/Data/Library/Application Support/Mixxx"
  elif [[ -d "$HOME/.var/app/org.mixxx.Mixxx/data/mixxx" && ! -d "$HOME/.mixxx" ]]; then
    FLATPAK=1
    echo "$HOME/.var/app/org.mixxx.Mixxx/data/mixxx"          # Flatpak
  else
    echo "$HOME/.mixxx"
  fi
}
DATA="${DATA:-$(detect_data_dir)}"
# The Flatpak sandbox cannot follow a symlink that points outside its own data folder.
if [[ "$DATA" == *"/.var/app/org.mixxx.Mixxx/"* ]]; then FLATPAK=1; fi
if [[ $FLATPAK -eq 1 && "$MODE" == link ]]; then MODE=copy; echo "Flatpak detected: copying the skin instead of linking it."; fi

SKIN_SRC="$REPO/skins/StudioDeck"; SKIN_DST="$DATA/skins/StudioDeck"
KBD_SRC="$REPO/keyboard/Custom.kbd.cfg"; KBD_DST="$DATA/Custom.kbd.cfg"

if [[ ! -f "$SKIN_SRC/skin.xml" ]]; then
  echo "ERROR: $SKIN_SRC/skin.xml not found - is this a complete checkout of the repo?" >&2; exit 1
fi
echo "Mixxx data folder: $DATA"

# Controller mappings (controllers/*.xml, *.js) -> <data folder>/controllers/
for f in "$REPO"/controllers/*.xml "$REPO"/controllers/*.js; do
  [[ -e "$f" ]] || continue
  if [[ $UNINSTALL -eq 1 ]]; then rm -f "$DATA/controllers/$(basename "$f")"
  else mkdir -p "$DATA/controllers"; cp "$f" "$DATA/controllers/"; echo "Mapping: $(basename "$f")"; fi
done

if [[ $UNINSTALL -eq 1 ]]; then
  rm -rf "$SKIN_DST" && echo "Skin removed: $SKIN_DST"
  if [[ -f "$KBD_DST" ]] && cmp -s "$KBD_SRC" "$KBD_DST"; then
    rm -f "$KBD_DST"
    latest=""
    for b in "$KBD_DST".bak.*; do [[ -e "$b" ]] && latest="$b"; done   # timestamps in the name sort alphabetically
    if [[ -n "$latest" ]]; then mv "$latest" "$KBD_DST" && echo "Previous keyboard layout restored."; fi
    echo "Keyboard layout removed."
  fi
  exit 0
fi

mkdir -p "$DATA/skins"
rm -rf "$SKIN_DST"      # removes only the link if it is a symlink
if [[ "$MODE" == link ]]; then ln -s "$SKIN_SRC" "$SKIN_DST"; echo "Skin linked:  $SKIN_DST -> $SKIN_SRC"
else cp -r "$SKIN_SRC" "$SKIN_DST"; echo "Skin copied:   $SKIN_DST"; fi

if [[ $KEYBOARD -eq 1 ]]; then
  if [[ -f "$KBD_DST" ]] && ! cmp -s "$KBD_SRC" "$KBD_DST"; then
    cp "$KBD_DST" "$KBD_DST.bak.$(date +%Y%m%d-%H%M%S)"; echo "Existing Custom.kbd.cfg backed up (.bak.*)"
  fi
  cp "$KBD_SRC" "$KBD_DST"; echo "Keyboard layout: $KBD_DST"
fi

cat <<MSG

Done. In Mixxx: Preferences > Interface > Skin = StudioDeck, Color scheme = Studio.
Restart Mixxx so the keyboard layout is loaded. To reload skin changes from the repo use
Ctrl+Shift+R (developer mode only: mixxx --developer).
Note: the skin is derived from Mixxx 2.5.x. Older Mixxx versions (e.g. 2.4.0 from the Ubuntu 24.04
repositories) may not list or load it - check with: mixxx --version
MSG
