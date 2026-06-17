'''
Shared data structures for check results passed between optimizer and wise one

Checks are sourced from AnalogAgent paper
'''

from dataclasses import dataclass, field
from typing import Optional

# Stages in the optimizer check pipeline (in order).
CHECK_STAGES = [
    "requirement",   # script compiles; circuit, ground, output node and devices present
    "op_point",      # DC operating point converges (+ MOSFET saturation for analog classes)
    "dc_sweep",      # output responds to its natural stimulus (DC sweep / transient / AC)
    "function",      # task-specific functional assertion (gain / oscillation / filtering / bias)
    "waveform",      # output shape sanity (swing, monotonicity, bounded & sustained)
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
    applicable: bool = True  # False when the stage was skipped as not meaningful for this circuit class
                             # (recorded as passed=True so it never counts as a failure)

@dataclass
class IterationRecord:
    '''
    Comprehensive record of one iteration of the main loop, passed to wise one for curation
    '''
    attempt: int # iteration tally in each independent run, starting at 1
    task_type: str # circuit type string, used to route SEM task_types lookup
    script: str   # the PySpice script that was evaluated
    checks: list[CheckResult] # a list of each of the five CheckResults from optimizer pipeline 
    netlist: str = "n/a" # the netlist extracted from the script after requirement stage
    repair_plan: Optional[str] = None # concise diagnosis and proposed next steps for repair, sourced from optimizer diagnosis agent, if none provided default to None
    accepted: bool = False
    plot_data: dict = field(default_factory=dict) # plot-ready simulation arrays captured during the check suite (see optimizer._extract_plot_data); consumed by main's --plots rendering

    # returns first failed check if any, else None
    def first_failure(self) -> Optional[CheckResult]:
        for c in self.checks:
            if not c.passed:
                return c
        return None

    # returns the stage of the first failed check if any, else None
    def failure_stage(self) -> Optional[str]:
        f = self.first_failure()
        return f.stage if f else None
