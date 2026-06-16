## API

- [API] The top-level Circuit object must be assigned to a variable named exactly `circuit`
- [API] Use circuit.M() for MOSFETs, not circuit.MOSFET()
- [API] MOSFET syntax: circuit.M('name', 'drain', 'gate', 'source', 'bulk', model='MODEL', l=length_m, w=width_m)
- [API] l= and w= take plain floats in meters (e.g. l=1e-6, w=10e-6) or PySpice unit values (l=1@u_um)
- [API] There is no body= or L= or W= argument — bulk is the 5th positional node, l/w are lowercase keyword arguments
- [API] lambda is a Python reserved word — use lambda\_= in model definitions
- [API] Do not pass type= to circuit.model() — the model type (nmos/pmos) is already set by the second positional argument; passing type= causes ngspice to receive a string where it expects a number

## NODE

- [NODE] Output node must be named Vout
- [NODE] Input source must be circuit.V('in', 'Vin', circuit.gnd, ...)
- [NODE] Supply must be circuit.V('dd', 'Vdd', circuit.gnd, ...)
- [NODE] NMOS bulk ties to ground; PMOS bulk ties to Vdd
- [NODE] Every node must have a DC path to ground — no floating nodes

## SYNTAX

- [SYNTAX] Do not define circuit inside a function unless it is assigned to a module-level variable at the bottom — exec() only sees the top-level namespace

## SIM

- [SIM] Do not call plt.show() or include any display/plot code — the validation pipeline runs headless

## SIM (continued)

- [SIM] Do not add simulation or operating point code at module level — the validation pipeline runs its own simulations; any inline sim calls will cause import errors or interfere with exec()
- [SIM] Leave input source DC values at a realistic bias (e.g. 1.0–1.5V for NMOS gates) — leaving Vin at 0V puts input transistors in cutoff at the operating point

## CONV

- [CONV] Do not connect an NMOS drain back to its own source/tail node through any resistor — this forces Vds ≈ 0
- [CONV] Do not use milliohm or microohm resistors to alias nodes — reuse the same node name string instead

- [NODE] Do not leave gate nodes driven by independent fixed DC sources when the testbench will sweep a master input (Vin); tie gate node names to Vin or remove per-gate voltage sources and sweep the gate nodes directly so the sweep actually drives the transistor gates.

- [CONV] Do not add high-value "leak" resistors from CMOS outputs or internal inverter nodes to ground or Vdd; complementary transistors define static states and such resistors create asymmetric loading and unwanted bias currents that distort logic behavior.

- [NODE] Do not connect an NMOS source to Vdd while leaving its bulk at ground — this forward‑biases the body diode; tie the bulk to the appropriate well/source node (or keep device orientation consistent with substrate) to avoid forward‑biased body junctions.
- [CONV] A diode‑connected MOSFET is a low‑impedance device and is not a high‑resistance current source; use a diode‑connected reference plus a mirrored transistor (current mirror) or a cascode mirror when you need a high‑impedance load/current source.

- [API] Do not call circuit.Node(...); the Circuit object has no Node() method — nodes are created implicitly by using node-name strings in element/component calls (e.g., circuit.R('R1', 'Vdd', 'Iref', ...)).

- [CONV] Avoid ultra‑high resistance values (e.g., megaohm‑scale) in bias/reference resistor legs for MOS analog circuits; such large resistances can starve bias nodes of current and leave downstream transistors near cutoff.
- [CONV] When using a diode‑connected MOSFET to generate a gate/reference voltage for a current source or mirror, ensure the diode device W/L and any series resistor are chosen so the diode's Vgs settles comfortably above threshold; otherwise the mirrored/current‑source transistor and the stages it biases may remain off.

- [CONV] PMOS current‑mirror loads can force their drain nodes up to Vdd if the mirror reference current or PMOS device widths are too large; limit mirror current (increase the reference resistance) or reduce PMOS width to prevent intermediate nodes from being rail‑stuck.
