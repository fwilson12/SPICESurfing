'''
Optimizer / validation agent.

Runs the five-stage check suite over an LLM-generated PySpice script and, on the
first failure, asks the LLM for a targeted repair plan. The five stages mirror the
AnalogAgent paper's design-optimizer checks (requirement → operating point →
sweep → function → waveform), but here they are *circuit-class aware*: a circuit
"profile" (see PROFILES) decides which stimulus drives the later stages and which
assertions are meaningful, so the suite runs end-to-end for amplifiers, oscillators,
filters, mirrors and digital/system blocks instead of assuming everything is an amplifier.
'''

import ollama
import numpy as np
from dataclasses import dataclass, field
from schema import CheckResult, IterationRecord

import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)



# Minimum transistor counts per circuit type for topology validation
TOPOLOGY_REQUIREMENTS = {
    "Inverter":       {"Mosfet": 2},
    "LogicGate":      {"Mosfet": 2},
    "Amplifier":      {"Mosfet": 1},
    "CurrentMirror":  {"Mosfet": 2},
    "Opamp":          {"Mosfet": 4},
    "Oscillator":     {"Mosfet": 1},
    "Schmitt":        {"Mosfet": 2},
    "Comparator":     {"Mosfet": 1},
    "VCO":            {"Mosfet": 1},
    "Latch":          {"Mosfet": 4},
    "Switch":         {"Mosfet": 1},
    "Mixer":          {"Mosfet": 4},
    "Filter":         {},   # no MOSFET requirement
    "ADC":            {"Mosfet": 2},
    "DAC":            {"Mosfet": 2},
    "PLL":            {"Mosfet": 4},
    "VoltageReference":{"Mosfet": 1},
    "VoltageRegulator":{"Mosfet": 1},
    "BiasCircuit":    {"Mosfet": 2},
    "ChargePump":     {"Mosfet": 2},
    "SampleHold":     {"Mosfet": 1},
    "Integrator":     {"Mosfet": 1},
    "Adder":          {"Mosfet": 2},
}

# Approximate threshold voltage magnitudes for saturation checks
NMOS_VTH = 0.5
PMOS_VTH = 0.5  # magnitude — actual Vth is negative for PMOS


def check_suite(script: str, task: dict) -> list[CheckResult]:
    '''
    Run all five check stages in sequence. Returns early on first failure.
    simspace carries circuit object and sim results between stages.
    '''
    results = []
    simspace = {} # namespace for isolated script execution, used to fetch circuit/simulation results 

    ''' Stage 1: basic requirement/topology checks '''
    try:
        exec(script, simspace)
    
    except SyntaxError as e:
        results.append(CheckResult(
            stage="requirement", passed=False,
            message=f"SyntaxError: {e}",
            details=str(e)
        ))
        return results
    
    except Exception as e:
        results.append(CheckResult(
            stage="requirement", passed=False,
            message=f"Script execution error: {e}",
            details=str(e)
        ))
        return results

    # script must define a top-level variable named 'circuit'
    circuit = simspace.get("circuit")
    if circuit is None:
        results.append(CheckResult(
            stage="requirement", passed=False,
            message="Script did not define a 'circuit' variable.",
            details="Ensure the PySpice Circuit object is assigned to a variable named 'circuit'."
        ))
        return results

    # check required nodes exist
    node_names = [str(n) for n in circuit.nodes]
    for required_node in ["Vout"]:
        if required_node not in node_names:
            results.append(CheckResult(
                stage="requirement", passed=False,
                message=f"Required node '{required_node}' not found in circuit.",
                details=f"Nodes present: {node_names}"
            ))
            return results

    # check minimum device counts for this circuit type
    circuit_type = task.get("circuit_type", "")
    reqs = TOPOLOGY_REQUIREMENTS.get(circuit_type, {})
    element_types = [type(e).__name__ for e in circuit.elements]
    for device, min_count in reqs.items():
        count = element_types.count(device)
        if count < min_count:
            results.append(CheckResult(
                stage="requirement", passed=False,
                message=f"Topology error: expected at least {min_count} {device}(s), found {count}.",
                details=f"All elements: {element_types}"
            ))
            return results

    results.append(CheckResult(
        stage="requirement", passed=True,
        message="Netlist compiled, required nodes and devices present.",
        details=f"Nodes: {node_names} | Elements: {element_types}"
    ))

    ''' Stage 2: operating point checks for all MOSFETs in circuit '''
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        op = simulator.operating_point()
        simspace["op"] = op

        failures = []
        for element in circuit.elements:
            if type(element).__name__ != "Mosfet":
                continue

        name = str(element.name)
        is_pmos = "pmos" in str(element.model).lower() or str(element.model).lower().startswith("p")
        try:
            vg = float(op[str(element.gate)])
            vs = float(op[str(element.source)])
            vd = float(op[str(element.drain)])
        except KeyError as e:
            failures.append(f"{name}: node {e} not found in op results")
            continue

        if is_pmos:
            vsg, vsd = vs - vg, vs - vd
            if vsg < PMOS_VTH:
                failures.append(f"{name} (PMOS): Vsg={vsg:.3f}V < Vth={PMOS_VTH}V — not in saturation")
            elif vsd < vsg - PMOS_VTH:
                failures.append(f"{name} (PMOS): Vsd={vsd:.3f}V < Vsg-Vth={vsg - PMOS_VTH:.3f}V — not in saturation")
        else:
            vgs, vds = vg - vs, vd - vs
            if vgs < NMOS_VTH:
                failures.append(f"{name} (NMOS): Vgs={vgs:.3f}V < Vth={NMOS_VTH}V — not in saturation")
            elif vds < vgs - NMOS_VTH:
                failures.append(f"{name} (NMOS): Vds={vds:.3f}V < Vgs-Vth={vgs - NMOS_VTH:.3f}V — not in saturation")
    return failures


