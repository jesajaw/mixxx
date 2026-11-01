// Tests of controllers/DJS-Touch-Panel-scripts.js against a mock of Mixxx's scripting API.
//   node tests/panel_mapping.test.js
// (Mixxx itself is not needed; this checks the logic, not that Mixxx accepts the file.)
"use strict";
const assert = require("assert");
const path = require("path");

const state = {};
function reset() {
    state.values = {};
    state.params = {};
    state.sent = [];
    state.calls = [];
    state.connections = [];
    state.timers = {};
    state.scratching = {};
    state.nextTimer = 1;
}
const key = (g, k) => g + "|" + k;

global.engine = {
    log: () => {},
    getValue: (g, k) => state.values[key(g, k)] || 0,
    setValue: (g, k, v) => { state.values[key(g, k)] = v; state.calls.push(["setValue", g, k, v]); },
    getParameter: (g, k) => state.params[key(g, k)] || 0,
    setParameter: (g, k, v) => { state.params[key(g, k)] = v; state.calls.push(["setParameter", g, k, v]); },
    makeConnection: (g, k, cb) => {
        const conn = {g, k, cb, disconnected: false, disconnect() { this.disconnected = true; }};
        state.connections.push(conn);
        return conn;
    },
    beginTimer: (ms, fn) => { const id = state.nextTimer++; state.timers[id] = {ms, fn}; return id; },
    stopTimer: (id) => { delete state.timers[id]; },
    scratchEnable: (d, ...a) => { state.scratching[d] = true; state.calls.push(["scratchEnable", d, ...a]); },
    scratchDisable: (d) => { state.scratching[d] = false; state.calls.push(["scratchDisable", d]); },
    scratchTick: (d, n) => state.calls.push(["scratchTick", d, n]),
    isScratching: (d) => !!state.scratching[d],
};
global.midi = { sendShortMsg: (s, a, b) => state.sent.push([s, a, b]) };
global.script = {
    toggleControl: (g, k) => {
        state.values[key(g, k)] = state.values[key(g, k)] ? 0 : 1;
        state.calls.push(["toggle", g, k]);
    },
};

const P = require(path.join(__dirname, "..", "controllers", "DJS-Touch-Panel-scripts.js"));
const byId = (id) => P.PROTOCOL.find((c) => c.id === id);
const press = (id, down = true) => { const c = byId(id); P.input(0, c.num, down ? 127 : 0, P.NOTE_ON_IN, c.mixxx.group); };
const cc = (id, v, add = 0) => { const c = byId(id); P.input(0, c.num + add, v, P.CC_IN, c.mixxx.group); };
const last = () => state.calls[state.calls.length - 1];

let n = 0;
function test(name, fn) {
    reset();
    P.init("DJSPanel", false);
    state.calls.length = 0;
    state.sent.length = 0;
    try { fn(); n++; console.log("ok   " + name); }
    catch (e) { console.log("FAIL " + name + "\n" + e.stack); process.exitCode = 1; }
    P.shutdown();
}

test("init: connects every non-polled feedback control, polls the others, answers with all values", () => {
    reset();
    P.init("DJSPanel", false);
    const withFb = P.PROTOCOL.filter((c) => c.feedback);
    const polled = withFb.filter((c) => c.feedback.poll);
    assert.strictEqual(state.connections.length, withFb.length - polled.length);
    assert.strictEqual(Object.keys(state.timers).length, 1);
    assert.strictEqual(state.sent.length > withFb.length, true);   // 14-bit controls send two messages
    P.shutdown();
});

test("hold button: 1 while pressed, 0 on release", () => {
    press("d1.cue"); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "cue_default", 1]);
    press("d1.cue", false); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "cue_default", 0]);
});

test("toggle button toggles on press only", () => {
    press("d2.play"); press("d2.play", false);
    assert.strictEqual(state.calls.filter((c) => c[0] === "toggle").length, 1);
    assert.strictEqual(engine.getValue("[Channel2]", "play"), 1);
    press("d2.play"); assert.strictEqual(engine.getValue("[Channel2]", "play"), 0);
});

test("hotcue activates; with shift it clears; release undoes what the press did", () => {
    press("d1.hotcue3"); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "hotcue_3_activate", 1]);
    press("shift");                                   // shift pressed while the cue is still held
    press("d1.hotcue3", false); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "hotcue_3_activate", 0]);
    press("d1.hotcue2"); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "hotcue_2_clear", 1]);
    press("d1.hotcue2", false); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "hotcue_2_clear", 0]);
    press("shift", false);
    press("d1.hotcue2"); assert.deepStrictEqual(last(), ["setValue", "[Channel1]", "hotcue_2_activate", 1]);
});

test("7-bit controls use the normalized parameter", () => {
    cc("xfader", 127); assert.deepStrictEqual(last(), ["setParameter", "[Master]", "crossfader", 1]);
    cc("d1.eq_lo", 0); assert.deepStrictEqual(last(), ["setParameter", "[EqualizerRack1_[Channel1]_Effect1]", "parameter1", 0]);
    cc("d2.filter", 64);
    assert.ok(Math.abs(last()[3] - 64 / 127) < 1e-9);
    assert.strictEqual(last()[1], "[QuickEffectRack1_[Channel2]]");
});

