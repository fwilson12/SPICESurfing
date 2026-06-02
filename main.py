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
    for i in range(max_attempts):
        
        script = generate_script(task)

        IterRecord = validate_and_optimize(i, task, script)
        record_book.append(IterRecord)
    
        SEM_addition = curate(IterRecord, task)
        SEM_additions.append(f'SEM Addition for iteration {i}: {SEM_addition} \n\n')

    print(SEM_additions)
    return record_book

# implement later
def view_record_book(records: list[IterationRecord]) -> None:
    pass


def main(task: dict, max_attempts: int) -> None:
    
    record_book = circuit_time(task, max_attempts)

    # view_record_book(record_book)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True, help='Path to task JSON file (e.g. tasks/easy_6.json)')
    parser.add_argument('--max-attempts', type=int, default=10)
    
    args = parser.parse_args()
    main(json.loads(Path(args.task).read_text()), args.max_attempts)


