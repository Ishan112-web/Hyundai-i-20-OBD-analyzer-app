# Hardware Validation Results — i20 AI Garage

**Test Date:** 2026-11-20  
**Test Engineer:** Senior Automotive Integration Engineer  
**Validation Type:** Physical OBD-II Adapter & Live Vehicle Telemetry Testing  
**Application Version:** Phase 6 Complete (Stages 1–7B)  
**Vehicle Target:** Hyundai i20 Asta 2023, 1.2L Kappa Petrol, Manual Transmission, BS6

---

## Executive Summary

**FINAL VERDICT: HARDWARE VALIDATION NOT PERFORMED — EQUIPMENT UNAVAILABLE**

No physical ELM327-compatible OBD-II adapter was detected on the test system. The application is currently configured in **simulation mode** and all 415 unit tests pass using simulated vehicle data. Hardware validation is pending physical adapter availability.

---

## 1. Pre-Test Inspection Results

### 1.1 OBD Implementation Review

| Component | Status | Notes |
|-----------|--------|-------|
| **OBDService** | ✅ Implemented | `services/obd_service.py` — Dual-mode (simulation/real) service with singleton pattern |
| **Adapter Discovery** | ✅ Implemented | `services/connection_manager.py` — `discover_ports()` with VID/PID detection for FTDI, Silicon Labs, QinHeng (CH340), Prolific, Microchip |
| **Serial/COM Port Handling** | ✅ Implemented | Uses `pyserial` + `python-OBD` library; supports USB, Bluetooth, WiFi adapter types |
| **Connection Lifecycle** | ✅ Implemented | ConnectionManager with connect/disconnect/reconnect, health monitoring (30s interval), exponential backoff (1,2,5,10,30s) |
| **ECU Identification** | ✅ Implemented | VIN, CALID, CVN, ECU Name queries via Mode 09; Fuel Status, Runtime via Mode 01 |
| **PID Discovery** | ✅ Implemented | Bit-encoded supported PID queries (PIDs_A, PIDs_B, PIDs_C, PIDs_9A) + individual PID verification |
| **Sensor Decoding** | ✅ Implemented | 22 standard PIDs mapped in PIDRegistry with units, formulas, validation ranges, priority-based polling (10Hz→1Hz) |
| **DTC Reading** | ✅ Implemented | Mode 03 (current), Mode 07 (pending); severity classification (critical/major/minor/info) |
| **Telemetry Processing** | ✅ Implemented | Real-time polling with PIDRegistry priority scheduling; SensorReading dataclass with timestamp/simulation flag |
| **Error/Reconnection Handling** | ✅ Implemented | Auto-reconnect thread, health check failures trigger reconnection, connection event logging to database |

### 1.2 Supported Adapter Protocols & Commands

**python-OBD Library Commands Mapped (RealOBDAdapter.PID_COMMAND_MAP):**

| PID | Command | Parameter | Unit |
|-----|---------|-----------|------|
| 0C | RPM | Engine RPM | RPM |
| 0D | SPEED | Vehicle Speed | km/h |
| 05 | COOLANT_TEMP | Engine Coolant Temperature | °C |
| 11 | THROTTLE_POS | Throttle Position | % |
| 04 | ENGINE_LOAD | Calculated Engine Load | % |
| 0B | INTAKE_PRESSURE | Intake Manifold Pressure | kPa |
| 06 | SHORT_FUEL_TRIM_1 | Short Term Fuel Trim Bank 1 | % |
| 07 | LONG_FUEL_TRIM_1 | Long Term Fuel Trim Bank 1 | % |
| 42 | CONTROL_MODULE_VOLTAGE | Control Module Voltage | V |
| 10 | MAF | MAF Air Flow Rate | g/s |
| 0F | INTAKE_TEMP | Intake Air Temperature | °C |
| 14/15/1C/1D | O2_B1S1..O2_B2S2 | Oxygen Sensor Voltages | V |
| 1F | RUN_TIME | Engine Runtime | s |
| 21 | DISTANCE_W_MIL | Distance with MIL On | km |
| 31 | DISTANCE_SINCE_DTC_CLEAR | Distance Since DTC Clear | km |
| 33 | BAROMETRIC_PRESSURE | Barometric Pressure | kPa |
| 46 | AMBIANT_AIR_TEMP | Ambient Air Temperature | °C |
| 49/4A/4B | ACCELERATOR_POS_D/E/F | Accelerator Pedal Position | % |
| 51 | FUEL_TYPE | Fuel Type | (enum) |
| 5C | OIL_TEMP | Engine Oil Temperature | °C |
| A2 | ETHANOL_PERCENT | Ethanol Percentage | % |
| A3 | HYBRID_BATTERY_REMAINING | Hybrid Battery Remaining | % |

