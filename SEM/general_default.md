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
- [SIM] Do not add simulation or operating point code at module level — the validation pipeline runs its own simulations; any inline sim calls will cause import errors or interfere with exec()

## ADDED BY CURATOR
