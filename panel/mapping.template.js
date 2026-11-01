// DJS Touch Panel - Mixxx controller script.
//
// GENERATED FILE: edit panel/mapping.template.js and panel/protocol.py, then run
//   python3 tools/make_panel.py
//
// The browser panel (panel/server.py) sends MIDI on channel 1; this script answers on channel 2.
// Every control comes from the protocol table below (see panel/protocol.py for the meaning of the kinds/modes).

var DJSPanel = {};

DJSPanel.PROTOCOL = /*@PROTOCOL@*/ [];
/*@CONSTANTS@*/

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
