## Amplifier

## Topology
- [NODE] Differential pair: MN1 drain→nd1, MN2 drain→Vout; both sources at Itail (common tail node)
- [NODE] PMOS mirror load: M3 diode-connected (drain=gate=nd1, source=bulk=Vdd), M4 mirrored (drain=Vout, gate=nd1, source=bulk=Vdd)
- [NODE] MN2 drain MUST share the same node as P4 drain — name both 'Vout' directly; do not use separate names (nd2 vs Vout) connected by aliases, 0V sources, or tiny resistors
- [NODE] Tail NMOS: drain=Itail, gate=Vbias, source=bulk=gnd; Itail is the shared source node of MN1 and MN2

## Biasing
- [CONV] Tail NMOS Vbias should be just above Vth (e.g. 1.0–1.2V for Vto=0.7) — high Vbias increases Vgs-Vth and makes saturation harder, not easier
- [CONV] Both Vin and Vref must be biased above Vth (≥ 1.0V for Vto=0.7) — leaving either at 0V puts the input NMOS in cutoff
- [CONV] Set Vin and Vref to different values (e.g. Vin=1.0V, Vref=1.5V) — equal values produce a degenerate symmetric operating point where the simulator cannot determine a unique DC solution
- [CONV] NMOS model threshold is Vto=0.7 — size and bias accordingly

## Load
- [CONV] Load resistor at Vout to ground should be 10k–100kΩ; too small (< 5kΩ) dominates the PMOS mirror current and prevents Vout from rising; too large has no effect on swing
- [CONV] Do not connect any NMOS drain back to the Itail (source/tail) node — this forces Vds ≈ 0 and kills that branch

