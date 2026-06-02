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
        results.append(CheckResult(stage = "requirement", passed = False, message = f"SyntaxError: {e}", details = str(e)))
        return results
    
    except Exception as e:
        results.append(CheckResult(stage = "requirement", passed = False, message = f"Script execution error: {e}", details = str(e)))
        return results

    # script must define a top-level variable named 'circuit'
    circuit = simspace.get("circuit")
    if circuit is None:
        results.append(CheckResult(stage = "requirement", passed = False, message = "Script did not define a 'circuit' variable.", details = "Ensure the PySpice Circuit object is assigned to a variable named 'circuit'."))
        return results



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
