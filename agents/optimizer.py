import ollama
import numpy as np
from schema import CheckResult, IterationRecord

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
            model_name = str(element.model).lower()
            is_pmos = "pmos" in model_name or model_name.startswith("p")

            try:
                vg = float(op[str(element.gate)])
                vs = float(op[str(element.source)])
                vd = float(op[str(element.drain)])
            except KeyError as e:
                failures.append(f"{name}: node {e} not found in op results")
                continue

            if is_pmos:
                vsg = vs - vg
                vsd = vs - vd
                if vsg < PMOS_VTH:
                    failures.append(f"{name} (PMOS): Vsg={vsg:.3f}V < Vth={PMOS_VTH}V — not in saturation")
                elif vsd < vsg - PMOS_VTH:
                    failures.append(f"{name} (PMOS): Vsd={vsd:.3f}V < Vsg-Vth={vsg - PMOS_VTH:.3f}V — not in saturation")
            else:
                vgs = vg - vs
                vds = vd - vs
                if vgs < NMOS_VTH:
                    failures.append(f"{name} (NMOS): Vgs={vgs:.3f}V < Vth={NMOS_VTH}V — not in saturation")
                elif vds < vgs - NMOS_VTH:
                    failures.append(f"{name} (NMOS): Vds={vds:.3f}V < Vgs-Vth={vgs - NMOS_VTH:.3f}V — not in saturation")

        if failures:
            results.append(CheckResult(
                stage="op_point", passed=False,
                message="One or more MOSFETs not in saturation.",
                details="\n".join(failures)
            ))
            return results

        results.append(CheckResult(
            stage="op_point", passed=True,
            message="All MOSFETs biased in saturation.",
            details=""
        ))

    except Exception as e:
        results.append(CheckResult(
            stage="op_point", passed=False,
            message=f"Operating point simulation failed: {e}",
            details=str(e)
        ))
        return results

    ''' Stage 3: DC sweep to detect rail-stuck output '''
    try:
        # detect supply voltage from circuit (look for VoltageSource named 'dd' or '1')
        vdd = 5.0  # default fallback
        for el in circuit.elements:
            if type(el).__name__ == "VoltageSource":
                try:
                    v = float(el.dc_value)
                    if v > 1.0:
                        vdd = v
                        break
                except Exception:
                    pass

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        dc = simulator.dc(Vin=slice(0, vdd, vdd / 50))
        simspace["dc"] = dc
        simspace["vdd"] = vdd

        vout = np.array(dc["Vout"], dtype=float)

        # rail-stuck: std dev of Vout relative to Vdd is tiny
        if np.std(vout) / vdd < 0.02:
            pinned = "Vdd" if np.mean(vout) > vdd * 0.8 else "GND"
            results.append(CheckResult(
                stage="dc_sweep", passed=False,
                message=f"Vout is rail-stuck near {pinned} across the entire sweep.",
                details=f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V, Vdd={vdd}V"
            ))
            return results

        results.append(CheckResult(
            stage="dc_sweep", passed=True,
            message="Vout responds to Vin sweep — not rail-stuck.",
            details=f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V"
        ))

    except Exception as e:
        results.append(CheckResult(
            stage="dc_sweep", passed=False,
            message=f"DC sweep failed: {e}",
            details=str(e)
        ))
        return results

    ''' Stage 4: function check — gain threshold '''
    try:
        dc = simspace["dc"]
        vdd = simspace["vdd"]

        vin  = np.array(dc["Vin"],  dtype=float)
        vout = np.array(dc["Vout"], dtype=float)

        # numerical derivative |dVout/dVin|
        gain = np.abs(np.gradient(vout, vin))
        max_gain = np.max(gain)

        # minimum meaningful gain — at least 0.5 V/V (catches unity-gain buffers too)
        GAIN_THRESHOLD = 0.5

        if max_gain < GAIN_THRESHOLD:
            results.append(CheckResult(
                stage="function", passed=False,
                message=f"Gain too low: max |dVout/dVin| = {max_gain:.3f} V/V (threshold: {GAIN_THRESHOLD}).",
                details=f"Circuit may be disconnected or non-functional."
            ))
            return results

        results.append(CheckResult(
            stage="function", passed=True,
            message=f"Circuit functional: max |dVout/dVin| = {max_gain:.3f} V/V.",
            details=""
        ))

    except Exception as e:
        results.append(CheckResult(
            stage="function", passed=False,
            message=f"Function check failed: {e}",
            details=str(e)
        ))
        return results

    ''' Stage 5: waveform shape check — valid transition with monotonic region '''
    try:
        vout = np.array(simspace["dc"]["Vout"], dtype=float)
        vdd  = simspace["vdd"]

        # check for a valid transition: Vout must span at least 60% of Vdd
        swing = vout.max() - vout.min()
        if swing < 0.6 * vdd:
            results.append(CheckResult(
                stage="waveform", passed=False,
                message=f"Output swing too small: {swing:.3f}V (need ≥ {0.6 * vdd:.3f}V).",
                details=f"Vout range: [{vout.min():.3f}, {vout.max():.3f}]V"
            ))
            return results

        # check for a monotonic region: at least half of dVout/dVin points
        # should have the same sign (consistently inverting or non-inverting)
        vin  = np.array(simspace["dc"]["Vin"], dtype=float)
        dv   = np.gradient(vout, vin)
        dominant_sign = np.sign(np.median(dv))
        monotonic_fraction = np.mean(np.sign(dv) == dominant_sign)

        if monotonic_fraction < 0.5:
            results.append(CheckResult(
                stage="waveform", passed=False,
                message="Output curve is not monotonic — no clear inverting or non-inverting region.",
                details=f"Monotonic fraction: {monotonic_fraction:.2f}"
            ))
            return results

        results.append(CheckResult(
            stage="waveform", passed=True,
            message=f"Waveform valid: swing={swing:.3f}V, monotonic fraction={monotonic_fraction:.2f}.",
            details=""
        ))

    except Exception as e:
        results.append(CheckResult(
            stage="waveform", passed=False,
            message=f"Waveform check failed: {e}",
            details=str(e)
        ))

    return results


def diagnose(task: dict, script: str, failed_check: CheckResult) -> str:
    '''
   given a failed check, query llm for a diagnosis and repair plan
    '''
    context = [
        {"role": "system",  
            "content": (
                    '''You are a PySpice circuit optimization agent. You are given a circuit script 
                    that failed a validation check. Diagnose the failure and provide a concise, 
                    actionable repair plan with specific changes to make to fix the issue. 
                    Do not rewrite the full script. Output only the repair directive.'''
            )
        },
        {"role": "user", "content": f"*Failed Task* (type: {task['circuit_type']})\n {task['name']}: {task['description']}"},
        {"role": "user", "content": f"*Failing Script*:\n{script}"},
        {"role": "user", "content": f"*Failed Check*: {failed_check.stage}\n Summary: {failed_check.message}Details:\n {failed_check.details}" }
    ]
    response = ollama.chat(model="llama3.2", messages=context)
    return response["message"]["content"]


def validate_and_optimize(attempt: int, task: dict, script: str) -> IterationRecord:
    '''
    Run the check suite. If a check fails, call the LLM for a repair plan; returns an IterationRecord for main and wise one.
    '''
    record = IterationRecord(attempt = attempt, task_type = task["circuit_type"], script = script, checks = [])

    record.checks = check_suite(script, task)

    failure = record.first_failure()
    if failure is None:
        record.accepted = True
    else:
        record.repair_plan = diagnose(task, script, failure)

    return record
