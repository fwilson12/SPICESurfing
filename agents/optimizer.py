


instantiate ollama model 
create context list of dicts
add basic info (
                "role": "system", 
                "content": """you are PySpice code optimization agent, part of a team of three, yada yada, you are given
                a pyspice script and must validate first that it compiles and can be simulated, then run a series of simulations to to record
                the resultant circuit behavior, then confirm the behavior is consistent with the task. also check topology and what not. """
                )
add task ("role": "user", "content": task(includes type)) to context
add script ("role": "user", "content": script from code_geneerator) to context
while optimizing:
    try:
        run script and simulate
        for sim_res in sims:
            context.append({"role": "simulation", "content": sim_res})
        get response (tool call to SEM)
    except Exception as e:
