import argparse
import json
import os
import subprocess
from pathlib import Path

from schema import IterationRecord

from agents.optimizer import validate_and_optimize
from agents.wise_one import curate
from agents.code_generator import generate_script


def circuit_time(task: dict, max_attempts: int) -> list[IterationRecord]:

    SEM_additions = []
    record_book = []
    current_repair_plan = ""
    current_netlist = ""
    for i in range(max_attempts):

        print(f"\n{'=' * 60}\n  ATTEMPT {i + 1} OF {max_attempts}  |  {task['name']}\n{'=' * 60}")

        ''' Script Generation '''
        print("\n--- Generating PySpice code ---\n")
        script = generate_script(task, current_repair_plan, current_netlist)
        # debug
        print(script)


        ''' Validation and Simulations '''
        print("\n--- Validating ---\n")
        IterRecord = validate_and_optimize(i + 1, task, script)
        # context for next iteration
        current_repair_plan = IterRecord.repair_plan
        current_netlist = IterRecord.netlist
        record_book.append(IterRecord)
        for check in IterRecord.checks:
            # SKIP = stage not applicable to this circuit class; otherwise PASS/FAIL
            status = "SKIP" if not check.applicable else ("PASS" if check.passed else "FAIL")
            print(f"  [{status}] {check.stage:<12} {check.message}")

        ''' Self-Evolving Memory Additions '''
        print("\n--- Curating SEM additions ---\n")
        SEM_addition = curate(IterRecord, task)
        SEM_additions.append(f'SEM Addition for iteration {i + 1}: {SEM_addition} \n\n')
        print(f"New knowledge added to SEM:\n{SEM_addition}")


        # script passed
        if IterRecord.accepted:
            print(f"\n--- ACCEPTED on attempt {i + 1} ---\n")
            print(f"---FINAL SCRIPT ({task['name']})---:\n\n{script}\n")
            break


        else:
            print(f"\n  Result: REJECTED (failed at '{IterRecord.failure_stage()}')")
            print(f"  Repair plan for next attempt:\n{current_repair_plan}\n")

    if record_book and not record_book[-1].accepted:
        print(f"\n{'-' * 60}\n  NOT ACCEPTED after {len(record_book)} attempt(s)\n{'-' * 60}")

    return record_book



def view_record_book(records: list[IterationRecord], task: dict) -> None:

    print(f"\n{'-' * 60}\n  RECORD BOOK: {task['name'].upper()}\n{'-' * 60}")
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





def final_accepted_netlist(records: list[IterationRecord]) -> str | None:
    '''
    Returns the SPICE netlist of the final accepted iteration, or None if the
    run never produced an accepted circuit (or no netlist was captured).
    '''
    if records and records[-1].accepted:
        netlist = records[-1].netlist
        if netlist and netlist != "n/a":
            return netlist
    return None


# default location of the (patched) netlist-viewer executable; override with the NETLIST_VIEWER_EXE environment variable or the --viewer CLI argument
DEFAULT_VIEWER_EXE = r"C:\dev\netlist-viewer\NetlistViewer\build\win\x64\Release\netlist_viewer.exe"


def visualize_netlist(netlist: str, task_label: str, viewer_exe: str) -> None:
    '''
    Writes the given SPICE netlist to visualizations/<task_label>.ckt and launches
    the netlist-viewer GUI on it (non-blocking) if --visualize was passed
    
    task_label is the task file stem (e.g. "easy_2", "medium_7")
    '''
    viewer = Path(viewer_exe)
    if not viewer.is_file():
        print(f"\n[visualize] netlist-viewer not found at '{viewer}'.")
        print("[visualize] Pass --viewer <path-to-netlist_viewer.exe> or set "
              "the NETLIST_VIEWER_EXE environment variable.")
        return

    # write the netlist keyed by the task file name (e.g. easy_2.ckt) so figures persist
    out_dir = Path("visualizations")
    out_dir.mkdir(exist_ok=True)
    ckt_path = out_dir / f"{task_label}.ckt"
    ckt_path.write_text(netlist, encoding="utf-8")

    print(f"\n[visualize] Netlist written to {ckt_path}")
    print(f"[visualize] Opening netlist-viewer ...")
    try:
        subprocess.Popen([str(viewer), str(ckt_path.resolve())]) # open the netlist-viewer process, args are the executable loc and netlist file location
    except OSError as e:
        print(f"[visualize] Failed to launch viewer: {e}")


def main(task: dict, max_attempts: int, visualize: bool = False,
         viewer_exe: str = DEFAULT_VIEWER_EXE, task_label: str = "circuit") -> None:

    record_book = circuit_time(task, max_attempts)

    view_record_book(record_book, task)

    if visualize:
        netlist = final_accepted_netlist(record_book)
        if netlist is None:
            print("\n[visualize] No accepted netlist to display")
        else:
            visualize_netlist(netlist, task_label, viewer_exe)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True, help='Path to task JSON file (e.g. tasks/easy_6.json)')
    parser.add_argument('--max_attempts', type=int, default=10)
    parser.add_argument('--visualize', action='store_true', help='On success, render the final netlist as a schematic in netlist-viewer')
    parser.add_argument('--viewer', default=DEFAULT_VIEWER_EXE, help='Path to the netlist_viewer.exe used by --visualize')

    args = parser.parse_args()
    main(json.loads(Path(args.task).read_text()), args.max_attempts, visualize=args.visualize, viewer_exe=args.viewer, task_label=Path(args.task).stem)
