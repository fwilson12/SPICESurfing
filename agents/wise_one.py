from schema import CheckResult, IterationRecord
import ollama
import os
import re

def curate(iteration: IterationRecord, task: dict) -> str:
    ''' 
    Given a complete record of one optimization cycle, agent elects to append to the SEM based on generalizable patterns/heuristics that
    may be applicable to future iterations. Returns None, but may write to SEM directory
    '''

    optimization_results = [f"Stage: {check.stage} | Passed: {check.passed} | Summary: {check.message} | Details: {check.details} \n" for check in iteration.checks]

    context = [
        {"role": "system", "content": 
                            '''You are an agent in a team of three that are tasked with generating correct and functional circuits with PySpice. Your role
                            is the knowledge curator; after the coding agent generates a script and the optimization and validation agent tests it and runs simulations,
                            your job is to evaluate the assigned task, the script that was generated, the list of checks and their results, and the repair plan drafted by
                            the optimization agent. You will then look for common design flaws, syntax/api errors, or other generalizable patterns, and append them to an
                            evolving memory bank, in a general syntax/PySpice convention/node structuring file, and/or a task-specific file, which should contain useful
                            information for future iterations regarding the design of a specific circuit type. In your response, format each addition like so:
                            -   To write to the general syntax/structure file, precede your addition with the tag [WRITE TO: general.md]
                            -   To write to a task specific file, precede your addition with [WRITE TO: task_types\(circuit_type)]. (circuit_type) will be provided to you in the next message.
                            If you don't see any immidiately helpful information that is worth storing away, your response should contain only: [NO WRITE]'''
        },
        {"role": "user", "content": f"This is a circuit that {"passed" if iteration.accepted else "failed"} on iteration {iteration.attempt} for a {task["name"]} ({task["description"]}), which is of type {task["circuit_type"]}"},
        {"role": "user", "content": f"PySpice Script: {iteration.script}"},
        {"role": "user", "content":f"Record from optimization stage: {str(optimization_results)}"}, 
        {"role": "user", "content": f"Repair plan from Optimization agent {iteration.repair_plan}"}
    ]

    response = ollama.chat(model="qwen3.5:9b", messages=context)
    text = response["messge"]["context"]
    SEM_updates = {} # filepath (str): text to add (str)


    # regex mess incoming | Want filepath substring in tag: "[WRITE TO: {filepath stringaling}]" and all subsequent text in block, plus additional block if wise one wants to add to general.md and a task_type md
    # Make wise one return [NO WRITE] if he doesn't feel the need to append to SEM, this is more for debugging  
    if "[NO WRITE]" in text:
        return
    
    matches = re.findall(r'\[WRITE TO:\s*([^\]]+)\](.*?)(?=\[WRITE TO:|$)', text, re.DOTALL) # shoutout to claude dude what 
    SEM_updates = {filepath.strip(): content.strip() for filepath, content in matches}
    write_to_SEM(SEM_updates)
    
    return text # for debugging




def write_to_SEM(knowledge: dict) -> None:
    ''' appends content to files specified by the wise one agent, or initialiazes a task_file if it doesn't exist yet '''    
    
    for filepath, content in knowledge.items():
        with open(os.path.join("../SEM", filepath), "a") as f: # creates file in task_types subdir if it doesn't exist already
            f.write(content + "\n\n")

    
