from schema.py import CheckResult, IterationRecord

def curate(iteration: IterationRecord, task: dict) -> None:
    ''' 
    Given a complete record of one optimization cycle, agent elects to append to the SEM based on generalizable patterns/heuristics that
    may be applicable to future iterations. Returns None, but may write to SEM directory
    '''

    optimization_results = [f"Stage: {check.stage} | Passed: {check.passed} | Summary: {check.message} | Details: {check.details} \n" for check in iteration.checks]

    context = [
        {"role": "system", "content": "PROMPT PLACEHOLDER"},
        {"role": "user", "content": f"This is a circuit that {"passed" if iteration.accepted else "failed"} on iteration {iteration.attempt} for a {task["name"]} ({task["description"]}), which is of type {task["circuit_type"]}"},
        {"role": "user", "content": f"PySpice Script: {iteration.script}"},
        {"role": "user", "content":f"Record from optimization stage: {str(optimization_results)}"}, 
        {"role": "user", "content": f"Repair plan from Optimization agent {iteration.repair_plan}"}

    ]