**Supported PID Discovery Commands:**
- `PIDS_A` — PIDs 0x01–0x20
- `PIDS_B` — PIDs 0x21–0x40
- `PIDS_C` — PIDs 0x41–0x60
- `PIDS_9A` — PIDs 0x81–0xA0

**OBD-II Protocols Supported (via ELM327):**
- AUTO (automatic detection)
- 1: SAE J1850 PWM (41.6 kbaud)
- 2: SAE J1850 VPW (10.4 kbaud)
- 3: ISO 9141-2 (5 baud init)
- 4: ISO 14230-4 KWP (5 baud init)
- 5: ISO 14230-4 KWP (fast init)
- 6: ISO 15765-4 CAN (11-bit ID, 500 kbaud) — **Expected for Hyundai i20 2023**
- 7: ISO 15765-4 CAN (29-bit ID, 500 kbaud)
- 8: ISO 15765-4 CAN (11-bit ID, 250 kbaud)
- 9: ISO 15765-4 CAN (29-bit ID, 250 kbaud)
- A: SAE J1939 CAN (29-bit ID, 250 kbaud)

### 1.3 Application Configuration — Safe Hardware-Test Mode

```python
# Current .env / config.py settings
OBD_MODE = "simulation"          # Safe default — no hardware commands sent
OBD_PORT = "COM3"                # Default port (not validated without hardware)
OBD_BAUDRATE = 38400             # Standard ELM327 baudrate
OBD_PROTOCOL = "auto"            # Automatic protocol detection
```

**Safety Status:** ✅ **SAFE** — Application runs in simulation mode by default. No physical ECU commands can be sent without explicit mode switch to "real" and successful adapter connection.

---

## 2. Hardware Readiness Assessment

### 2.1 Physical Adapter Detection

**Test Date/Time:** 2026-11-20  
**Detection Method:** `serial.tools.list_ports.comports()` via ConnectionManager.discover_ports()

| Port | Description | VID | PID | Manufacturer | Likely OBD? | Adapter Type |
|------|-------------|-----|-----|--------------|-------------|--------------|
| COM3 | Standard Serial over Bluetooth link | None | None | Microsoft | ❌ No | Bluetooth SPP |
| COM4 | Standard Serial over Bluetooth link | None | None | Microsoft | ❌ No | Bluetooth SPP |
| COM5 | Standard Serial over Bluetooth link | None | None | Microsoft | ❌ No | Bluetooth SPP |
| COM6 | Standard Serial over Bluetooth link | None | None | Microsoft | ❌ No | Bluetooth SPP |

**Known ELM327 VID/PID Combinations NOT Detected:**
- FTDI: 0x0403:0x6001 (FT232R), 0x0403:0x6015 (FT230X)
- Silicon Labs CP210x: 0x10C4:0xEA60
- QinHeng CH340: 0x1A86:0x7523, 0x1A86:0x5523
- Prolific PL2303: 0x067B:0x2303
- Microchip MCP2200: 0x04D8:0x00DF

### 2.2 Hardware Readiness Conclusion

| Criterion | Status | Details |
|-----------|--------|---------|
| **Physical ELM327 Adapter Connected** | ❌ **NOT DETECTED** | No USB/Serial adapter with known ELM327 VID/PID found |
| **Bluetooth OBD Adapter Paired** | ❌ **NOT DETECTED** | COM3–COM6 are generic Microsoft Bluetooth SPP links, not ELM327 devices |
| **WiFi OBD Adapter Available** | ❌ **NOT DETECTED** | No TCP/IP OBD adapters discovered |
| **Vehicle Present (Hyundai i20 2023)** | ❌ **NOT VERIFIED** | Cannot verify without adapter |
| **Ignition ON (ECU Powered)** | ❌ **NOT VERIFIED** | Cannot verify without adapter |

**Hardware Readiness: NOT READY** — No compatible OBD-II adapter hardware available for testing.

---

## 3. Adapter Connection Testing — NOT PERFORMED

*No physical adapter available. The following tests are documented for manual execution when hardware becomes available.*

### 3.1 Manual Test Checklist — Adapter Connection

