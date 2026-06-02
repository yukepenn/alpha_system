# Label Store MVP

ASV1-P10 defines a local-only label layer for offline research diagnostics and
model-training datasets. A label describes future information after an event
timestamp. It is never a live factor input, strategy input, order-routing input,
or execution input.

## Label Record Schema

Every label record has exactly these fields:

```text
label_id
instrument_id
event_ts
horizon
label_type
value
path_metadata
data_version
label_available_ts
```

`event_ts` is the decision/event timestamp being labeled. `label_available_ts`
is the earliest timestamp at which the label may be used for offline research
because all future information needed by the label has completed and become
available. These timestamps are intentionally distinct.

`path_metadata` carries path and alignment details such as:

```text
session_id
bar_index
label_version
horizon_minutes
horizon_end_ts
required_future_bars
observed_future_bars
insufficient_future
clamped_to_session_close
```

The top-level record schema stays fixed while `path_metadata` records the
session and label-version keys required for research joins.

## Standard Label Families

The MVP supports:

```text
forward_return_1m
forward_return_3m
forward_return_5m
forward_return_10m
forward_return_30m
mfe_by_horizon
mae_by_horizon
target_before_stop
stop_before_target
future_realized_volatility
future_spread_liquidity
```

Forward returns are close-to-close labels from the event bar close to the close
at the requested future horizon. MFE and MAE use the high/low path inside the
future window. Target/stop labels use conservative ordering: if both target and
stop are touched in the same one-minute bar, neither ordering label is marked
true and the path metadata records `ambiguous_same_bar`.

Future realized volatility is computed from future close-to-close returns.
Future spread/liquidity uses average future spread as the scalar value and
stores supporting liquidity context, such as total volume and average trade
count, in `path_metadata`.

## Availability And No-Lookahead

Labels are future-information artifacts. A label is valid only when:

```text
label_available_ts >= path_metadata.horizon_end_ts
label_available_ts >= event_ts
```

For complete horizons, `label_available_ts` is taken from the terminal future
bar's `available_ts`, not merely from its bar end time. For insufficient future
windows, the label value is `null`, `insufficient_future` is true, and the
record is clamped to the observed session close. The generator does not carry a
forward horizon into the next session.

## Session And Half-Day Handling

Generation groups bars by:

```text
instrument_id
data_version
session_id
```

Within each group, `bar_index` is expected to reset for the session. Horizons
are resolved by bar index inside the same session. If the requested future bars
are not present before the session close, including half-day closes, the result
is an insufficient-future label rather than a fabricated cross-session value.

## Factor-Label Join Policy

Factor-to-label joins are offline point-in-time research joins only. The
alignment key is:

```text
instrument_id
event_ts
session_id
horizon
data_version
label_version
```

Labels are not a factor input domain and are not a strategy input domain. The
label alignment API rejects live-factor and live-strategy consumption purposes,
and it rejects proposed input fields that are label records or label fields.

## Versioning

Label versions are recorded in the ASV1-P05 `label_versions` table. ASV1-P10
does not add or redefine registry schema. Version records include:

```text
label_id
label_version
label_type
created_at
git_commit
git_dirty
code_hash
config_hash
data_version
parameters_json
artifact_paths_json
decision_status
status_message
```

Tests use temporary SQLite registry paths outside the repository. No production
registry database is created under `metadata/`.

## Artifact Policy

The default label store writes JSONL files under a temporary local directory.
Caller-provided store roots inside the repository, Windows-mounted paths, and
common synced-folder paths are rejected. Generated label stores, local SQLite
files, Parquet, Arrow, Feather, raw data, canonical data, logs, caches, and
large artifacts are not commit-eligible.

## Known Limitations

This MVP is library-level only. It has no label CLI, no factor computation, no
diagnostic scoring, no model training workflow, no backtest engine, no portfolio
logic, no strategy logic, no broker integration, and no live or paper trading
path. Fixtures are tiny deterministic correctness fixtures only.
