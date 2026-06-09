from pathlib import Path
import ollama
import os
import re



SEM_FILE_PATH = Path(__file__).resolve().parent.parent / "SEM"

def fetch_SEM(task_type: str) -> list[dict]:    
    '''fetch general rules and task-specific heuristics if a task type file is found'''
    res = []
    
    # always get general notes
    with open(os.path.join(SEM_FILE_PATH, "general.md"), encoding="utf-8") as f:
        general = {"role": "user", "content": f.read()}
        res.append(general)
    
    # if there are existing notes specific to this task type, get those too
    task_specific = os.path.join(SEM_FILE_PATH, "task_types", f"{task_type}.md")
    if os.path.exists(task_specific):
        with open(task_specific, encoding="utf-8") as f:
            specific = {"role": "user", "content": f.read()}
            res.append(specific)
    
    return res


def extract_script(script: str) -> str:
    ''' gets rid of python script markdown in script string returned by LLMS w/ regex'''
    match = re.search(r'```python\s*(.*?)```', script, re.DOTALL)
    if match:
        return match.group(1).strip()
    return script.strip()


def generate_script(task: dict, repair_plan: str, netlist: str = "no previous netlist") -> str:

    SEM_notes = fetch_SEM(task["circuit_type"])
    general_rules = SEM_notes[0]["content"] if len(SEM_notes) > 0 else "No general rules found in SEM."
    task_specific_rules = SEM_notes[1]["content"] if len(SEM_notes) > 1 else "No task-specific rules in SEM currently. You got this!"

    context = [
        {
            "role": "system", 
            "content": """You are a PySpice circuit code generation agent. Your job is to produce a single, complete, 
                        executable Python file that implements the described analog circuit using PySpice and ngspice.
                        Your code is validated and tested by a separate optimization agent, which runs a series of checks and 
                        simulations on your code and provides you with a repair plan to address any issues that arise. You will 
                        use this feedback to iteratively improve your code until it passes all checks and is accepted by the 
                        optimization agent on every attempt but your first. You are also given the netlist form of the script from 
                        your previous attempt for reference (unless this is your first attempt).
                        
                        In your code:

                        HARD REQUIREMENTS — the validation pipeline depends on these:
                        - The top-level PySpice Circuit object MUST be assigned to a variable named exactly `circuit`
                        - The output node MUST be named `Vout`
                        - The primary DC input voltage source MUST be created as `circuit.V('in', 'Vin', circuit.gnd, ...)` so ngspice names it `vin` for sweeps
                        - The supply rail MUST be named `Vdd` (circuit.V('dd', 'Vdd', circuit.gnd, ...))
                        - `circuit.gnd` must be referenced so ngspice sees a ground node named `0`
                        PYSPICE CONVENTIONS:
                        - Use `circuit.M(name, drain, gate, source, bulk, model=...)` for MOSFETs — NOT circuit.MOSFET()
                        - `lambda` is a Python keyword — use `lambda_=` in model definitions
                        - Units: use `@u_V`, `@u_kOhm`, `@u_uF` etc. from `from PySpice.Unit import *`
                        - PMOS bulk must tie to Vdd; NMOS bulk must tie to ground
                        - Every node must have a DC path to ground — no floating nodes
                        - Do not call plt.show() or include any display/plot code
                        OUTPUT: raw Python only — no markdown, no code fences, no explanation."""
        },
        {
            "role": "user", 
            "content": "General rules from the SEM : " + general_rules
        } ,
        {
            "role": "user", 
            "content": f'Task-specific rules from the SEM (Circuit Type: {task["circuit_type"]}): {task_specific_rules}'
        },
        {
            "role": "user", 
            "content": f'Create a PySpice script for a {task["name"]}: {task["description"]}.' # Ex:  "Create a script for a CMOS Inverter (NOT Gate): "Uses one NMOS and one PMOS transistor connected in series between Vdd and ground. Input is connected to both gates; output is taken from the connection between the transistors. When the input is high, NMOS conducts, pulling output low; when input is low, PMOS conducts, pulling output high.","
        }
    ]

    if repair_plan:
        context.append({"role": "user", 
                        "content": f"The validation agent identified this failure and repair directive — address it specifically:\n{repair_plan}"})


    completion = ollama.chat(model="qwen3.5:9b", messages=context)
    script = completion.message.content
    return extract_script(script)

    