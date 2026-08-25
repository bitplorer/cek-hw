//! Peer **hw driver** — digital world for `hw.*`.
//!
//! Not a kernel. Same job as `cek-ops-ui`. Host already decided.
//! Catalog: repo `catalog/hw-v1.json`. Vendor into `cek-runtime` when that
//! workspace takes a third driver crate — do not publish a second Peer kernel.

#![forbid(unsafe_code)]

use serde_json::Value;
use std::collections::HashMap;

#[derive(Debug, Clone, Default)]
pub struct MotorState {
    pub running: bool,
    pub rpm: i64,
}

#[derive(Debug, Default, Clone)]
pub struct HwStore {
    pub gpio: HashMap<(String, u8), u8>,
    pub relays: HashMap<(String, String), u8>,
    pub motors: HashMap<(String, String), MotorState>,
    pub pulses: Vec<(String, String, u64)>,
    pub safe_applied: Vec<String>,
}

impl HwStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn gpio_set(&mut self, device: impl Into<String>, pin: u8, level: u8) {
        self.gpio
            .insert((device.into(), pin), if level == 0 { 0 } else { 1 });
    }

    pub fn gpio_get(&self, device: &str, pin: u8) -> Option<u8> {
        self.gpio.get(&(device.to_string(), pin)).copied()
    }

    pub fn relay_set(&mut self, device: impl Into<String>, id: impl Into<String>, level: u8) {
        self.relays
            .insert((device.into(), id.into()), if level == 0 { 0 } else { 1 });
    }

    pub fn motor_start(&mut self, device: impl Into<String>, id: impl Into<String>, rpm: i64) {
        self.motors.insert(
            (device.into(), id.into()),
            MotorState {
                running: true,
                rpm,
            },
        );
    }

    pub fn motor_stop(&mut self, device: impl Into<String>, id: impl Into<String>) {
        self.motors.insert(
            (device.into(), id.into()),
            MotorState {
                running: false,
                rpm: 0,
            },
        );
    }
}

/// Apply one hw Op. `Ok` landed; `Err` failed that Op.
pub fn apply_op(store: &mut HwStore, ns: &str, name: &str, payload: &Value) -> Result<(), ()> {
    let device = payload.get("device").and_then(|v| v.as_str()).ok_or(())?;
    match (ns, name) {
        ("hw.gpio", "set") => {
            let pin = payload.get("pin").and_then(|v| v.as_u64()).ok_or(())? as u8;
            let level = payload.get("level").and_then(|v| v.as_u64()).ok_or(())? as u8;
            store.gpio_set(device, pin, level);
            Ok(())
        }
        ("hw.relay", "set") => {
            let id = payload.get("id").and_then(|v| v.as_str()).ok_or(())?;
            let level = payload.get("level").and_then(|v| v.as_u64()).ok_or(())? as u8;
            store.relay_set(device, id, level);
            Ok(())
        }
        ("hw.relay", "pulse") => {
            let id = payload.get("id").and_then(|v| v.as_str()).ok_or(())?;
            let ms = payload.get("ms").and_then(|v| v.as_u64()).ok_or(())?;
            if ms == 0 {
                return Err(());
            }
            store.pulses.push((device.to_string(), id.to_string(), ms));
            store.relay_set(device, id, 0);
            Ok(())
        }
        ("hw.motor", "start") => {
            let id = payload.get("id").and_then(|v| v.as_str()).ok_or(())?;
            let rpm = payload.get("rpm").and_then(|v| v.as_i64()).unwrap_or(0);
            store.motor_start(device, id, rpm);
            Ok(())
        }
        ("hw.motor", "stop") => {
            let id = payload.get("id").and_then(|v| v.as_str()).ok_or(())?;
            store.motor_stop(device, id);
            Ok(())
        }
        ("hw.safe", "state") => {
            store.safe_applied.push(device.to_string());
            Ok(())
        }
        _ => Err(()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn gpio_set_get() {
        let mut s = HwStore::new();
        apply_op(
            &mut s,
            "hw.gpio",
            "set",
            &json!({"device":"p","pin":13,"level":1}),
        )
        .unwrap();
        assert_eq!(s.gpio_get("p", 13), Some(1));
    }

    #[test]
    fn unknown_pair_fails() {
        let mut s = HwStore::new();
        assert!(apply_op(&mut s, "ui.dom", "morph", &json!({})).is_err());
    }
}
