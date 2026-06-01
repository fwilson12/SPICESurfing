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
        general = {"role": "user", "content": f.read()}
        res.append(general)
    
    # if there are existing notes specific to this task type, get those too
    task_specific = os.path.join(SEM_FILE_PATH, f"/{task_type}.md")
    if os.path.exists(task_specific):
        with open(task_specific) as f:
            specific = {"role": "user", "content": f.read()}
            res.append(specific)
    
    return res

def generate_script(task: dict, observations: list[dict]) -> str:

    SEM_notes = fetch_SEM(task["type"])
    general_rules = SEM_notes[0]["content"] if len(SEM_notes) > 0 else "No general rules found in SEM."
    task_specific_rules = SEM_notes[1]["content"] if len(SEM_notes) > 1 else "No task-specific rules found in SEM currently."


    context = [
        {
            "role": "system", 
            "content": '''
                        you are PySpice code generating agent, part of a team of three, yada yada, you have access to the
                        SEM/Design playbook, given a certain task type query the SEM for relevant heuristics/conventions and any past 
                        observations from the current run, then generate a PySpice script that meets the task requirements as best you can.
                        '''
        },
        {
            "role": "user", 
            "content": "General rules from the SEM : " + general_rules
        } ,
        {
            "role": "user", 
            "content": f'Task-specific rules from the SEM (type {task["type"]}): {task_specific_rules}'
        },
        {
            "role": "user", 
            "content": f'Create a PySpice script for a {task["name"]}: {task["description"]}.'
        },
    ]