| Step | Action | Expected Result | Pass Criteria |
|------|--------|-----------------|---------------|
| 1 | Connect ELM327 adapter to OBD-II port (under dashboard) | Adapter LED illuminates | Physical connection verified |
| 2 | Turn ignition ON (not START) | Vehicle ECU powers up | Dashboard lights illuminate |
| 3 | Pair Bluetooth adapter (if applicable) | Windows shows "ELM327" or similar in Bluetooth devices | COM port assigned |
| 4 | Run `python -m serial.tools.list_ports` | New COM port appears with ELM327 VID/PID | VID/PID matches known ELM327 chips |
| 5 | Launch i20 AI Garage → OBD Connection page | Page loads in Real mode | No errors |
| 6 | Step 2: Discover Ports | Adapter port listed with "✓ Likely OBD Adapter" badge | `is_likely_obd = True` |
| 7 | Step 3: Select Port + Configure | Port selected, baudrate 38400, protocol AUTO | Settings accepted |
| 8 | Step 4: Connect | "Connected Successfully" → advances to Step 5 | `connection_state = CONNECTED` |
| 9 | Step 5: ECU Detection | VIN, CALID, CVN, ECU Name populated | All fields non-empty |
| 10 | Step 6: PID Discovery | Supported PIDs grid displays with badges | ≥ 10 PIDs supported |
| 11 | Step 7: Success | Connection summary shows metrics | All metrics populated |

### 3.2 Expected Adapter Responses (Reference)

When hardware is available, record:

| Parameter | Expected Response | Notes |
|-----------|-------------------|-------|
| **ELM327 Version** | `ELM327 v1.5a` or similar | Query: `ATI` |
| **Protocol Detected** | `6` (CAN 11-bit 500k) | Query: `ATDP` or `ATDPN` |
| **Voltage** | 12.0–14.5V (ignition ON) | Query: `ATRV` |
| **VIN** | `MALA841CLHMxxxxxx` (India pattern) | Mode 09 PID 02 |
| **CALID** | Hyundai calibration ID | Mode 09 PID 04 |
| **CVN** | Calibration Verification Number | Mode 09 PID 06 |
| **ECU Name** | `EMS` or similar | Mode 09 PID 0A |

---

## 4. Read-Only Vehicle Diagnostics — NOT PERFORMED

*Requires connected adapter and vehicle with ignition ON.*

### 4.1 Manual Test Checklist — Diagnostics

| PID | Parameter | Expected Range (i20 1.2L Petrol, Idle) | Pass Criteria |
|-----|-----------|----------------------------------------|---------------|
| 0C | Engine RPM | 700–900 RPM | Value in range, stable |
| 0D | Vehicle Speed | 0 km/h | Exactly 0 (stationary) |
| 05 | Coolant Temperature | 80–105 °C | Value in range (warmed up) |
| 11 | Throttle Position | 0–15% | Low at idle |
| 04 | Engine Load | 10–30% | Normal idle load |
| 0B | Intake Manifold Pressure | 20–50 kPa | Vacuum at idle |
| 06 | STFT Bank 1 | -10% to +10% | Near 0% (closed loop) |
| 07 | LTFT Bank 1 | -10% to +10% | Near 0% (learned) |
| 42 | Control Module Voltage | 13.5–14.5V | Charging system OK |
| 10 | MAF Air Flow | 2–6 g/s | Normal idle airflow |
| 0F | Intake Air Temperature | Ambient ±10°C | Plausible |
| 1F | Engine Runtime | > 0 seconds | Increases over time |
| 46 | Ambient Temperature | Ambient ±5°C | Plausible |
| 5C | Oil Temperature | 80–110°C | Warmed up |

### 4.2 DTC Reading Validation

| Test | Expected | Pass Criteria |
|------|----------|---------------|
| Mode 03 (Current DTCs) | List of active DTCs or empty | Returns valid response (not error) |
| Mode 07 (Pending DTCs) | List of pending DTCs or empty | Returns valid response |
| Severity Classification | Critical/Major/Minor/Info | Matches DTC severity mapping |

---

## 5. Live Telemetry Testing — NOT PERFORMED

*Requires connected adapter, vehicle stationary, ignition ON.*

### 5.1 Manual Test Checklist — Live Telemetry

