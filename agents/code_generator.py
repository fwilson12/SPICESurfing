# instantiate  model 
# create context list of dicts
# add basic info (
#                 "role": "system", 
#                 "content": """you are PySpice code generating agent, part of a team of three, yada yada, you have acess to the
#                               SEM/Design playbook, given a certain task type query the SEM for relevant heuristics/conventions"""
#                 )
# add task ("role": "user", "content": task(includes type)) to context
# get response (tool call to SEM)
# skim SEM file for notes on task
# append notes to context (role: notes, content: notes.content)
# get response again
# send script to optimization agent


import ollama
import PySpice
import os

BENCHMARK_FILE_PATH = "../tasks"
SEM_FILE_PATH = "../SEM"

def fetch_SEM(task_type: str) -> list[dict]:
    '''fetch general rules and task-specific heuristics if a task type file is found'''
    res = []
    
    # always get general notes
    with open(os.path.join(SEM_FILE_PATH, "general.md")) as f:
        general = {"role": "notes", "content": f.read()}
        res.append(general)
    
    # if there are existing notes specific to this task type, get those too
    task_specific = os.path.join(SEM_FILE_PATH, f"/{task_type}.md")
    if os.path.exists(task_specific):
        with open(task_specific) as f:
            specific = {"role": "notes", "content": f.read()}
            res.append(specific)
    
    return res

def generate_script(task: dict, SEM_notes: list[str], observations: list[dict]) -> str:

    SEM_notes = fetch_SEM(task["circuit_type"])