test("14-bit rate: MSB then LSB; center snaps to exactly 0.5; extremes reach 0 and 1", () => {
    cc("d1.rate", 64); assert.strictEqual(state.calls.length, 0);           // MSB alone does nothing
    cc("d1.rate", 0, 32); assert.deepStrictEqual(last(), ["setParameter", "[Channel1]", "rate", 0.5]);
    cc("d1.rate", 127); cc("d1.rate", 127, 32); assert.strictEqual(last()[3], 1);
    cc("d1.rate", 0); cc("d1.rate", 0, 32); assert.strictEqual(last()[3], 0);
    cc("d1.rate", 70); cc("d1.rate", 5, 32);
    assert.ok(Math.abs(last()[3] - ((70 << 7) | 5) / 16383) < 1e-12);
});

test("jog: scratch only while the platter is touched; ring nudges", () => {
    cc("d1.jog", 64 + 5); assert.strictEqual(state.calls.length, 0);        // not touching: ignored
    press("d1.jog_touch");
    assert.strictEqual(last()[0], "scratchEnable");
    assert.strictEqual(last()[2], 1024);
    cc("d1.jog", 64 - 7); assert.deepStrictEqual(last(), ["scratchTick", 1, -7]);
    cc("d1.jog", 64); assert.deepStrictEqual(last(), ["scratchTick", 1, -7]);   // delta 0: nothing new
    press("d1.jog_touch", false); assert.deepStrictEqual(last(), ["scratchDisable", 1]);
    cc("d2.nudge", 64 + 10);
    assert.deepStrictEqual(last().slice(0, 3), ["setValue", "[Channel2]", "jog"]);
    assert.ok(Math.abs(last()[3] - 0.5) < 1e-9);
});

test("library: relative encoder and step buttons", () => {
    cc("lib", 64 + 3); assert.deepStrictEqual(last(), ["setValue", "[Library]", "MoveVertical", 3]);
    press("lib_up"); assert.deepStrictEqual(last(), ["setValue", "[Library]", "MoveVertical", -1]);
    press("lib_up", false); press("lib_down"); assert.deepStrictEqual(last(), ["setValue", "[Library]", "MoveVertical", 1]);
});

test("feedback: LED, 7-bit and 14-bit values go out on MIDI channel 2", () => {
    const play = byId("d1.play");
    engine.setValue("[Channel1]", "play_indicator", 1);
    state.connections.find((c) => c.g === "[Channel1]" && c.k === "play_indicator").cb();
    assert.deepStrictEqual(state.sent.pop(), [0x91, play.num, 127]);

    const rate = byId("d1.rate");
    state.params[key("[Channel1]", "rate")] = 0.5;
    state.connections.find((c) => c.g === "[Channel1]" && c.k === "rate").cb();
    const raw = Math.round(0.5 * 16383);
    assert.deepStrictEqual(state.sent.slice(-2), [[0xB1, rate.num, raw >> 7], [0xB1, rate.num + 32, raw & 127]]);

    const xf = byId("xfader");
    state.params[key("[Master]", "crossfader")] = 1;
    state.connections.find((c) => c.g === "[Master]" && c.k === "crossfader").cb();
    assert.deepStrictEqual(state.sent.pop(), [0xB1, xf.num, 127]);
});

test("polled values (VU, position, bpm) are sent only when they change", () => {
    const poll = Object.values(state.timers)[0].fn;
    state.params[key("[Channel1]", "VuMeter")] = 0.5;
    state.values[key("[Channel1]", "bpm")] = 128.04;
    poll();
    const first = state.sent.length;
    assert.ok(first >= 2);
    const bpm = byId("d1.bpm");
    assert.deepStrictEqual(state.sent.filter((m) => m[1] === bpm.num).pop(), [0xB1, bpm.num, (1280 >> 7)]);
    poll();
    assert.strictEqual(state.sent.length, first);                      // nothing changed: silence
    state.params[key("[Channel1]", "VuMeter")] = 1;
    poll();
    assert.strictEqual(state.sent.length, first + 1);
});

test("request note makes Mixxx resend everything", () => {
    press("request");
    assert.ok(state.sent.length >= P.PROTOCOL.filter((c) => c.feedback).length);
});

test("shutdown disconnects everything and releases scratch mode", () => {
    press("d1.jog_touch");
    P.shutdown();
    assert.strictEqual(Object.keys(state.timers).length, 0);
    assert.ok(state.connections.every((c) => c.disconnected));
    assert.strictEqual(state.scratching[1], false);
    P.init("DJSPanel", false);
});

test("every input control of the protocol can be driven without errors", () => {
    P.PROTOCOL.forEach((c) => {
        if (c.kind === "button") { press(c.id); press(c.id, false); }
        else if (c.kind === "abs7" || c.kind === "rel") { cc(c.id, 70); }
        else if (c.kind === "abs14") { cc(c.id, 70); cc(c.id, 3, 32); }
    });
});

test("MIDI numbers are unique per direction", () => {
    const seen = new Set();
    P.PROTOCOL.forEach((c) => {
        const keys = [];
        if (c.kind === "button" || c.kind === "led") keys.push("n" + c.num);
        else if (c.kind === "abs14" || c.kind === "out14") keys.push("c" + c.num, "c" + (c.num + 32));
        else keys.push("c" + c.num);
        keys.forEach((k) => { assert.ok(!seen.has(k), "duplicate " + k + " (" + c.id + ")"); seen.add(k); });
    });
});

console.log(n + " tests passed" + (process.exitCode ? " (with failures)" : ""));