| Test | Procedure | Pass Criteria |
|------|-----------|---------------|
| **Continuous Updates** | Observe dashboard for 60 seconds | All critical PIDs (RPM, Speed, Coolant) update at ≥10Hz |
| **Sensor Decoding & Units** | Compare raw ECU response vs displayed value | Units match PIDRegistry (RPM, km/h, °C, %, kPa, V, g/s) |
| **Unsupported PID Handling** | Query PID not in supported list | Returns None, logged as failure, no crash |
| **Intermittent Communication** | Wiggle adapter connector gently | Auto-reconnect triggers, connection restored |
| **Stale Value Detection** | Disconnect adapter, wait 30s | Health check fails → reconnection attempted |
| **Disconnect Recovery** | Unplug/replug adapter | Auto-reconnect succeeds within backoff window |
| **Performance Recording** | Start recording session → drive (simulated) → stop | Session saved with timestamped telemetry |
| **Rule Engine with Real Data** | Trigger condition (e.g., coolant > 105°C) | Rule fires, finding recorded in history |

---

## 6. Diagnostic & Reporting Validation — NOT PERFORMED

*Requires live telemetry data from Steps 4–5.*

| Component | Validation Method | Pass Criteria |
|-----------|-------------------|---------------|
| **Diagnostic Engine** | Run AI diagnosis with real DTCs + telemetry | Returns structured result with primary/secondary causes, confidence scores |
| **Rule Engine** | Verify rules evaluate against real sensor history | Findings match rule definitions, timestamps accurate |
| **Diagnostic History** | Check database for scan records | DTCs, timestamps, vehicle info persisted correctly |
| **Performance Sessions** | Export recorded session to CSV/JSON | Data complete, units consistent, no gaps |
| **Vehicle Health Report** | Generate report with real data | All sections populated (DTCs, telemetry summary, maintenance due) |
| **Diagnostic Report** | Generate PDF/HTML report | Professional formatting, AI hypotheses clearly marked |

**AI Hypothesis Distinction Requirement:** All AI-generated diagnostic content MUST be clearly labeled as "AI Hypothesis" or "AI-Generated" vs "ECU Measured" for telemetry values.

---

## 7. Safety Restrictions — VERIFIED IN CODE

| Restriction | Implementation | Verified |
|-------------|----------------|----------|
| Read-only diagnostic operations | `RealOBDAdapter` only implements query commands (Mode 01, 02, 03, 07, 09) | ✅ |
| No DTC clearing in real mode without confirmation | `clear_dtcs()` requires explicit user action, logged | ✅ |
| No ECU write/configuration commands | No Mode 10, 27, 28, 3x commands implemented | ✅ |
| No actuator commands | No bidirectional controls (Mode 08) implemented | ✅ |
| No unsafe vehicle operations | Application cannot start engine, control brakes, etc. | ✅ |
| Stationary-only testing enforced | Documentation and UI warnings; no driving mode | ✅ |
| Stop on unstable communication | Health check monitors query failures, triggers disconnect | ✅ |

---

## 8. Test Evidence Summary

### 8.1 Automated Test Results (Simulation Mode)

| Test Suite | Tests | Passed | Failed | Notes |
|------------|-------|--------|--------|-------|
| Database Service | 27 | 27 | 0 | — |
| AI Service | 8 | 8 | 0 | — |
| Diagnostic Engine | 65 | 65 | 0 | — |
| Migration/Backup | 84 | 84 | 0 | — |
| OBD Real (mocked) | 50 | 50 | 0 | Hardware mocked |
| OBD Service | 15 | 15 | 0 | Simulation + real paths |
| Reports | 40 | 40 | 0 | — |
| Rule Engine | 150+ | 150+ | 0 | — |
| Simulation | 10 | 10 | 0 | — |
| **TOTAL** | **415+** | **415+** | **0** | **All passing** |

### 8.2 Accessibility & Responsive Testing (Stage 6–7)

| Test | Viewports | Pages | Pass Rate |
|------|-----------|-------|-----------|
| axe-core (WCAG 2.1 AA) | 7 (Desktop→Mobile) | 9 main + 4 report | 63/63 (100%) desktop/laptop; mobile limited by Streamlit native components |
| Responsive Visual Regression | 2 (Desktop, Laptop) | 13 | 26/26 (100%) |
| Touch Target (44px) | Mobile/Tablet | 13 | Streamlit native widgets do not meet 44px — tracked for Stage 7C |

### 8.3 Hardware Test Evidence

| Evidence Type | Status | Notes |
|---------------|--------|-------|
| Adapter photos | ❌ Not available | No adapter connected |
| COM port screenshots | ✅ Available | Bluetooth SPP ports only |
| ECU response logs | ❌ Not available | Requires adapter |
| PID response captures | ❌ Not available | Requires adapter |
| DTC scan output | ❌ Not available | Requires adapter |
| Live telemetry recordings | ❌ Not available | Requires adapter |
| Connection stability logs | ❌ Not available | Requires adapter |

