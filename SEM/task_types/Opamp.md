- [CONV] For multi‑stage op‑amps, make the final stage provide voltage gain (e.g., common‑source or push‑pull common‑source) when overall DC gain is required; using source followers as the output stage yields near‑unity gain and limits total amplifier gain and DC swing control.

- [CONV] Ensure the output stage pull‑up (PMOS) can source comparable current to the pull‑down (NMOS); under‑sized pull‑ups will let the output collapse toward ground even if pull‑down transistors are moderate, preventing a mid‑range DC operating point.

- [CONV] For multi‑stage MOS op‑amps, ensure intermediate gain‑node biasing is set by a balanced combination of PMOS load strength, tail current, and output transistor sizing — oversized PMOS loads or excessive bias current will push intermediate nodes to Vdd and make the output immovable at the rail.