# --- The five check stages -------------------------------------------------
# Each stage returns a single CheckResult. check_suite() runs them in order and
# stops at the first failure; simspace carries the circuit object and any simulation
# results forward between stages so later stages don't re-run analyses.

def _check_requirement(script: str, task: dict, profile: CircuitProfile, simspace: dict) -> CheckResult:
    '''
    Stage 1 — Requirement / topology.
    Execute the script and confirm the structural basics: it compiles and runs, defines a
    'circuit' object, has a ground node and a recognizable output node, and contains at
    least the minimum devices expected for this circuit family.
    '''
    try:
        exec(script, simspace)
    except SyntaxError as e:
        return _result("requirement", False, f"SyntaxError: {e}", str(e))
    except Exception as e:
        return _result("requirement", False, f"Script execution error: {e}", str(e))

    circuit = simspace.get("circuit")
    if circuit is None:
        return _result("requirement", False,
                       "Script did not define a 'circuit' variable.",
                       "Assign the PySpice Circuit object to a top-level variable named 'circuit'.")

    node_names = [str(n) for n in circuit.nodes]

    # ngspice needs a ground reference ('0') reachable in the netlist
    if "0" not in node_names:
        return _result("requirement", False,
                       "No ground node found — circuit.gnd ('0') is required by ngspice.",
                       f"Nodes present: {node_names}")

    # an output node must exist under a recognized name (Vout by convention)
    out_node = _find_output_node(circuit, profile)
    if out_node is None:
        return _result("requirement", False,
                       "No recognized output node found.",
                       f"Expected one of {tuple(profile.output_nodes) + OUTPUT_CANDIDATES}; nodes present: {node_names}")

    # minimum device counts for this circuit type
    element_types = [type(e).__name__ for e in circuit.elements]
    for device, min_count in profile.min_devices.items():
        count = element_types.count(device)
        if count < min_count:
            return _result("requirement", False,
                           f"Topology error: expected at least {min_count} {device}(s), found {count}.",
                           f"All elements: {element_types}")

    simspace["out_node"] = out_node
    return _result("requirement", True,
                   "Netlist compiled; ground, output node and required devices present.",
                   f"Output: {out_node} | Nodes: {node_names} | Elements: {element_types}")


def _check_op_point(profile: CircuitProfile, simspace: dict) -> CheckResult:
    '''
    Stage 2 — Operating point / DC feasibility.
    Solve the DC operating point (catches floating nodes / singular-matrix / non-convergence).
    For analog gain & bias classes, additionally require every MOSFET to sit in saturation;
    switching and digital circuits legitimately rest in triode/cutoff, so they only need to converge.
    '''
    circuit = simspace["circuit"]
    try:
        op = circuit.simulator(temperature=25, nominal_temperature=25).operating_point()
    except Exception as e:
        return _result("op_point", False, f"Operating point simulation failed: {e}", str(e))
    simspace["op"] = op

    if profile.expect_saturation:
        failures = _saturation_failures(circuit, op)
        if failures:
            return _result("op_point", False, "One or more MOSFETs not in saturation.", "\n".join(failures))
        return _result("op_point", True, "All MOSFETs biased in saturation.")

    # switching / digital: convergence alone is the bar; report the output rail for context
    try:
        vout = float(op[simspace["out_node"]])
        detail = f"Operating point Vout = {vout:.3f}V"
    except Exception:
        detail = "Operating point solved."
    return _result("op_point", True, "DC operating point converged.", detail)


