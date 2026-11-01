// DJS Touch Panel - Mixxx controller script.
//
// GENERATED FILE: edit panel/mapping.template.js and panel/protocol.py, then run
//   python3 tools/make_panel.py
//
// The browser panel (panel/server.py) sends MIDI on channel 1; this script answers on channel 2.
// Every control comes from the protocol table below (see panel/protocol.py for the meaning of the kinds/modes).

var DJSPanel = {};

DJSPanel.PROTOCOL = [
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "play_indicator",
   "type": "led"
  },
  "id": "d1.play",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "play",
   "mode": "toggle"
  },
  "num": 0
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "cue_indicator",
   "type": "led"
  },
  "id": "d1.cue",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "cue_default",
   "mode": "hold"
  },
  "num": 1
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "sync_enabled",
   "type": "led"
  },
  "id": "d1.sync",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "sync_enabled",
   "mode": "toggle"
  },
  "num": 2
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "pfl",
   "type": "led"
  },
  "id": "d1.pfl",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "pfl",
   "mode": "toggle"
  },
  "num": 3
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "keylock",
   "type": "led"
  },
  "id": "d1.keylock",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "keylock",
   "mode": "toggle"
  },
  "num": 4
 },
 {
  "feedback": null,
  "id": "d1.load",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "LoadSelectedTrack",
   "mode": "hold"
  },
  "num": 5
 },
 {
  "feedback": null,
  "id": "d1.bend_down",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "rate_temp_down",
   "mode": "hold"
  },
  "num": 6
 },
 {
  "feedback": null,
  "id": "d1.bend_up",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "rate_temp_up",
   "mode": "hold"
  },
  "num": 7
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "hotcue_1_enabled",
   "type": "led"
  },
  "id": "d1.hotcue1",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "hotcue_1_activate",
   "mode": "hotcue",
   "n": 1
  },
  "num": 8
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "hotcue_2_enabled",
   "type": "led"
  },
  "id": "d1.hotcue2",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "hotcue_2_activate",
   "mode": "hotcue",
   "n": 2
  },
  "num": 9
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "hotcue_3_enabled",
   "type": "led"
  },
  "id": "d1.hotcue3",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "hotcue_3_activate",
   "mode": "hotcue",
   "n": 3
  },
  "num": 10
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "hotcue_4_enabled",
   "type": "led"
  },
  "id": "d1.hotcue4",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "hotcue_4_activate",
   "mode": "hotcue",
   "n": 4
  },
  "num": 11
 },
 {
  "feedback": null,
  "id": "d1.loop_in",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "loop_in",
   "mode": "hold"
  },
  "num": 12
 },
 {
  "feedback": null,
  "id": "d1.loop_out",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "loop_out",
   "mode": "hold"
  },
  "num": 13
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "loop_enabled",
   "type": "led"
  },
  "id": "d1.reloop",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "reloop_toggle",
   "mode": "hold"
  },
  "num": 14
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "beatloop_4_enabled",
   "type": "led"
  },
  "id": "d1.loop4",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "beatloop_4_toggle",
   "mode": "hold"
  },
  "num": 15
 },
 {
  "feedback": null,
  "id": "d1.loop_halve",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "loop_halve",
   "mode": "hold"
  },
  "num": 16
 },
 {
  "feedback": null,
  "id": "d1.loop_double",
  "kind": "button",
  "mixxx": {
   "group": "[Channel1]",
   "key": "loop_double",
   "mode": "hold"
  },
  "num": 17
 },
 {
  "feedback": null,
  "id": "d1.jog_touch",
  "kind": "button",
  "mixxx": {
   "deck": 1,
   "group": "[Channel1]",
   "key": "scratch2_enable",
   "mode": "scratch"
  },
  "num": 18
 },
 {
  "feedback": null,
  "id": "d1.jog",
  "kind": "rel",
  "mixxx": {
   "deck": 1,
   "group": "[Channel1]",
   "key": "scratch2",
   "mode": "scratch_tick"
  },
  "num": 64
 },
 {
  "feedback": null,
  "id": "d1.nudge",
  "kind": "rel",
  "mixxx": {
   "group": "[Channel1]",
   "key": "jog",
   "mode": "jog",
   "scale": 0.05
  },
  "num": 65
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "pregain",
   "type": "param7"
  },
  "id": "d1.gain",
  "kind": "abs7",
  "mixxx": {
   "group": "[Channel1]",
   "key": "pregain",
   "mode": "param"
  },
  "num": 66
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "volume",
   "type": "param7"
  },
  "id": "d1.vol",
  "kind": "abs7",
  "mixxx": {
   "group": "[Channel1]",
   "key": "volume",
   "mode": "param"
  },
  "num": 67
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter3",
   "type": "param7"
  },
  "id": "d1.eq_hi",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter3",
   "mode": "param"
  },
  "num": 68
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter2",
   "type": "param7"
  },
  "id": "d1.eq_mid",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter2",
   "mode": "param"
  },
  "num": 69
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter1",
   "type": "param7"
  },
  "id": "d1.eq_lo",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel1]_Effect1]",
   "key": "parameter1",
   "mode": "param"
  },
  "num": 70
 },
 {
  "feedback": {
   "group": "[QuickEffectRack1_[Channel1]]",
   "key": "super1",
   "type": "param7"
  },
  "id": "d1.filter",
  "kind": "abs7",
  "mixxx": {
   "group": "[QuickEffectRack1_[Channel1]]",
   "key": "super1",
   "mode": "param"
  },
  "num": 71
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "rate",
   "type": "param14"
  },
  "id": "d1.rate",
  "kind": "abs14",
  "mixxx": {
   "center_snap": true,
   "group": "[Channel1]",
   "key": "rate",
   "mode": "param"
  },
  "num": 0
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "VuMeter",
   "poll": true,
   "type": "param7"
  },
  "id": "d1.vu",
  "kind": "out7",
  "mixxx": null,
  "num": 72
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "playposition",
   "poll": true,
   "type": "param14"
  },
  "id": "d1.pos",
  "kind": "out14",
  "mixxx": null,
  "num": 1
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "bpm",
   "poll": true,
   "scale": 10,
   "type": "scaled14"
  },
  "id": "d1.bpm",
  "kind": "out14",
  "mixxx": null,
  "num": 2
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "duration",
   "scale": 1,
   "type": "scaled14"
  },
  "id": "d1.dur",
  "kind": "out14",
  "mixxx": null,
  "num": 3
 },
 {
  "feedback": {
   "group": "[Channel1]",
   "key": "track_loaded",
   "type": "led"
  },
  "id": "d1.loaded",
  "kind": "led",
  "mixxx": null,
  "num": 19
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "play_indicator",
   "type": "led"
  },
  "id": "d2.play",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "play",
   "mode": "toggle"
  },
  "num": 20
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "cue_indicator",
   "type": "led"
  },
  "id": "d2.cue",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "cue_default",
   "mode": "hold"
  },
  "num": 21
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "sync_enabled",
   "type": "led"
  },
  "id": "d2.sync",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "sync_enabled",
   "mode": "toggle"
  },
  "num": 22
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "pfl",
   "type": "led"
  },
  "id": "d2.pfl",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "pfl",
   "mode": "toggle"
  },
  "num": 23
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "keylock",
   "type": "led"
  },
  "id": "d2.keylock",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "keylock",
   "mode": "toggle"
  },
  "num": 24
 },
 {
  "feedback": null,
  "id": "d2.load",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "LoadSelectedTrack",
   "mode": "hold"
  },
  "num": 25
 },
 {
  "feedback": null,
  "id": "d2.bend_down",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "rate_temp_down",
   "mode": "hold"
  },
  "num": 26
 },
 {
  "feedback": null,
  "id": "d2.bend_up",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "rate_temp_up",
   "mode": "hold"
  },
  "num": 27
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "hotcue_1_enabled",
   "type": "led"
  },
  "id": "d2.hotcue1",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "hotcue_1_activate",
   "mode": "hotcue",
   "n": 1
  },
  "num": 28
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "hotcue_2_enabled",
   "type": "led"
  },
  "id": "d2.hotcue2",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "hotcue_2_activate",
   "mode": "hotcue",
   "n": 2
  },
  "num": 29
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "hotcue_3_enabled",
   "type": "led"
  },
  "id": "d2.hotcue3",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "hotcue_3_activate",
   "mode": "hotcue",
   "n": 3
  },
  "num": 30
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "hotcue_4_enabled",
   "type": "led"
  },
  "id": "d2.hotcue4",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "hotcue_4_activate",
   "mode": "hotcue",
   "n": 4
  },
  "num": 31
 },
 {
  "feedback": null,
  "id": "d2.loop_in",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "loop_in",
   "mode": "hold"
  },
  "num": 32
 },
 {
  "feedback": null,
  "id": "d2.loop_out",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "loop_out",
   "mode": "hold"
  },
  "num": 33
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "loop_enabled",
   "type": "led"
  },
  "id": "d2.reloop",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "reloop_toggle",
   "mode": "hold"
  },
  "num": 34
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "beatloop_4_enabled",
   "type": "led"
  },
  "id": "d2.loop4",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "beatloop_4_toggle",
   "mode": "hold"
  },
  "num": 35
 },
 {
  "feedback": null,
  "id": "d2.loop_halve",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "loop_halve",
   "mode": "hold"
  },
  "num": 36
 },
 {
  "feedback": null,
  "id": "d2.loop_double",
  "kind": "button",
  "mixxx": {
   "group": "[Channel2]",
   "key": "loop_double",
   "mode": "hold"
  },
  "num": 37
 },
 {
  "feedback": null,
  "id": "d2.jog_touch",
  "kind": "button",
  "mixxx": {
   "deck": 2,
   "group": "[Channel2]",
   "key": "scratch2_enable",
   "mode": "scratch"
  },
  "num": 38
 },
 {
  "feedback": null,
  "id": "d2.jog",
  "kind": "rel",
  "mixxx": {
   "deck": 2,
   "group": "[Channel2]",
   "key": "scratch2",
   "mode": "scratch_tick"
  },
  "num": 73
 },
 {
  "feedback": null,
  "id": "d2.nudge",
  "kind": "rel",
  "mixxx": {
   "group": "[Channel2]",
   "key": "jog",
   "mode": "jog",
   "scale": 0.05
  },
  "num": 74
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "pregain",
   "type": "param7"
  },
  "id": "d2.gain",
  "kind": "abs7",
  "mixxx": {
   "group": "[Channel2]",
   "key": "pregain",
   "mode": "param"
  },
  "num": 75
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "volume",
   "type": "param7"
  },
  "id": "d2.vol",
  "kind": "abs7",
  "mixxx": {
   "group": "[Channel2]",
   "key": "volume",
   "mode": "param"
  },
  "num": 76
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter3",
   "type": "param7"
  },
  "id": "d2.eq_hi",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter3",
   "mode": "param"
  },
  "num": 77
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter2",
   "type": "param7"
  },
  "id": "d2.eq_mid",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter2",
   "mode": "param"
  },
  "num": 78
 },
 {
  "feedback": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter1",
   "type": "param7"
  },
  "id": "d2.eq_lo",
  "kind": "abs7",
  "mixxx": {
   "group": "[EqualizerRack1_[Channel2]_Effect1]",
   "key": "parameter1",
   "mode": "param"
  },
  "num": 79
 },
 {
  "feedback": {
   "group": "[QuickEffectRack1_[Channel2]]",
   "key": "super1",
   "type": "param7"
  },
  "id": "d2.filter",
  "kind": "abs7",
  "mixxx": {
   "group": "[QuickEffectRack1_[Channel2]]",
   "key": "super1",
   "mode": "param"
  },
  "num": 80
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "rate",
   "type": "param14"
  },
  "id": "d2.rate",
  "kind": "abs14",
  "mixxx": {
   "center_snap": true,
   "group": "[Channel2]",
   "key": "rate",
   "mode": "param"
  },
  "num": 4
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "VuMeter",
   "poll": true,
   "type": "param7"
  },
  "id": "d2.vu",
  "kind": "out7",
  "mixxx": null,
  "num": 81
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "playposition",
   "poll": true,
   "type": "param14"
  },
  "id": "d2.pos",
  "kind": "out14",
  "mixxx": null,
  "num": 5
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "bpm",
   "poll": true,
   "scale": 10,
   "type": "scaled14"
  },
  "id": "d2.bpm",
  "kind": "out14",
  "mixxx": null,
  "num": 6
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "duration",
   "scale": 1,
   "type": "scaled14"
  },
  "id": "d2.dur",
  "kind": "out14",
  "mixxx": null,
  "num": 7
 },
 {
  "feedback": {
   "group": "[Channel2]",
   "key": "track_loaded",
   "type": "led"
  },
  "id": "d2.loaded",
  "kind": "led",
  "mixxx": null,
  "num": 39
 },
 {
  "feedback": {
   "group": "[Master]",
   "key": "crossfader",
   "type": "param7"
  },
  "id": "xfader",
  "kind": "abs7",
  "mixxx": {
   "group": "[Master]",
   "key": "crossfader",
   "mode": "param"
  },
  "num": 82
 },
 {
  "feedback": {
   "group": "[Master]",
   "key": "headMix",
   "type": "param7"
  },
  "id": "cue_mix",
  "kind": "abs7",
  "mixxx": {
   "group": "[Master]",
   "key": "headMix",
   "mode": "param"
  },
  "num": 83
 },
 {
  "feedback": {
   "group": "[Master]",
   "key": "headGain",
   "type": "param7"
  },
  "id": "head_gain",
  "kind": "abs7",
  "mixxx": {
   "group": "[Master]",
   "key": "headGain",
   "mode": "param"
  },
  "num": 84
 },
 {
  "feedback": {
   "group": "[Master]",
   "key": "gain",
   "type": "param7"
  },
  "id": "main_gain",
  "kind": "abs7",
  "mixxx": {
   "group": "[Master]",
   "key": "gain",
   "mode": "param"
  },
  "num": 85
 },
 {
  "feedback": null,
  "id": "lib",
  "kind": "rel",
  "mixxx": {
   "group": "[Library]",
   "key": "MoveVertical",
   "mode": "step_rel"
  },
  "num": 86
 },
 {
  "feedback": null,
  "id": "lib_up",
  "kind": "button",
  "mixxx": {
   "group": "[Library]",
   "key": "MoveVertical",
   "mode": "step",
   "step": -1
  },
  "num": 40
 },
 {
  "feedback": null,
  "id": "lib_down",
  "kind": "button",
  "mixxx": {
   "group": "[Library]",
   "key": "MoveVertical",
   "mode": "step",
   "step": 1
  },
  "num": 41
 },
 {
  "feedback": {
   "group": "[AutoDJ]",
   "key": "enabled",
   "type": "led"
  },
  "id": "autodj",
  "kind": "button",
  "mixxx": {
   "group": "[AutoDJ]",
   "key": "enabled",
   "mode": "toggle"
  },
  "num": 42
 },
 {
  "feedback": null,
  "id": "autodj_fade",
  "kind": "button",
  "mixxx": {
   "group": "[AutoDJ]",
   "key": "fade_now",
   "mode": "hold"
  },
  "num": 43
 },
 {
  "feedback": null,
  "id": "autodj_skip",
  "kind": "button",
  "mixxx": {
   "group": "[AutoDJ]",
   "key": "skip_next",
   "mode": "hold"
  },
  "num": 44
 },
 {
  "feedback": null,
  "id": "shift",
  "kind": "button",
  "mixxx": {
   "group": "[Master]",
   "key": "shift",
   "mode": "shift"
  },
  "num": 45
 },
 {
  "feedback": null,
  "id": "request",
  "kind": "button",
  "mixxx": {
   "group": "[Master]",
   "key": "request",
   "mode": "request"
  },
  "num": 127
 }
];
DJSPanel.NOTE_ON_IN = 144;   // 0x90
DJSPanel.CC_IN = 176;        // 0xB0
DJSPanel.NOTE_ON_OUT = 145;  // 0x91
DJSPanel.CC_OUT = 177;       // 0xB1
DJSPanel.JOG_TICKS_PER_REV = 1024;


