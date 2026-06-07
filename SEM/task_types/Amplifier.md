## Amplifier

- [NODE] One differential input must be tied to the swept signal (Vin); fixed equal inputs produce zero differential signal and a flat Vout response
- [NODE] Tail current source gate must be biased sufficiently above Vto — if the tail NMOS is in cutoff there is no drain current and the differential pair is dead
- [CONV] A realistic load resistor (1k–100kΩ) at Vout to ground is required for voltage swing — without it Vout has no path to move
- [CONV] PMOS current mirror load: M3 diode-connected (drain=gate=Nd1, source=bulk=Vdd), M4 mirrored (drain=Vout, gate=Nd1, source=bulk=Vdd)
