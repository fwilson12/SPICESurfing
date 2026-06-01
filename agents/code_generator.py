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