DJSPanel.shift = false;
DJSPanel.debug = false;
DJSPanel.msb = {};          // last MSB per 14-bit control id
DJSPanel.held = {};         // action that is "held down" per control id (hotcues)
DJSPanel.lastSent = {};     // last raw value per polled feedback control
DJSPanel.connections = [];
DJSPanel.pollList = [];
DJSPanel.timer = 0;
DJSPanel.byIn = {};         // "status:number" -> {c: control, part: "msb"|"lsb"|""}

DJSPanel.log = function(msg) {
    if (DJSPanel.debug) {
        engine.log("DJSPanel: " + msg);
    }
};

DJSPanel.clamp = function(x, lo, hi) {
    return Math.min(hi, Math.max(lo, x));
};

DJSPanel.init = function(id, debugging) {
    DJSPanel.debug = !!debugging;
    DJSPanel.shift = false;
    DJSPanel.msb = {};
    DJSPanel.held = {};
    DJSPanel.lastSent = {};
    DJSPanel.connections = [];
    DJSPanel.pollList = [];
    DJSPanel.byIn = {};

    DJSPanel.PROTOCOL.forEach(function(c) {
        if (c.kind === "button") {
            DJSPanel.byIn[DJSPanel.NOTE_ON_IN + ":" + c.num] = {c: c, part: ""};
        } else if (c.kind === "abs7" || c.kind === "rel") {
            DJSPanel.byIn[DJSPanel.CC_IN + ":" + c.num] = {c: c, part: ""};
        } else if (c.kind === "abs14") {
            DJSPanel.byIn[DJSPanel.CC_IN + ":" + c.num] = {c: c, part: "msb"};
            DJSPanel.byIn[DJSPanel.CC_IN + ":" + (c.num + 32)] = {c: c, part: "lsb"};
        }
        var fb = c.feedback;
        if (!fb) {
            return;
        }
        if (fb.poll) {
            DJSPanel.pollList.push(c);
        } else {
            var conn = engine.makeConnection(fb.group, fb.key, function() {
                DJSPanel.sendFeedback(c, true);
            });
            DJSPanel.connections.push(conn);
        }
    });

    DJSPanel.timer = engine.beginTimer(40, DJSPanel.poll);
    DJSPanel.resendAll();
    DJSPanel.log("initialized, " + DJSPanel.PROTOCOL.length + " controls");
};

