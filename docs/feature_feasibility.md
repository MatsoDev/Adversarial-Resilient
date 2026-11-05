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
| `strings` | Statistics changed by appended content | Conditionally modifiable | Counts, averages, distributions and entropy must be recomputed together from a realizable edit. |
| `header` | Timestamp or header fields | Review required | Many fields are structural or loader-sensitive; keep immutable until the security review approves a concrete operation. |
| `exports` | Add or remove exports | Review required | Must preserve a valid PE and intended behavior; use only as a documented experiment. |
| `datadirectories` | Change addresses/sizes | Non-modifiable for baseline attacks | Direct edits can invalidate the file; derive changes from a valid structural transformation instead. |

For CIC-IDS-2017, timing and packet-size fields may be conditionally
modifiable in a network simulation; identifiers, labels, and fields that would
require changing the protocol state remain non-modifiable until SS-B documents
a safe simulation. All attacks report whether evidence is feature-space only,
problem-space validated, or unavailable.

## Constraints for the upcoming attack implementation

All group offsets refer to the raw feature vector before standardization; use
the [2381-dimensional layout](data/ember_feature_layout.md). Hashed coordinates
may be signed and collide, so a hashed bin cannot be treated as an independent
PE field. Integer scalar counts must remain integral and nonnegative;
normalized histogram groups must retain their normalization constraints. A
feature-space mask is only a research approximation, never proof of a valid
executable. Do not enable a mutation solely because a column is numeric.

| Network feature family | Initial policy | Required evidence |
|---|---|---|
| Timing / inter-arrival statistics | Conditional; immutable until validated | Consistent session duration, rates and direction-specific aggregates in a simulation |
| Packet/byte counts and sizes | Conditional; immutable until validated | Protocol-valid relationships, bounds, and unchanged intended session behavior |
| Flags / header-dependent counts | Immutable initially | Protocol-state and aggregate consistency review by SS-B |
| Labels, hashes, IDs and dataset metadata | Immutable; exclude from attack inputs | Preserve ground truth and sample identity |

SS-A and SS-B must review and approve concrete operations before Sprint 5
generates constrained attacks. This table is a proposal for review; no
problem-space mutation or live malware execution is implemented in Sprint 3.
