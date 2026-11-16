"""Single source of truth of the DJS touch panel protocol.

The panel (browser UI) talks to Mixxx through MIDI. This file defines every control once:
which MIDI message it uses and which Mixxx control it drives / mirrors. From it are generated
  * controllers/DJS-Touch-Panel.midi.xml + DJS-Touch-Panel-scripts.js   (tools/make_panel.py)
and it is imported by panel/server.py. tests/ check that the UI uses exactly these ids.

MIDI channels (so that a loopback port never feeds Mixxx its own feedback):
  panel -> Mixxx : channel 1  (status 0x90 notes, 0xB0 control change)
  Mixxx -> panel : channel 2  (status 0x91 notes, 0xB1 control change)

Control kinds (what the UI / server sends or receives as value):
  button  note        127 = pressed, 0 = released                      (panel -> Mixxx, optional LED back)
  abs7    cc          0..127                                           (both directions)
  abs14   cc + cc+32  0..16383, MSB first, then LSB                    (both directions)
  rel     cc          64 + delta (delta -63..63)                       (panel -> Mixxx)
  led     note        127 / 0                                          (Mixxx -> panel)
  out7    cc          0..127 readout (level meter)                     (Mixxx -> panel)
  out14   cc + cc+32  0..16383 readout (position, bpm x10, seconds)    (Mixxx -> panel)

Button modes (what Mixxx does):
  hold      control = 1 while pressed, 0 when released
  toggle    on press the control is toggled
  step      on press the control is set to `step` (relative library controls)
  hotcue    press = activate hotcue N, or clear it while "shift" is on
  shift     remembers the shift state (global modifier of the panel)
  scratch   finger on the jog platter: scratch mode on / off
  request   panel asks Mixxx to resend all feedback values
"""

DECKS = (1, 2)
IN_CH = 0    # panel -> Mixxx (MIDI channel 1)
OUT_CH = 1   # Mixxx -> panel (MIDI channel 2)
REQUEST_NOTE = 127
NOTE_ON_IN, CC_IN = 0x90 | IN_CH, 0xB0 | IN_CH
NOTE_ON_OUT, CC_OUT = 0x90 | OUT_CH, 0xB0 | OUT_CH
BPM_SCALE = 10          # bpm is sent as bpm * 10 (14 bit -> up to 1638.3 bpm)
JOG_TICKS_PER_REV = 1024

# Numeric constants shared by the server, the Mixxx script (generated) and the browser UI (/protocol.json).
# They are defined here ONLY; no other file may hard-code them (tests/test_panel.py checks index.html).
MAX7 = 127              # full scale of a 7 bit value; also "pressed" / "LED on"
MAX14 = 16383           # full scale of a 14 bit value (MSB << 7 | LSB)
REL_CENTER = 64         # relative controls: 64 + delta
REL_MAX = 63            # largest |delta| of one relative message
CENTER7 = 64            # resting position of a centred 7 bit knob (EQ, filter, crossfader)
CENTER14 = 8192         # resting position of the 14 bit pitch fader (0.00 %)
SCRATCH_RPM = 100 / 3   # the virtual platter turns like a record: 33 1/3 rpm
SECONDS_PER_REV = round(60 / SCRATCH_RPM, 6)   # = 1.8 s, used to turn the jog mark with the playposition
JOG_RING_DIVISOR = 6    # the outer jog ring (nudge) is this many times less sensitive than the platter


def ui_constants():
    """What the browser UI needs to know (served as /protocol.json)."""
    return {
        "max7": MAX7, "max14": MAX14, "rel_max": REL_MAX, "center7": CENTER7, "center14": CENTER14,
        "jog_ticks_per_rev": JOG_TICKS_PER_REV, "jog_ring_divisor": JOG_RING_DIVISOR,
        "bpm_scale": BPM_SCALE, "seconds_per_rev": SECONDS_PER_REV,
    }


class _Alloc:
    """Hands out unique MIDI numbers: notes 0..126, MSB cc 0..31 (LSB = +32), single cc 64..127."""

    def __init__(self):
        self.note, self.cc14, self.cc7 = 0, 0, 64

    def take_note(self):
        n = self.note
        self.note += 1
        assert n < REQUEST_NOTE, "out of MIDI notes"
        return n

    def take_cc14(self):
        n = self.cc14
        self.cc14 += 1
        assert n < 32, "out of 14-bit controllers"
        return n

    def take_cc7(self):
        n = self.cc7
        self.cc7 += 1
        assert n < 128, "out of 7-bit controllers"
        return n


