#  code_generator -> optimizer -> wise_one until accepted or max attempts reached 
#
# def run(task, max_attempts)
#
#     # initialize comprehensive record of iterations 
#     observations = []         

#     for attempt in range(1, max_attempts + 1):
#
#         memory-guided planning: 
#         retrieve relevant SEM entries for task["type"]
#         
#
#         code generation 
#         script = generate_script(task, SEM notes, observations)
#
#         optimizer
#         record = validate_and_optimize(attempt, task, script)
#         observations.append(record)
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