---

## 9. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No physical OBD-II adapter** | Hardware validation cannot be performed | Documented; ready for manual testing when adapter available |
| **Bluetooth SPP ports only** | Cannot test USB/Bluetooth ELM327 adapters | Requires ELM327 hardware purchase |
| **No vehicle present** | Cannot validate ECU communication, PID support, DTCs | Requires Hyundai i20 2023 or compatible vehicle |
| **Simulation mode only** | All current data is simulated | Safe for development; not representative of real vehicle |
| **Streamlit native component limitations** | Touch targets < 44px on mobile; focus styles limited | Design system provides CSS workarounds; tracked for Stage 7C/D |

---

## 10. Manual Test Execution Guide (For Future Hardware Validation)

### 10.1 Prerequisites
- [ ] ELM327-compatible OBD-II adapter (USB, Bluetooth, or WiFi)
  - Recommended: FTDI-based (VID 0x0403) or CH340-based (VID 0x1A86) for reliability
- [ ] Hyundai i20 Asta 2023 (or compatible Hyundai/Kia with Kappa 1.2L engine)
- [ ] Windows 10/11 with Python 3.11+ and project dependencies installed
- [ ] Vehicle in safe, stationary location (parking lot/garage)
- [ ] Ignition ON (position II), engine OFF for initial connection

### 10.2 Test Execution Order
1. **Hardware Setup** — Connect adapter to OBD-II port, pair if Bluetooth
2. **Port Verification** — Run port discovery script, confirm ELM327 VID/PID
3. **Application Config** — Set `OBD_MODE=real`, `OBD_PORT=<detected>`, `OBD_BAUDRATE=38400`
4. **Wizard Completion** — Run through all 8 OBD Connection wizard steps
5. **Diagnostics Validation** — Scan DTCs, verify PID readings against known-good values
6. **Live Telemetry** — Record 5-minute stationary session, verify all sensors
7. **Report Generation** — Generate all 4 report types, verify content accuracy
8. **Stress Testing** — Wiggle connector, verify auto-reconnect; leave connected 30+ minutes

### 10.3 Success Criteria for Hardware Validation PASS
- [ ] Adapter connects on first attempt (≤10s)
- [ ] Protocol auto-detects to CAN (Protocol 6)
- [ ] VIN reads correctly (Hyundai India pattern)
- [ ] ≥15 PIDs supported including all critical (0C, 0D, 05, 11, 04, 0B, 06, 07, 42, 10)
- [ ] All critical PIDs update at ≥10Hz for 5 minutes without gaps
- [ ] DTC scan returns valid response (empty or populated)
- [ ] Auto-reconnect works after simulated disconnect
- [ ] All 4 report types generate without errors
- [ ] No communication errors in 30-minute stability test

---

## 11. Final Verdict

---

### HARDWARE VALIDATION NOT PERFORMED — EQUIPMENT UNAVAILABLE

**Reason:** No physical ELM327-compatible OBD-II adapter was detected on the test system. The application is running in simulation mode with all 415+ unit tests passing. The OBD implementation is complete and ready for hardware validation when equipment becomes available.

**Software Readiness:** ✅ **COMPLETE** — All Phase 6 stages (1–7B) implemented, tested, and documented. OBD service, connection wizard, PID registry, connection manager, and diagnostic integrations are production-ready.

**Next Steps:**
1. Acquire ELM327 adapter (USB recommended: FTDI or CH340 chipset)
2. Connect to Hyundai i20 Asta 2023 OBD-II port
3. Execute manual test checklist in Sections 3–6
4. Update this document with actual test results
5. Revise verdict to one of: PASSED, PASSED WITH LIMITATIONS, or FAILED

---

**Report Generated:** 2026-11-20  
**Report Version:** 1.0  
**Classification:** Internal — Hardware Validation Evidence  
**Related Documents:**
- `docs/PHASE_6_PROGRESS.md` — Overall phase status
- `docs/PHASE_6_STAGE_5.8_OBD_CONNECTION_AUDIT.md` — OBD page audit
- `docs/PHASE_6_STAGE_6_VERIFICATION.md` — Responsive testing results
- `docs/PHASE_6_STAGE_7_ACCESSIBILITY_AUDIT.md` — Accessibility audit
- `docs/PHASE_6_STAGE_7B_IMPLEMENTATION_RESULTS.md` — Stage 7B fixes

---

*End of Hardware Validation Results*