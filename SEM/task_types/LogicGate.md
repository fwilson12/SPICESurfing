- [SYNTAX] Replace unit multiplications (e.g., `5 * u_V`, `100e6 * u_Ohm`) with the `value@unit` syntax (e.g., `5@u_V`, `100e6@u_Ohm`) to avoid TypeError issues.

- [API] Common issue: ImportError due to undefined units in PySpice. When encountering an ImportError, check for any omitted or deprecated units in the version of PySpice in use and update the code accordingly.

- [API] Ensure correct handling of DC operating point node values by indexing correctly to avoid TypeError related to array conversions.

- [API] In circuits with pulse voltage sources, note that their terminals might not be explicitly represented in the DC operating point analysis; use `dc_op.nodes.get('NodeName', [fallback_value])` to avoid errors.

- [SYNTAX] When creating sinusoidal voltage sources in PySpice, set the AC amplitude directly during initialization using the `ac_amplitude` parameter. Avoid additional indexing to access the source object post-creation.

