# Frontier Ralph Adapter

The adapter boundary is:

```text
Ralph loop
-> tools/frontier/ralph_driver.py
-> campaign/spec/handoff/review/run artifacts
-> merge gate scaffold
```

Generated code initializes run state and ledgers only. It does not call external model providers or GitHub APIs.
