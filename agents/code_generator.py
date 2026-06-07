import ollama
import os
import re

from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key= OPENAI_API_KEY)


BENCHMARK_FILE_PATH = "tasks"
SEM_FILE_PATH = "SEM"

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


def generate_script(task: dict, old_script: str, repair_plan: str) -> str:

    SEM_notes = fetch_SEM(task["circuit_type"])
    general_rules = SEM_notes[0]["content"] if len(SEM_notes) > 0 else "No general rules found in SEM."
    task_specific_rules = SEM_notes[1]["content"] if len(SEM_notes) > 1 else "No task-specific rules in SEM currently. You got this!"

    context = [
        {
            "role": "system", 
            "content": """You are a PySpice code generating agent, working in a team of three. Your task is to use the user's task prompt
                       and create a circuit with PySpice code that correctly represents and behaves like the described circuit. You are given access to the previously generated script,
                       along with a repair plan curated by the optimization agent, who reviews your work. You are also given access
                       to relevant notes and information that are part of your evolving memory bank, which include general notes and additionally task-specific 
                       notes related to the type of circuit you'll be designing, if they exist. Conform to the PySpice API and python syntax in your response. Generate
                       the complete file, naming the main circuit 'circuit' in the file's namespace for simulation purposes in later design steps. Your response must contain
                       nothing but complete full python file."""
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
        },
        {
            "role": "user",
            "content": f'Previously generated script:\n{old_script}'
        },
        {
            "role": "user",
            "content": f'Repair plan from the optimization agent:\n{repair_plan}'
        }
    ]


    completion = client.chat.completions.create(model="gpt-5.1", messages=context)
    text = completion.choices[0].message.content
    return extract_script(text)
