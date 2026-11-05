# Sprint 3 feature-feasibility table

This is a research planning artifact for constrained feature-space attacks. It
does not claim that a changed feature produces a valid executable. The security
team must review each row before it is used by an attack implementation.

| EMBER feature group | Candidate change | Initial status | Reason / validation needed |
|---|---|---|---|
| `section` | Add a section or append data | Conditionally modifiable | Must preserve a valid PE and remain functionality-preserving; validate only in an isolated lab with benign test files. |
| `imports` | Add an existing library/function reference | Conditionally modifiable | Requires a realizable PE edit and may change behavior; feature-only perturbations are insufficient evidence. |
| `general` | File size / section count | Conditionally modifiable | May follow a valid structural edit; never edit independently without a problem-space check. |
| `histogram` / `byteentropy` | Append bytes | Conditionally modifiable | Must be tied to a valid append operation and valid ranges; these groups are normalized summaries. |
| `header` | Timestamp or header fields | Review required | Many fields are structural or loader-sensitive; keep immutable until the security review approves a concrete operation. |
| `exports` | Add or remove exports | Review required | Must preserve a valid PE and intended behavior; use only as a documented experiment. |
| `datadirectories` | Change addresses/sizes | Non-modifiable for baseline attacks | Direct edits can invalidate the file; derive changes from a valid structural transformation instead. |

For CIC-IDS-2017, timing and packet-size fields may be conditionally
modifiable in a network simulation; identifiers, labels, and fields that would
require changing the protocol state remain non-modifiable until SS-B documents
a safe simulation. All attacks report whether evidence is feature-space only,
problem-space validated, or unavailable.