def _check_dc_sweep(profile: CircuitProfile, simspace: dict) -> CheckResult:
    '''
    Stage 3 — Stimulus / response.
    Drive the circuit with the stimulus appropriate to its family and confirm the output
    actually moves: a DC input sweep for transfer circuits, a transient for oscillators,
    an AC sweep for filters. Static and structural classes have no meaningful sweep here.
    '''
    circuit = simspace["circuit"]
    out_node = simspace["out_node"]

    if profile.mode == "transfer":
        # Sweep the detected DC input across the supply rails; a working transfer circuit
        # must produce an output that responds rather than sitting pinned at a rail.
        vdd, _, input_src = _classify_sources(circuit)
        simspace["vdd"] = vdd
        if input_src is None:
            return _result("dc_sweep", False,
                           "Could not identify a DC input source to sweep.",
                           "Add a DC voltage source on the input node (e.g. circuit.V('in', 'Vin', gnd, ...)).")
        try:
            dc = circuit.simulator(temperature=25, nominal_temperature=25).dc(
                **{str(input_src.name): slice(0, vdd, vdd / 50)})
        except Exception as e:
            return _result("dc_sweep", False, f"DC sweep failed: {e}", str(e))

        vout = np.array(dc[out_node], dtype=float)
        simspace["dc"] = dc
        simspace["vin"] = np.array(dc[str(input_src.name)], dtype=float)
        simspace["vout"] = vout

        if np.std(vout) / vdd < RAIL_STUCK_TOL:
            pinned = "Vdd" if np.mean(vout) > vdd * 0.8 else "GND"
            return _result("dc_sweep", False,
                           f"Vout is rail-stuck near {pinned} across the entire sweep.",
                           f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V, Vdd={vdd}V")
        return _result("dc_sweep", True, "Vout responds to the input sweep — not rail-stuck.",
                       f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V")

    if profile.mode == "oscillator":
        # No DC input to sweep — run a transient and confirm the output is time-varying
        # (a flat output means the loop never started oscillating).
        try:
            tran = circuit.simulator(temperature=25, nominal_temperature=25).transient(
                step_time=OSC_STEP, end_time=OSC_END)
        except Exception as e:
            return _result("dc_sweep", False, f"Transient simulation failed: {e}", str(e))

        tvout = np.array(tran[out_node], dtype=float)
        simspace["tvout"] = tvout
        if np.std(tvout) < 1e-3:
            return _result("dc_sweep", False,
                           "Output is flat in transient — circuit is not oscillating.",
                           "Ensure an odd-inversion loop and seed an initial condition to start oscillation.")
        return _result("dc_sweep", True, "Output is time-varying in transient.",
                       f"Vout range: [{tvout.min():.3f}, {tvout.max():.3f}]V")

    if profile.mode == "filter":
        # Run an AC sweep and confirm the magnitude response is frequency-dependent
        # (a flat or all-zero response means it isn't filtering / has no AC drive).
        try:
            ac = circuit.simulator(temperature=25, nominal_temperature=25).ac(
                start_frequency=AC_START, stop_frequency=AC_STOP,
                number_of_points=AC_POINTS_PER_DECADE, variation="dec")
        except Exception as e:
            return _result("dc_sweep", False, f"AC sweep failed: {e}", str(e))

        mag = np.abs(np.array(ac[out_node], dtype=complex))
        simspace["mag"] = mag
        if mag.max() < 1e-9:
            return _result("dc_sweep", False,
                           "AC response is ~0 across the band — no signal reaches the output.",
                           "Set an AC magnitude on the input source (e.g. ac=1) and check the signal path.")
        return _result("dc_sweep", True, "AC response present across the swept band.",
                       f"|H| range: [{mag.min():.3e}, {mag.max():.3e}]")

    # static (mirror/bias/reference) and structural classes: no meaningful sweep at this stage
    return _skip("dc_sweep", f"no input sweep for '{profile.mode}' class (verified via operating point)")


def _check_function(profile: CircuitProfile, simspace: dict) -> CheckResult:
    '''
    Stage 4 — Task-specific functional assertion.
    Check the behavior that defines the circuit family: voltage gain for transfer circuits,
    sustained oscillation for oscillators, a filtering ratio for filters, and a stable
    non-rail bias level for mirrors/references.
    '''
    if profile.mode == "transfer":
        vin, vout = simspace["vin"], simspace["vout"]
        max_gain = float(np.max(np.abs(np.gradient(vout, vin))))
        if max_gain < profile.gain_threshold:
            return _result("function", False,
                           f"Gain too low: max |dVout/dVin| = {max_gain:.3f} V/V (need ≥ {profile.gain_threshold}).",
                           "Circuit may be disconnected, mis-biased, or non-amplifying.")
        return _result("function", True, f"Functional: max |dVout/dVin| = {max_gain:.3f} V/V.")

    if profile.mode == "oscillator":
        # Count how often the output crosses its own mean — sustained oscillation needs several crossings.
        v = simspace["tvout"] - np.mean(simspace["tvout"])
        crossings = int(np.sum(np.diff(np.sign(v)) != 0))
        if crossings < OSC_MIN_CROSSINGS:
            return _result("function", False,
                           f"No sustained oscillation: only {crossings} mean-crossing(s) (need ≥ {OSC_MIN_CROSSINGS}).",
                           "Output moves but does not oscillate periodically over the transient window.")
        return _result("function", True, f"Sustained oscillation detected: {crossings} mean-crossings.")

    if profile.mode == "filter":
        # A real filter passes some frequencies and attenuates others — the magnitude span must be large enough.
        mag = simspace["mag"]
        nz = mag[mag > 0]
        ratio = float(nz.max() / nz.min()) if nz.size else 0.0
        if ratio < FILTER_MIN_RATIO:
            return _result("function", False,
                           f"Response too flat: max/min |H| = {ratio:.2f} (need ≥ {FILTER_MIN_RATIO}, ~3 dB).",
                           "Circuit does not selectively pass/attenuate frequencies.")
        return _result("function", True, f"Filtering confirmed: max/min |H| = {ratio:.2f}.")

    if profile.mode == "static":
        # Mirrors / references should hold the output at a stable intermediate level, not slam a rail.
        circuit = simspace["circuit"]
        vdd, _, _ = _classify_sources(circuit)
        try:
            vout = float(simspace["op"][simspace["out_node"]])
        except Exception as e:
            return _result("function", False, f"Could not read output bias: {e}", str(e))
        if not (0.1 * vdd < vout < 0.9 * vdd):
            return _result("function", False,
                           f"Output pinned to a rail: Vout = {vout:.3f}V (Vdd={vdd}V) — bias not established.",
                           "Reference/mirror should settle at a stable intermediate voltage.")
        return _result("function", True, f"Stable bias level: Vout = {vout:.3f}V (Vdd={vdd}V).")

    # structural classes: no automated analog functional check
    return _skip("function", f"no automated functional probe for '{profile.mode}' class")


def _check_waveform(profile: CircuitProfile, simspace: dict) -> CheckResult:
    '''
    Stage 5 — Waveform / shape sanity.
    A last shape check on the output: transfer curves need a clean, mostly-monotonic
    transition with adequate swing; oscillators must stay bounded and keep oscillating;
    filters need a finite, coherent roll-off. Static/structural classes have no waveform here.
    '''
    if profile.mode == "transfer":
        vout, vin, vdd = simspace["vout"], simspace["vin"], simspace["vdd"]
        swing = float(vout.max() - vout.min())
        if swing < SWING_FRACTION * vdd:
            return _result("waveform", False,
                           f"Output swing too small: {swing:.3f}V (need ≥ {SWING_FRACTION * vdd:.3f}V).",
                           f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V")
        # most of the curve should share one slope sign (a coherent inverting / non-inverting region)
        dv = np.gradient(vout, vin)
        dominant = np.sign(np.median(dv))
        mono = float(np.mean(np.sign(dv) == dominant))
        if mono < MONOTONIC_FRACTION:
            return _result("waveform", False,
                           "Transfer curve is not monotonic — no clear transition region.",
                           f"Monotonic fraction: {mono:.2f}")
        return _result("waveform", True, f"Waveform valid: swing={swing:.3f}V, monotonic fraction={mono:.2f}.")

    if profile.mode == "oscillator":
        # Oscillation must be bounded (not diverging) and still going in the back half of the window.
        tvout = simspace["tvout"]
        vdd = simspace.get("vdd")
        if vdd is None:
            vdd, _, _ = _classify_sources(simspace["circuit"])
        if not np.all(np.isfinite(tvout)) or np.max(np.abs(tvout)) > 10 * vdd:
            return _result("waveform", False, "Oscillation is unbounded / diverging.",
                           f"max|Vout| = {np.max(np.abs(tvout)):.3f}V vs Vdd={vdd}V")
        half = len(tvout) // 2
        first_swing = float(np.ptp(tvout[:half])) if half else 0.0
        last_swing = float(np.ptp(tvout[half:])) if half else 0.0
        if first_swing > 0 and last_swing < 0.25 * first_swing:
            return _result("waveform", False, "Oscillation decays away — not self-sustaining.",
                           f"swing first half={first_swing:.3f}V, second half={last_swing:.3f}V")
        return _result("waveform", True, f"Bounded, sustained oscillation (swing ≈ {last_swing:.3f}V).")

    if profile.mode == "filter":
        # Response should be finite and have a coherent roll-off (mostly one-directional in log-magnitude).
        mag = simspace["mag"]
        if not np.all(np.isfinite(mag)):
            return _result("waveform", False, "AC magnitude response contains non-finite values.",
                           "Check for unstable poles or a broken signal path.")
        logmag = np.log10(np.clip(mag, 1e-18, None))
        dm = np.diff(logmag)
        dominant = np.sign(np.median(dm)) if dm.size else 0
        trend = float(np.mean(np.sign(dm) == dominant)) if dm.size else 0.0
        if trend < MONOTONIC_FRACTION:
            return _result("waveform", False, "AC response has no coherent roll-off region.",
                           f"Dominant-trend fraction: {trend:.2f}")
        return _result("waveform", True, f"Coherent frequency response (trend fraction={trend:.2f}).")

    # static / structural: no waveform to inspect
    return _skip("waveform", f"no waveform check for '{profile.mode}' class")


def check_suite(script: str, task: dict) -> list[CheckResult]:
    '''
    Run the five check stages in order, short-circuiting on the first failure.
    The circuit profile (resolved from task['circuit_type']) decides which stimulus
    drives stages 3-5 and which assertions apply; simspace carries the circuit object
    and simulation results between stages.
    '''
    profile = profile_for(task)
    simspace = {}  # isolated namespace for the exec'd script + sim artifacts shared across stages
    results = []

    stages = (
        lambda: _check_requirement(script, task, profile, simspace),
        lambda: _check_op_point(profile, simspace),
        lambda: _check_dc_sweep(profile, simspace),
        lambda: _check_function(profile, simspace),
        lambda: _check_waveform(profile, simspace),
    )

    for run_stage in stages:
        result = run_stage()
        results.append(result)
        if not result.passed:   # skipped stages are passed=True, so they never short-circuit
            break

    return results


def diagnose(task: dict, script: str, failed_check: CheckResult) -> str:
    '''
   given a failed check, query llm for a diagnosis and repair plan
    '''
    context = [
        {"role": "system",
            "content": (
                    '''You are a PySpice circuit optimization agent, working in a team of three. You are given a circuit script
                    generated by the code generation agent in the previous design step that failed a validation check. Diagnose the
                    failure and provide a concise, actionable repair plan with specific changes to make to fix the issue.
                    Do not rewrite the full script. Output only the repair directive.'''
            )
        },
        {"role": "user", "content": f"*Failed Task* (type: {task['circuit_type']})\n {task['name']}: {task['description']}"},
        {"role": "user", "content": f"*Failing Script*:\n{script}"},
        {"role": "user", "content": f"*Failed Check*: {failed_check.stage}\n Summary: {failed_check.message}Details:\n {failed_check.details}" }
    ]
    
    # query OpenAI
    completion = client.chat.completions.create(model="gpt-4o", messages=context)
    response = completion.choices[0].message.content

    return response


def validate_and_optimize(attempt: int, task: dict, script: str) -> IterationRecord:
    '''
    Run the check suite. If a check fails, call the LLM for a repair plan; returns an IterationRecord for main and wise one.
    '''
    record = IterationRecord(attempt = attempt, task_type = task["circuit_type"], script = script, checks = [])

    record.checks = check_suite(script, task)

    failure = record.first_failure()
    if failure is None:
        record.accepted = True
        record.repair_plan = "No repairs needed. Script accepted."
    else:
        record.repair_plan = diagnose(task, script, failure)

    return record
