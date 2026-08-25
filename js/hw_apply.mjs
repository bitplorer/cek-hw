/**
 * hw-v1 apply_op — port of cek_hw.apply. Do not grow a second catalog.
 * Pair identity: (ns, name). Concatenation is never identity.
 */
export const HW_PAIRS = [
  ["hw.gpio", "set"],
  ["hw.relay", "set"],
  ["hw.relay", "pulse"],
  ["hw.motor", "start"],
  ["hw.motor", "stop"],
  ["hw.safe", "state"],
];

const PAIR_SET = new Set(HW_PAIRS.map(([n, m]) => `${n}\0${m}`));

export function isHwPair(ns, name) {
  return PAIR_SET.has(`${ns}\0${name}`);
}

export function createStore() {
  return { gpio: new Map(), relays: new Map(), motors: new Map(), pulses: [], safeApplied: [] };
}

function gk(device, pin) {
  return `${device}:${pin}`;
}

export function applyOp(store, op, registry = null) {
  const ns = String(op.ns || "");
  const name = String(op.name || "");
  if (!isHwPair(ns, name)) throw new Error(`not an hw pair: ${ns}.${name}`);
  const p = op.payload || {};
  const device = p.device;
  if (!device) throw new Error("device required");
  const bound = registry ? registry[device] : null;
  if (registry && !bound) throw new Error(`unknown device: ${device}`);

  if (ns === "hw.gpio" && name === "set") {
    const pin = Number(p.pin);
    if (bound && !(bound.pins || []).includes(pin)) throw new Error(`unknown pin ${pin}`);
    store.gpio.set(gk(device, pin), p.level ? 1 : 0);
    return;
  }
  if (ns === "hw.relay" && name === "set") {
    store.relays.set(gk(device, p.id), p.level ? 1 : 0);
    return;
  }
  if (ns === "hw.relay" && name === "pulse") {
    store.pulses.push({ device, id: p.id, ms: p.ms });
    store.relays.set(gk(device, p.id), 0);
    return;
  }
  if (ns === "hw.motor" && name === "start") {
    store.motors.set(gk(device, p.id), { running: true, rpm: p.rpm || 0 });
    return;
  }
  if (ns === "hw.motor" && name === "stop") {
    store.motors.set(gk(device, p.id), { running: false, rpm: 0 });
    return;
  }
  if (ns === "hw.safe" && name === "state") {
    store.safeApplied.push(device);
    if (bound) {
      for (const pin of bound.pins || []) store.gpio.set(gk(device, pin), bound.safe?.[pin] ?? 0);
    }
  }
}

export function applyResult(store, result, registry = null) {
  const kind = result.kind;
  if (kind === "authority_refusal" || kind === "dispatch_error") {
    return { landed: [], failed: [] };
  }
  const landed = [];
  const failed = [];
  let abort = false;
  for (const op of result.ops || []) {
    if (abort) {
      failed.push(op);
      continue;
    }
    if (!isHwPair(op.ns, op.name)) {
      failed.push(op);
      abort = true;
      continue;
    }
    try {
      applyOp(store, op, registry);
      landed.push(op);
    } catch {
      failed.push(op);
    }
  }
  return { landed, failed };
}

export function snapshot(store) {
  return {
    gpio: Object.fromEntries([...store.gpio.entries()].sort()),
    relays: Object.fromEntries([...store.relays.entries()].sort()),
    motors: Object.fromEntries([...store.motors.entries()].sort()),
    pulses: [...store.pulses],
    safeApplied: [...store.safeApplied],
  };
}
