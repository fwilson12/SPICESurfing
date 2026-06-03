import argparse
import json
from pathlib import Path

from schema import IterationRecord
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
        print(script)


        ''' Validation and Simulations '''
        print("\nValidating...\n")
        IterRecord = validate_and_optimize(i, task, script)
        current_repair_plan = IterRecord.repair_plan # for next iteration's code generation context
        record_book.append(IterRecord)
        print([f"{attr}: {content}\n" for attr, content in IterationRecord.items()])

        ''' Self-Evolving Memory Additions '''
        print("\nCurating SEM additions...\n")
        SEM_addition = curate(IterRecord, task)
        SEM_additions.append(f'SEM Addition for iteration {i}: {SEM_addition} \n\n')
        print(f"New knowledge added to SEM: \n {SEM_addition}")

    print(SEM_additions)
    return record_book



# implement later
def view_record_book(records: list[IterationRecord], task: dict) -> None:
    print(f"-----------------------------------------------\n RECORD BOOK: {task['name'].upper()}\n-----------------------------------------------\n")
    
    for record in records:
        print([f"{attr}: {content}\n" for attr, content in record.items()])




def main(task: dict, max_attempts: int) -> None:
    
    record_book = circuit_time(task, max_attempts)

    view_record_book(record_book, task)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True, help='Path to task JSON file (e.g. tasks/easy_6.json)')
    parser.add_argument('--max_attempts', type=int, default=10)
    
    args = parser.parse_args()
    main(json.loads(Path(args.task).read_text()), args.max_attempts)


