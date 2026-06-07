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
    current_repair_plan = ""
    for i in range(max_attempts):
        
        print(f"\n{'=' * 60}\n  ATTEMPT {i + 1} OF {max_attempts}  |  {task['name']}\n{'=' * 60}")

        ''' Script Generation '''
        print("\n--- Generating PySpice code ---\n")
        script = generate_script(task, current_repair_plan)
        current_script = script # for next iteration's code generation context
        # debug
        print(script)


        ''' Validation and Simulations '''
        print("\n--- Validating ---\n")
        IterRecord = validate_and_optimize(i + 1, task, script)
        current_repair_plan = IterRecord.repair_plan # for next iteration's code generation context
        record_book.append(IterRecord)
        for check in IterRecord.checks:
            # SKIP = stage not applicable to this circuit class; otherwise PASS/FAIL
            status = "SKIP" if not check.applicable else ("PASS" if check.passed else "FAIL")
            print(f"  [{status}] {check.stage:<12} {check.message}")

        if IterRecord.accepted:
            print(f"\n--- ACCEPTED on attempt {i + 1} ---\n")
            print(f"---FINAL SCRIPT ({task['name']})---:\n\n{script}\n")
            break

        print(f"\n  Result: REJECTED (failed at '{IterRecord.failure_stage()}')")

        ''' Self-Evolving Memory Additions '''
        print("\n--- Curating SEM additions ---\n")
        SEM_addition = curate(IterRecord, task)
        SEM_additions.append(f'SEM Addition for iteration {i + 1}: {SEM_addition} \n\n')
        print(f"New knowledge added to SEM:\n{SEM_addition}")

    if record_book and not record_book[-1].accepted:
        print(f"\n{'=' * 60}\n  NOT ACCEPTED after {len(record_book)} attempt(s)\n{'=' * 60}")

    return record_book



def view_record_book(records: list[IterationRecord], task: dict) -> None:
   
    print(f"\n{'=' * 60}\n  RECORD BOOK: {task['name'].upper()}\n{'=' * 60}")
    for record in records:
        print(f"\n--- Attempt #{record.attempt}  |  accepted: {record.accepted}  |  task: {record.task_type} ---")

        print("\nscript:\n" + "\n".join(f"{line}" for line in record.script.splitlines())) # output is formatted like an actual python file
        print("\nchecks:")
        for check in record.checks:
            # SKIP = stage not applicable to this circuit class; otherwise PASS/FAIL
            status = "SKIP" if not check.applicable else ("PASS" if check.passed else "FAIL")
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


