# Frozen published artifacts

The contract 1 vocabulary and shapes, exactly as 0.10.0 published them. Graphs
in the wild declare `dct:conformsTo <https://w3id.org/specl/contract/1>` and
pin `https://w3id.org/specl/ns/1`, so these have to keep resolving to the same
bytes forever.

They are files rather than a `git show` against a tag. The Pages build read them
from `v0.10.0` at first, which broke twice over: the tag does not exist in every
clone of this repository, and `actions/checkout` fetches no tags by default. A
frozen artifact that a build reconstructs from history is a frozen artifact one
shallow clone away from disappearing.

Do not edit these. Contract 2 lives in `src/specl/`, and a third contract would
add `ns-2.ttl` and `shapes-2.ttl` here at the same time.
