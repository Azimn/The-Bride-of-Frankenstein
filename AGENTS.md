# Agent instructions

`README.md` is the canonical architecture contract, developer guide, release gate, and project status record for this repository.

Before behavior-changing work, read `README.md` completely and preserve its authority boundaries. If a change requires altering an architectural rule, update the README in the same reviewed change and add tests that demonstrate the new contract.

Do not let renderer or semantic-interpreter output directly mutate canonical truth. Do not introduce a second action executor. Do not store unique history only in a disposable projection. Do not add a mandatory cloud dependency to the core without an explicit project-level architecture decision.