DJSPanel.shutdown = function() {
    if (DJSPanel.timer) {
        engine.stopTimer(DJSPanel.timer);
        DJSPanel.timer = 0;
    }
    DJSPanel.connections.forEach(function(conn) {
        if (conn && conn.disconnect) {
            conn.disconnect();
        }
    });
    DJSPanel.connections = [];
    // make sure no deck stays in scratch mode
    [1, 2].forEach(function(deck) {
        if (engine.isScratching(deck)) {
            engine.scratchDisable(deck, false);
        }
    });
};

// ---------------------------------------------------------------- panel -> Mixxx

// Every mapped MIDI message of the panel ends up here (see the generated XML).
DJSPanel.input = function(channel, control, value, status, group) {
    var hit = DJSPanel.byIn[status + ":" + control];
    if (!hit) {
        return;
    }
    var c = hit.c;
    switch (c.kind) {
    case "button":
        DJSPanel.button(c, value > 0);
        break;
    case "abs7":
        engine.setParameter(c.mixxx.group, c.mixxx.key, value / 127);
        break;
    case "abs14":
        DJSPanel.abs14(c, hit.part, value);
        break;
    case "rel":
        DJSPanel.relative(c, value - 64);
        break;
    }
};

DJSPanel.button = function(c, pressed) {
    var m = c.mixxx;
    switch (m.mode) {
    case "hold":
        engine.setValue(m.group, m.key, pressed ? 1 : 0);
        break;
    case "toggle":
        if (pressed) {
            script.toggleControl(m.group, m.key);
        }
        break;
    case "step":
        if (pressed) {
            engine.setValue(m.group, m.key, m.step);
        }
        break;
    case "hotcue":
        if (pressed) {
            var action = DJSPanel.shift ? "hotcue_" + m.n + "_clear" : "hotcue_" + m.n + "_activate";
            DJSPanel.held[c.id] = action;
            engine.setValue(m.group, action, 1);
        } else if (DJSPanel.held[c.id]) {
            engine.setValue(m.group, DJSPanel.held[c.id], 0);
            delete DJSPanel.held[c.id];
        }
        break;
    case "shift":
        DJSPanel.shift = pressed;
        break;
    case "scratch":
        if (pressed) {
            engine.scratchEnable(m.deck, DJSPanel.JOG_TICKS_PER_REV, 33 + 1 / 3, 1 / 8, (1 / 8) / 32);
        } else {
            engine.scratchDisable(m.deck);
        }
        break;
    case "request":
        if (pressed) {
            DJSPanel.resendAll();
        }
        break;
    }
};

