#!/usr/bin/env bash
# dj-stream.sh - virtual "DJ-Stream" audio device for Mixxx (PulseAudio / PipeWire-pulse)
#
# Idea: Spotify / the browser (SoundCloud) do NOT play to the speakers but into a
# virtual device. Mixxx reads its monitor as an Auxiliary input and mixes it
# through master/headphone cue. You then only hear the stream through the Mixxx mixer.
#
#   ./dj-stream.sh up                 Create the virtual device
#   ./dj-stream.sh down               Remove it again
#   ./dj-stream.sh status             Show the device + currently playing streams
#   ./dj-stream.sh move spotify       Redirect all streams whose app name matches "spotify"
#   ./dj-stream.sh move "firefox|chrom"   (regex, case-insensitive)
#   ./dj-stream.sh back               Move all redirected streams back to the default output
#
# Then in Mixxx: Preferences > Sound Hardware > Input > Auxiliary 1 = device
# "pulse"/"pipewire", channels 1-2. In pavucontrol (tab "Recording") set the source
# for Mixxx to "Monitor of DJ-Stream".
set -euo pipefail

SINK="${DJ_STREAM_SINK:-dj_stream}"
DESC="${DJ_STREAM_DESC:-DJ-Stream}"
STATE="${XDG_RUNTIME_DIR:-/tmp}/dj-stream.module"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 (pactl: package pulseaudio-utils or pipewire-pulse)" >&2; exit 1; }; }
need pactl

sink_exists() { pactl list short sinks | awk '{print $2}' | grep -qx "$SINK"; }

# Prints "index<TAB>application name" for all playback streams
streams() {
  pactl list sink-inputs | awk '
    /^Sink Input #/ { idx=substr($3,2) }
    /application.name = / { n=$0; sub(/.*application.name = "/,"",n); sub(/"$/,"",n); print idx "\t" n }'
}

cmd_up() {
  if sink_exists; then echo "$SINK already exists."; return; fi
  mod=$(pactl load-module module-null-sink "sink_name=$SINK" "sink_properties=device.description=$DESC")
  echo "$mod" > "$STATE"
  echo "Created: sink '$SINK' (module $mod). Monitor source: ${SINK}.monitor"
}

cmd_down() {
  if [[ -f "$STATE" ]]; then pactl unload-module "$(cat "$STATE")" && rm -f "$STATE"
  elif sink_exists; then echo "Sink exists, but the module ID is unknown - pactl list modules short | grep null-sink" >&2; exit 1
  fi
  echo "Removed."
}

cmd_status() {
  if sink_exists; then echo "Sink: $SINK  OK"; else echo "Sink: $SINK  missing (./dj-stream.sh up)"; fi
  echo "Playback streams:"; streams | sed 's/^/  #/'
}

cmd_move() {
  local pat="${1:?Pattern missing, e.g.: move spotify}"
  sink_exists || { echo "Run './dj-stream.sh up' first." >&2; exit 1; }
  local n=0
  while IFS=$'\t' read -r idx name; do
    if [[ "${name,,}" =~ ${pat,,} ]]; then
      pactl move-sink-input "$idx" "$SINK" && echo "-> #$idx ($name) to $SINK" && n=$((n+1))
    fi
  done < <(streams)
  [[ $n -gt 0 ]] || echo "No matching stream. Is the app running and currently playing audio? (status shows the list)"
}

cmd_back() {
  local def; def=$(pactl get-default-sink)
  while IFS=$'\t' read -r idx name; do
    pactl move-sink-input "$idx" "$def" 2>/dev/null && echo "-> #$idx ($name) back to $def" || true
  done < <(streams)
}

usage() { awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "$0"; }

case "${1:-}" in
  up) cmd_up ;;
  down) cmd_down ;;
  status) cmd_status ;;
  move) shift; cmd_move "$@" ;;
  back) cmd_back ;;
  *) usage; exit 1 ;;
esac
