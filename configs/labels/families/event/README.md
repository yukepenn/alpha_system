# Event Label Config Placeholder

This directory is reserved for future declarative configuration for the
strategy-agnostic event label family. FLF-P20 adds no materialization jobs,
provider access, registry writes, broker/live/paper/order behavior, strategy
wrappers, or alpha claims.

Expected future configuration fields are governed by `LabelSpec` records and
include event label name, horizon, event direction, sweep side, BBO quality
thresholds, and availability semantics. Label values remain local-only and are
not stored in this placeholder directory.