def _build():
    a = _Alloc()
    out = []

    def add(cid, kind, num, mixxx=None, feedback=None):
        out.append({"id": cid, "kind": kind, "num": num, "mixxx": mixxx, "feedback": feedback})

    def button(cid, group, key, mode="hold", led=None, **extra):
        mixxx = {"group": group, "key": key, "mode": mode}
        mixxx.update(extra)
        fb = {"group": group, "key": led, "type": "led"} if led else None
        add(cid, "button", a.take_note(), mixxx, fb)

    for d in DECKS:
        g, p = f"[Channel{d}]", f"d{d}."
        # transport
        button(p + "play", g, "play", "toggle", led="play_indicator")
        button(p + "cue", g, "cue_default", "hold", led="cue_indicator")
        button(p + "sync", g, "sync_enabled", "toggle", led="sync_enabled")
        button(p + "pfl", g, "pfl", "toggle", led="pfl")
        button(p + "keylock", g, "keylock", "toggle", led="keylock")
        button(p + "load", g, "LoadSelectedTrack", "hold")
        button(p + "bend_down", g, "rate_temp_down", "hold")
        button(p + "bend_up", g, "rate_temp_up", "hold")
        # hotcues (shift + hotcue = delete it)
        for n in range(1, 5):
            button(p + f"hotcue{n}", g, f"hotcue_{n}_activate", "hotcue", led=f"hotcue_{n}_enabled", n=n)
        # loops
        button(p + "loop_in", g, "loop_in", "hold")
        button(p + "loop_out", g, "loop_out", "hold")
        button(p + "reloop", g, "reloop_toggle", "hold", led="loop_enabled")
        button(p + "loop4", g, "beatloop_4_toggle", "hold", led="beatloop_4_enabled")
        button(p + "loop_halve", g, "loop_halve", "hold")
        button(p + "loop_double", g, "loop_double", "hold")
        # jog: platter touch = scratch, platter drag = scratch ticks, ring drag = nudge
        button(p + "jog_touch", g, "scratch2_enable", "scratch", deck=d)
        add(p + "jog", "rel", a.take_cc7(), {"group": g, "key": "scratch2", "mode": "scratch_tick", "deck": d})
        add(p + "nudge", "rel", a.take_cc7(), {"group": g, "key": "jog", "mode": "jog", "scale": 0.05})
        # faders / knobs (both directions: the panel follows what happens in Mixxx)
        for cid, key, grp in (
            ("gain", "pregain", g),
            ("vol", "volume", g),
            ("eq_hi", "parameter3", f"[EqualizerRack1_[Channel{d}]_Effect1]"),
            ("eq_mid", "parameter2", f"[EqualizerRack1_[Channel{d}]_Effect1]"),
            ("eq_lo", "parameter1", f"[EqualizerRack1_[Channel{d}]_Effect1]"),
            ("filter", "super1", f"[QuickEffectRack1_[Channel{d}]]"),
        ):
            add(p + cid, "abs7", a.take_cc7(), {"group": grp, "key": key, "mode": "param"},
                {"group": grp, "key": key, "type": "param7"})
        add(p + "rate", "abs14", a.take_cc14(), {"group": g, "key": "rate", "mode": "param", "center_snap": True},
            {"group": g, "key": "rate", "type": "param14"})
        # read-outs (Mixxx -> panel)
        add(p + "vu", "out7", a.take_cc7(), None, {"group": g, "key": "VuMeter", "type": "param7", "poll": True})
        add(p + "pos", "out14", a.take_cc14(), None, {"group": g, "key": "playposition", "type": "param14", "poll": True})
        add(p + "bpm", "out14", a.take_cc14(), None,
            {"group": g, "key": "bpm", "type": "scaled14", "scale": BPM_SCALE, "poll": True})
        add(p + "dur", "out14", a.take_cc14(), None, {"group": g, "key": "duration", "type": "scaled14", "scale": 1})
        out.append({"id": p + "loaded", "kind": "led", "num": a.take_note(), "mixxx": None,
                    "feedback": {"group": g, "key": "track_loaded", "type": "led"}})

    # master section
    for cid, key in (("xfader", "crossfader"), ("cue_mix", "headMix"), ("head_gain", "headGain"),
                     ("main_gain", "gain")):
        add(cid, "abs7", a.take_cc7(), {"group": "[Master]", "key": key, "mode": "param"},
            {"group": "[Master]", "key": key, "type": "param7"})

    # library / auto DJ
    add("lib", "rel", a.take_cc7(), {"group": "[Library]", "key": "MoveVertical", "mode": "step_rel"})
    button("lib_up", "[Library]", "MoveVertical", "step", step=-1)
    button("lib_down", "[Library]", "MoveVertical", "step", step=1)
    button("autodj", "[AutoDJ]", "enabled", "toggle", led="enabled")
    button("autodj_fade", "[AutoDJ]", "fade_now", "hold")
    button("autodj_skip", "[AutoDJ]", "skip_next", "hold")

    # panel itself
    add("shift", "button", a.take_note(), {"group": "[Master]", "key": "shift", "mode": "shift"})
    add("request", "button", REQUEST_NOTE, {"group": "[Master]", "key": "request", "mode": "request"})
    return out


CONTROLS = _build()
BY_ID = {c["id"]: c for c in CONTROLS}


def midi_in_status(c):
    """Status byte the panel uses to send this control to Mixxx (None: not an input)."""
    if c["kind"] in ("button",):
        return NOTE_ON_IN
    if c["kind"] in ("abs7", "abs14", "rel"):
        return CC_IN
    return None


def midi_out_status(c):
    """Status byte Mixxx uses to send feedback for this control (None: no feedback)."""
    if c["kind"] in ("led",) or (c["kind"] == "button" and c.get("feedback")):
        return NOTE_ON_OUT
    if c["kind"] in ("abs7", "abs14", "out7", "out14") and c.get("feedback"):
        return CC_OUT
    return None


def is_14bit(c):
    return c["kind"] in ("abs14", "out14")