DJSPanel.abs14 = function(c, part, value) {
    if (part === "msb") {
        DJSPanel.msb[c.id] = value;
        return;
    }
    var raw = ((DJSPanel.msb[c.id] || 0) << 7) | value;
    var param = DJSPanel.clamp(raw / 16383, 0, 1);
    if (c.mixxx.center_snap && Math.abs(param - 0.5) < 0.0008) {
        param = 0.5;    // exact pitch center: 0.00 %
    }
    engine.setParameter(c.mixxx.group, c.mixxx.key, param);
};

DJSPanel.relative = function(c, delta) {
    if (delta === 0) {
        return;
    }
    var m = c.mixxx;
    switch (m.mode) {
    case "scratch_tick":
        if (engine.isScratching(m.deck)) {
            engine.scratchTick(m.deck, delta);
        }
        break;
    case "jog":
        engine.setValue(m.group, m.key, delta * m.scale);
        break;
    case "step_rel":
        engine.setValue(m.group, m.key, delta);
        break;
    }
};

// ---------------------------------------------------------------- Mixxx -> panel

DJSPanel.sendFeedback = function(c, force) {
    var fb = c.feedback;
    var raw;
    switch (fb.type) {
    case "led":
        raw = engine.getValue(fb.group, fb.key) ? 127 : 0;
        break;
    case "param7":
        raw = Math.round(DJSPanel.clamp(engine.getParameter(fb.group, fb.key), 0, 1) * 127);
        break;
    case "param14":
        raw = Math.round(DJSPanel.clamp(engine.getParameter(fb.group, fb.key), 0, 1) * 16383);
        break;
    case "scaled14":
        raw = Math.round(DJSPanel.clamp(engine.getValue(fb.group, fb.key) * fb.scale, 0, 16383));
        break;
    default:
        return;
    }
    if (!force && DJSPanel.lastSent[c.id] === raw) {
        return;
    }
    DJSPanel.lastSent[c.id] = raw;
    if (fb.type === "led") {
        midi.sendShortMsg(DJSPanel.NOTE_ON_OUT, c.num, raw);
    } else if (fb.type === "param7") {
        midi.sendShortMsg(DJSPanel.CC_OUT, c.num, raw);
    } else {
        midi.sendShortMsg(DJSPanel.CC_OUT, c.num, raw >> 7);
        midi.sendShortMsg(DJSPanel.CC_OUT, c.num + 32, raw & 0x7F);
    }
};

DJSPanel.poll = function() {
    DJSPanel.pollList.forEach(function(c) {
        DJSPanel.sendFeedback(c, false);
    });
};

DJSPanel.resendAll = function() {
    DJSPanel.PROTOCOL.forEach(function(c) {
        if (c.feedback) {
            DJSPanel.sendFeedback(c, true);
        }
    });
};

if (typeof module !== "undefined") {
    module.exports = DJSPanel;   // for tests/panel_mapping.test.js (Mixxx has no "module")
}
