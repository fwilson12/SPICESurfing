from schema import IterationRecord
from optimizer import validate_and_optimize
from wise_one import curate
from code_generator import generate_script


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


def view_record_book(records: list[IterationRecord]) -> None:
    pass


def main(task: dict, max_attempts: int) -> None:
    
    record_book = circuit_time(task, max_attempts=10)

    # view_record_book(record_book)


if __name__ == '__main__':
    main()


