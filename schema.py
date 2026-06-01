'''
schema.py — shared data structures for check results passed between optimizer and wise one

Checks are sourced from AnalogAgent paper
'''

from dataclasses import dataclass, field
from typing import Optional

# Stages in the optimizer check pipeline (in order)
CHECK_STAGES = [
    "requirement",   # topology/node validation
    "op_point",      # ngspice op + Vgs>Vth etc.
    "dc_sweep",      # rail-stuck detection
    "function",      # gain threshold check
    "waveform",      # curve shape / monotonicity
]

@dataclass
class CheckResult:
    '''
    Result of a single check in the optimizer pipeline

    '''

    stage: str  # one of CHECK_STAGES
    passed: bool
    message: str  # human/LLM-readable summary
    details: str  # sim output or error trace 

@dataclass
class IterationRecord:
    '''
    Comprehensive record of one iteration of the main loop, passed to wise one for curation
    
    '''

    attempt: int # iteration tally in each independent run, starting at 1
    task_type: str # circuit type string, used to route SEM task_types lookup
    script: str   # the PySpice script that was evaluated
    checks: list[CheckResult] # a list of each of the five CheckResults from optimizer pipeline 
    accepted: bool = False 

    # returns first failed check if any, else None
    def first_failure(self) -> Optional[CheckResult]:
        for c in self.checks:
            if not c.passed:
                return c
        return None


    def failure_stage(self) -> Optional[str]:
        f = self.first_failure()
        return f.stage if f else None
