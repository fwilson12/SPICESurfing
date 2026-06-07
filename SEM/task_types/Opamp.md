- [NODE] Ensure the output node of the OTA is named one of the recognized names such as 'Vout', 'output', etc. to pass validation checks.
- [NODE] Consider maintaining backward compatibility with existing scripts or tooling by creating an alias for the renamed output node.

- [SIM] The operating point simulation may fail if PMOS transistors are biased out of saturation; ensure that the overdrive voltage (|Vsg|) is greater than the threshold voltage (|Vth|) with a sufficient margin for proper operation.

- [SIM] For the PMOS current mirror to operate correctly, ensure that the source node (Pbias) is not too close to the power supply (VDD) to allow sufficient overdrive for the PMOS transistors to enter saturation.

- [SIM] Ensure PMOS devices (like PM3, PM4) are biased well into saturation by adjusting either the bias current or sizing, especially focusing on ensuring |Vsg| is greater than |Vth|.
- [SIM] If output current mirrors are required to maintain a specific value, consider adjusting the width (W) of PMOS devices to achieve necessary saturation conditions without exceeding maximum voltage limits.
- [SIM] When optimizing bias currents, consider the trade-off between mirror accuracy and device saturation to ensure circuitry functions as required.

- [REPAIR] Increase PMOS current mirror bias current (`I_mirr`) to ensure PM3 and PM4 operate in saturation: adjustment helps increase Vsg above threshold.
- [REPAIR] Optionally decrease PMOS widths (w) of mirror devices (PM3, PM4) to increase the required gate overdrive for achieving similar current, ensuring they operate in saturation.

- [SIM] Ensure PM3 and PM4 MOSFETs are in saturation by adjusting their sizing and threshold voltage. Monitor their Vsg against Vth to confirm saturation status.

- [REPAIR] When a PMOS device is found not to be in saturation, consider adjusting the threshold voltage (vto) of the PMOS model to ensure it qualifies for saturation with the given VSG. For example, change the vto of the PMOS from -0.55V to -0.4V if |VSG| is close to the threshold.
- [REPAIR] Alternatively, reduce the widths of PMOS devices in a current mirror configuration to ensure a higher |VSG| for the same bias current. Decreasing the width will require a higher overdrive voltage to sustain the same current, thereby helping to keep them in saturation more effectively.

- [SIM] The common cause of a "not in saturation" error for MOSFETs involves inadequate biasing of the gate-source voltage (Vsg) in PMOS devices. Adjusting the bias current or increasing the W/L ratio can help achieve proper operation. Always check that Vsg is sufficiently larger than the absolute value of the threshold voltage (Vth).

- [REPAIR] To ensure PMOS transistors (PM3, PM4) are in saturation, increase their gate-source voltage (Vsg) by raising the reference current for the mirror while keeping their width/length ratio small. Set optimal bias to 80-100 µA and consider reducing width.
- [CHECK] After adjustments, verify that |Vsg| > |Vth| for PM3 and PM4 during operating-point analysis.
- [API] Ensure that the element names assigned in `circuit.MOSFET()` match the keys used for parameter overrides. Do not prefix with `M_` when overriding parameters such as `l` and `w`.

- [API] Make sure to use `circuit.M(...)` for all MOSFET devices to ensure they are created and indexed correctly.
- [API] Update attribute accesses for sinusoidal voltage sources to correspond with their assigned names.

- [API] Fix PMOS terminal ordering in PySpice `M()` function: The correct order is `(drain, gate, source, bulk)`. Ensure to audit the terminal order for consistency in all PMOS devices. 
- [API] For PM3 and PM4, if keeping source and bulk at VDD, the terminal orders should be: `PM3` as `(drain='N_PBIAS', gate='N_PBIAS', source='VDD', bulk='VDD')` and `PM4` as `(drain=PBIAS, gate='N_PBIAS', source='VDD', bulk='VDD')`.

- [REPAIR] When defining MOSFETs, ensure that all necessary parameters such as L (length) and W (width) are included directly within the model definition. This avoids issues with incomplete device definitions which can cause simulation failures.

- [NODE] Update NMOS diode-connected mirror definition to source from ground and keep bulk at ground for valid DC path. This is crucial for correct biasing in circuit implementations.

- [TOP] Ensure that NMOS mirror connections adhere to valid circuit topology. A diode-connected NMOS cannot have its source at ground if its drain node is pulled below 0 V by a PMOS above it; this can cause convergence issues and device limit violations. Instead, ensure the NMOS's source is connected to a proper tail current node to maintain legality.

- [API] NgSpice rejects illegal MOS model parameter names such as `lambda_` and `is_`. Use `lambda` and `is` instead. 
- [API] If using `lambda` as a keyword argument presents issues, consider using the dictionary format for parameters in model definitions.

- [SYNTAX] Change instances of `N@u_unit` to `N * u_unit` to ensure correct syntax in PySpice scripts to avoid syntax errors during compilation. Common conversions include `10@u_kΩ` to `10 * u_kΩ` and similar patterns for other units.

- [SYNTAX] In MOSFET model definitions within PySpice, replace instances of `**{'lambda': value}` with `lambda_=value` to prevent SyntaxError due to reserved keywords in Python.

- [API] For OTA designs, ensure that the `lambda_` keyword argument is omitted in both subcircuit models and top-level circuit model definitions to prevent syntax errors.

- [SYNTAX] Ensure that the subcircuit initialization signature includes nodes directly instead of declaring a separate __nodes__ attribute to avoid syntax errors and maintain compatibility with PySpice.

