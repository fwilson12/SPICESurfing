# General Rules

## Curator: append atomic entries under the appropriate section

## Format: `- [TAG] description` Tags: API, NODE, SYNTAX, SIM, CONV

## API

- [API] Use `circuit.R('R1', 'node1', 'node2', 1@u_kOhm)` — units must come from PySpice.Unit.
- [API] Capacitor initial condition: `ic=...` parameter, NOT `initial_condition=...`.
- [API] Never use `circuit.add_nodes()` — nodes are created implicitly when referenced.
- [API] Subcircuit pin names must be passed as a single iterable to `subcircuit()`.
- [API] Any `circuit.X(...)` instantiation requires the subcircuit to be defined/loaded beforehand.
- [API] Opamp subcircuit interface: exactly three pins (non-inv, inv, out); do not redefine Opamp.

## NODE

- [NODE] Ground node `circuit.gnd` must be defined and reachable from every node (required by ngspice).
- [NODE] Every node must have a DC path to ground to avoid singular matrix errors.
- [NODE] Output nodes must be named exactly as specified in the task (e.g., `Vout`, `Voutp`).
- [NODE] NMOS bulk must tie to source; PMOS bulk must tie to Vdd.

## SYNTAX

- [SYNTAX] Avoid Python reserved words as node/label names; append underscore if needed (e.g., `lambda_`, `in_`, `is_`).
- [SYNTAX] Place each Python statement on its own line — concatenation causes SyntaxError.
- [SYNTAX] MOSFET model polarity: `vto` positive for NMOS, negative for PMOS.

## SIM

- [SIM] Always include an operating point analysis (`simulator.operating_point()`) to catch DC bias issues before transient/AC.
- [SIM] For convergence failures: try tightening `reltol`/`abstol` via `simulator.options(...)` before restructuring the circuit.
- [SIM] DC sweep: sweep wide first (0 to Vdd) to catch rail-stuck behavior before zooming in.
- [SIM] AC output is complex — verify `np.iscomplexobj(vout)` before computing phase; magnitude-only data makes phase meaningless.

## CONV

- [CONV] PMOS width is typically 2x NMOS width to balance mobility differences.
- [CONV] Minimum channel length for analog: `l=1e-6`; use longer L for better matching in mirrors.
- [CONV] Required imports: `from PySpice.Spice.Netlist import Circuit`, `from PySpice.Unit import *`.
- **Issue:** SyntaxError and parsing failures at startup (Line 1) often stem from invisible Byte Order Marks (BOMs `\ufeff`) in generated Python scripts when passed to execution environments or parsers.
- _Fix:_ Ensure all script generation tools save files without BOM using UTF-8 encoding (`encoding='utf-8-sig'` is bad for this; use standard `open(..., 'w')`). Always strip non-printable leading characters in automated code blocks before simulation execution to prevent immediate SyntaxError states.
- _Observation:_ Avoid importing unit conversion modules via wildcards (`from PySpice.Unit import *`) as the repair process indicated these are unsupported or deprecated in current netlist generators; use raw string literals for values (e.g., `'10k'`, `5V` compatible strings) instead. Do not append custom decorators like `@u_kOhm` to numeric constants passed directly into circuit component definition functions, as standard PySpice components expect valid SPICE-like parameter formats or explicit model calls without external decorator syntax which may break netlist conversion routines in this toolchain version.

: PySpice `Circuit` instance must be explicitly instantiated via `sp.Circuit()` immediately after import statements and assigned strictly to a variable named `'circuit'`. The component definition (e.g., `.add_mos`) requires this specific identifier to exist in the script's namespace; validation failures occur if any other name is used.
