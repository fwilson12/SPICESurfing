from schema import CheckResult, IterationRecord
import ollama
import os


def curate(iteration: IterationRecord, task: dict) -> None:
    ''' 
    Given a complete record of one optimization cycle, agent elects to append to the SEM based on generalizable patterns/heuristics that
    may be applicable to future iterations. Returns None, but may write to SEM directory
    '''

    optimization_results = [f"Stage: {check.stage} | Passed: {check.passed} | Summary: {check.message} | Details: {check.details} \n" for check in iteration.checks]

    context = [
        {"role": "system", "content": 
                            '''PROMPT PLACEHOLDER    Include specific details about what to include in response so '''
        },
        {"role": "user", "content": f"This is a circuit that {"passed" if iteration.accepted else "failed"} on iteration {iteration.attempt} for a {task["name"]} ({task["description"]}), which is of type {task["circuit_type"]}"},
        {"role": "user", "content": f"PySpice Script: {iteration.script}"},
        {"role": "user", "content":f"Record from optimization stage: {str(optimization_results)}"}, 
        {"role": "user", "content": f"Repair plan from Optimization agent {iteration.repair_plan}"}
    ]

    response = ollama.chat(model="qwen3.5:9b", messages=context)
    text = response["messge"]["context"]
    file_path = "?"




def write_to_SEM(file_path: str, knowledge: str) -> None:
    
    if not os.path.exists(f"SEM/{file_path}"):
        os.mkdir(f"SEM/{file_path}")