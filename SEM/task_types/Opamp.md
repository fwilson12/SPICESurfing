- [CONV] For multi‑stage op‑amps, make the final stage provide voltage gain (e.g., common‑source or push‑pull common‑source) when overall DC gain is required; using source followers as the output stage yields near‑unity gain and limits total amplifier gain and DC swing control.

- [CONV] Ensure the output stage pull‑up (PMOS) can source comparable current to the pull‑down (NMOS); under‑sized pull‑ups will let the output collapse toward ground even if pull‑down transistors are moderate, preventing a mid‑range DC operating point.

- [CONV] For multi‑stage MOS op‑amps, ensure intermediate gain‑node biasing is set by a balanced combination of PMOS load strength, tail current, and output transistor sizing — oversized PMOS loads or excessive bias current will push intermediate nodes to Vdd and make the output immovable at the rail.

- [CONV] In OTA input stages, use an NMOS tail current sink beneath an NMOS differential pair (or a PMOS tail above a PMOS pair) so the tail device sees the correct Vgs/Vsg polarity; mis-oriented tails (e.g., PMOS tail feeding an NMOS pair from Vdd with its gate driven by a low node) often leave the entire differential pair cut off and the output rail-stuck.

- [CONV] Do not self‑bias a PMOS current mirror for an OTA output or load stage by tying its gate/drain node near Vdd through a high‑value resistor; this collapses Vsg toward 0, turns both the reference and output PMOS devices off, and leaves the output rail‑stuck at ground — instead, reference the diode‑connected PMOS to the actual signal/bias node it must mirror.

- [CONV] Do not use NMOS transistors as high‑side “active loads” for an NMOS differential pair with their sources at Vdd and bulks at ground; this forward‑biases body diodes and forces the gain nodes toward ground, collapsing headroom and rail‑locking the OTA output — use PMOS loads tied to Vdd instead.

- [CONV] In OTA differential input stages with PMOS active loads and PMOS output mirrors, set the PMOS gate bias close enough to Vdd that Vsg at low output/gain-node voltages is only slightly above |Vth|; a gate bias too far below Vdd overdrives the PMOS loads/mirror, clamping gain nodes and Vout near ground and preventing usable output swing.

- [CONV] When implementing a PMOS current mirror used as an active load or output stage in an OTA, ensure the PMOS source terminals are tied to the high supply (Vdd) and the drains to the lower signal nodes; mis‑orienting the devices so that source and drain are effectively swapped toward the signal node collapses Vsd/Vsg, turns the mirror off or into a low‑impedance clamp, and leaves the OTA output rail‑stuck.

- [CONV] In NMOS-input OTAs with PMOS active loads and PMOS mirrors, if the output node is stuck near the positive rail while the differential pair is biased on, first adjust the PMOS gate-bias voltage closer to Vdd and/or reduce the output load resistance to increase PMOS overdrive and output current swing, rather than only increasing tail bias current.

- [CONV] In NMOS‑input OTAs with PMOS active loads and PMOS current‑mirror outputs, an output node stuck near Vdd across an input sweep is often caused by over‑strong PMOS loads/mirror relative to the NMOS tail current; to recover differential swing, simultaneously (a) reduce PMOS load/mirror bias (raise Vpg toward Vdd), (b) downsize the PMOS mirror devices, or (c) modestly increase the NMOS tail current so the differential pair can pull the gain/output nodes away from the positive rail.

- [CONV] In NMOS‑input OTAs with PMOS active loads and a PMOS current‑mirror output, if Vout is stuck near Vdd despite a valid operating point, check for an under‑biased differential pair and weak tail current: increase NMOS tail current (via stronger tail device or lower bias resistance) and move the PMOS load‑gate bias closer to mid‑supply so N1/N2 can swing and force appreciable current through the PMOS mirror and output load.

