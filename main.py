import argparse
import json
from pathlib import Path

from schema import IterationRecord
from dataclasses import fields

from agents.optimizer import validate_and_optimize
from agents.wise_one import curate
from agents.code_generator import generate_script


def circuit_time(task: dict, max_attempts: int) -> list[IterationRecord]:


    SEM_additions = []
    record_book = []
    current_script = "" 
    current_repair_plan = ""
    for i in range(max_attempts):
        
        print(f"--------------------\n Attempt {i+1} of {max_attempts} for task: {task['name']}\n--------------------")
        
        ''' Script Generation '''
        print("Generating PySpice code...\n")
        script = generate_script(task, current_script, current_repair_plan)
        current_script = script # for next iteration's code generation context
        # debug
        print(script)


        ''' Validation and Simulations '''
        print("\nValidating...\n")
        IterRecord = validate_and_optimize(i + 1, task, script)
        current_repair_plan = IterRecord.repair_plan # for next iteration's code generation context
        record_book.append(IterRecord)
        # debug
        for check in IterRecord.checks:
            print([f"{stage.name}: {getattr(check, stage.name)}\n" for stage in fields(check)]) # essentially a k-v list comprehension with a custom DC instead of a dict

        ''' Self-Evolving Memory Additions '''
        print("\nCurating SEM additions...\n")
        SEM_addition = curate(IterRecord, task)
        SEM_additions.append(f'SEM Addition for iteration {i + 1}: {SEM_addition} \n\n')
        # debug
        print(f"New knowledge added to SEM: \n {SEM_addition}")

    print(SEM_additions)
    return record_book



def view_record_book(records: list[IterationRecord], task: dict) -> None:
   
    print(f"-----------------------------------------------\n RECORD BOOK: {task['name'].upper()}\n-----------------------------------------------\n")
    for record in records:
        print(f"Attempt #{record.attempt}  |  accepted: {record.accepted}  |  task: {record.task_type}")
        
        print("script:\n" + "\n".join(f"{line}" for line in record.script.splitlines())) # output is formatted like an actual python file
        print("\nchecks:")
        for check in record.checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"    [{status}] {check.stage}")
            print(f"    message: {check.message}")
            if check.details:
                print(f"    details: {check.details}")
        print(f"repair_plan: {record.repair_plan or '(none)'}\n")
       




def main(task: dict, max_attempts: int) -> None:
    
    record_book = circuit_time(task, max_attempts)

    view_record_book(record_book, task)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True, help='Path to task JSON file (e.g. tasks/easy_6.json)')
    parser.add_argument('--max_attempts', type=int, default=10)
    
    args = parser.parse_args()
    main(json.loads(Path(args.task).read_text()), args.max_attempts)


