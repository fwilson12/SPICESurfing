#  code_generator -> optimizer -> wise_one until accepted or max attempts reached 
#
# def run(task, max_attempts)
#
#     # initialize comprehensive record of iterations 
#     iteration_log = []         

#     for attempt in range(1, max_attempts + 1):
#
#         memory-guided planning: 
#         retrieve relevant SEM entries for task["type"]
#         
#
#         code generation 
#         script = generate_script(task, SEM notes, iteration_log)
#
#         optimizer
#         record = validate_and_optimize(attempt, task, script)
#         iteration_log.append(record)
#
#         wise guy
#         if new actionable evidence found in record:
#              curate(task, record)          # wise_one writes to SEM
#
#         stop criterion 
#         if record.accepted:
#           return record
#
#     budget exhausted
#     return None



from schema import IterationRecord, CheckResult
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
    
    record_book = circuit_time()

    # view_record_book(record_book)


if __name__ == '__main__':
    main()

    
