# instantiate model 
# create context list of dicts
# add basic info (
#                 "role": "system", 
#                 "content": """you are PySpice code optimization agent, part of a team of three, yada yada, you are given
#                 a pyspice script and must validate first that it compiles and can be simulated, then run a series of simulations to to record
#                 the resultant circuit behavior, then confirm the behavior is consistent with the task. also check topology and what not. """
#                 )
# add task ("role": "user", "content": task(includes type)) to context
# add script ("role": "user", "content": script from code_geneerator) to context
# write script to temp file, add relevant tests at bottom of file:
#   do something like:
#       try:
#           sim results = circuit.transient() or .ac() or whatever 
#           optimizer.context.append({"role": "simulation", "content": results})
#       except Exception as e:
#           optimizer.context.append({"role": "error", "content": str(e)})
#      
# 
# run script
# get response with either error or results        
# proposes changes, sends info to wise one, context from simulation suite gets fed back to the generator upon next iteration
