# Canary: planted true-signal detection

Purpose: verify that the synthetic diagnostic path detects a declared planted
relationship when the relationship is above the declared floor, and does not
detect a weaker planted relationship below that floor.

The fixtures are point-in-time clean: each label is constructed from the same
row feature value plus deterministic noise, and each label availability
timestamp is after its horizon end. These fixtures are synthetic canary
metadata only and are not market evidence.
