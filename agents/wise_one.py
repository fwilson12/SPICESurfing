from dotenv import load_dotenv

from schema import CheckResult, IterationRecord
import ollama
import os
import re

from pathlib import Path


from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)



SEM_FILE_PATH = Path(__file__).resolve().parent.parent / "SEM"


def curate(iteration: IterationRecord, task: dict) -> str:
    ''' 
    Given a complete record of one optimization cycle, agent elects to append to the SEM based on generalizable patterns/heuristics that
    may be applicable to future iterations. Returns None, but may write to SEM directory
    '''

    optimization_results = [f"Stage: {check.stage} | Passed: {check.passed} | Summary: {check.message} | Details: {check.details} \n" for check in iteration.checks]

    # avoiding redundant entries to avoid context bloating
    with open(os.path.join(SEM_FILE_PATH, "general.md"), encoding="utf-8") as f:
        existing_general_notes = f.read()
   
    # get task-specific notes if they exist 
    existing_task_notes = "No existing notes for this task type."
    if os.path.exists(os.path.join(SEM_FILE_PATH, "task_types", f"{task['circuit_type']}.md")):
        with open(os.path.join(SEM_FILE_PATH, "task_types", f"{task['circuit_type']}.md"), encoding="utf-8") as f:
            existing_task_notes = f.read()    
    
    

    context = [
        {"role": "system", "content": 
                           f"""You are the knowledge curator in a PySpice circuit design pipeline. After each design iteration,
                            you review the script, validation results, and repair plan to decide whether any generalizable knowledge
                            is worth storing in the persistent memory bank (SEM).

                            ADMISSION CRITERIA | only write a rule if it meets at least one of:
                            1. A PySpice API or syntax error that would affect any script of this type, not just this one
                            2. A circuit convention or topology requirement that is non-obvious and violated here
                            3. A failure pattern that is likely to recur on similar tasks
                            4. A successful design pattern that is likely to be applicable in future iterations

                            DO NOT write rules that are:
                            - Already present in the existing SEM content provided to you by the user
                            - Specific to this script's particular parameter values
                            - Restatements of basic Python or obvious PySpice usage
                            - Uncertain inferences; if you are not confident it generalizes, use [NO WRITE]
                            - Describe symptoms of an issue while omitting the root cause

                            WHEN IN DOUBT, use [NO WRITE]. A sparse SEM with high-quality entries is better than a bloated one.
                            Again: DO NOT add repeat entries that contain the same instructions or insights as existing SEM content,
                            even if they are worded differently. 
                            
                            Ask yourself: what single design principle, if known before, would have prevented the 
                            failures in this run? Write that.

                            OUTPUT FORMAT:
                            - Each rule must be a single atomic fact on one line
                            - To write to the general file: [WRITE TO: general.md] followed by entries using format `- [TAG] rule` (tags: API, NODE, SYNTAX, SIM, CONV)
                            - To write to the circuit-type file: [WRITE TO: {task['circuit_type']}.md] followed by entries in the same format
                            - To skip writing entirely: [NO WRITE]"""
        },
        {"role": "user", "content": f"This is a circuit that {'passed' if iteration.accepted else 'failed'} on iteration {iteration.attempt} for a {task['name']} ({task['description']}), which is of type {task['circuit_type']}"},
        {"role": "user", "content": f"PySpice Script: {iteration.script}"},
        {"role": "user", "content":f"Record from optimization stage: {str(optimization_results)}"}, 
        {"role": "user", "content": f"Repair plan from Optimization agent {iteration.repair_plan}"},
       
        # avoid duplicate entries to SEM
        {"role": "user", "content": f"[Existing general.md]\n{existing_general_notes}"},
        {"role": "user", "content": f"[Existing {task['circuit_type']}.md]\n{existing_task_notes}"}
    ]

    completion = client.chat.completions.create(model="gpt-5.1", messages=context)
    text = completion.choices[0].message.content
    


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
        name = os.path.basename(filepath.strip()) # gets ultimate file from the filepath, helps with errant paths
        if name == "general.md":
            dest = os.path.join(SEM_FILE_PATH, "general.md")
        else:
            dest = os.path.join(SEM_FILE_PATH, "task_types", name)

        with open(dest, "a", encoding="utf-8") as f:  # creates the file if it doesn't exist yet
            f.write(content + "\n\n")

    