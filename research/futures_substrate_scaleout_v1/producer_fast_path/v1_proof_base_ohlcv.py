import time, json, sqlite3, os
from pathlib import Path
import polars as pl
root=os.environ['ALPHA_DATA_ROOT']
CAN=f"{root}/databento/canonical/glbx_mdp3/dsv_databento_ohlcv_05404069799decb0/schema=ohlcv_1m/root=ES/part-00000.parquet"
W=20

# ---- V1 fast path: load once, compute all 6 features vectorized ----
t0=time.time()
df=pl.read_parquet(CAN).sort(["available_ts"])
for col in ("open","high","low","close","volume"):
    df=df.with_columns(pl.col(col).cast(pl.Float64))
rmin_low=pl.col("low").rolling_min(window_size=W, min_periods=W)
rmax_high=pl.col("high").rolling_max(window_size=W, min_periods=W)
df=df.with_columns([
    (pl.col("close")/pl.col("close").shift(1)-1.0).alias("returns"),
    (pl.col("close")/pl.col("close").shift(1)).log().alias("log_returns"),
])
df=df.with_columns([
    pl.col("returns").rolling_std(window_size=W, min_periods=W, ddof=0).alias("rolling_volatility"),
    (rmax_high-rmin_low).alias("rolling_range"),
    pl.when(rmax_high==rmin_low).then(None).otherwise((pl.col("close")-rmin_low)/(rmax_high-rmin_low)).alias("range_position"),
    ((pl.col("volume")-pl.col("volume").rolling_mean(window_size=W,min_periods=W))/pl.col("volume").rolling_std(window_size=W,min_periods=W,ddof=0)).alias("volume_zscore"),
])
v1_time=time.time()-t0
print(f"V1 (polars, load+compute 6 features): {v1_time:.2f}s  rows={df.height}")

# ---- parity vs materialized reference ----
c=sqlite3.connect(root+'/registry/features.sqlite')
def ref_values(fid):
    p=c.execute("select parquet_path from feature_registry_records where feature_id=? and partition_id='ES_2024_full_year'",(fid,)).fetchone()[0]
    r=pl.read_parquet(p).select(["available_ts","value_json"])
    return r.with_columns(pl.col("value_json").map_elements(lambda s: float(s) if s not in (None,"null","") else None, return_dtype=pl.Float64).alias("ref")).select(["available_ts","ref"])

feat_map={"returns":"base_ohlcv_returns","log_returns":"base_ohlcv_log_returns","rolling_volatility":"base_ohlcv_rolling_volatility","rolling_range":"base_ohlcv_rolling_range","range_position":"base_ohlcv_range_position","volume_zscore":"base_ohlcv_volume_zscore"}
print(f"\n{'feature':22}{'n':>8}{'val_match':>10}{'maxdiff':>12}{'gap_match':>10}")
allok=True
for col,fid in feat_map.items():
    ref=ref_values(fid)
    j=df.select(["available_ts",pl.col(col).alias("v1")]).join(ref, on="available_ts", how="inner")
    n=j.height
    both_val=j.filter(pl.col("v1").is_not_null() & pl.col("ref").is_not_null())
    diff=(both_val["v1"]-both_val["ref"]).abs()
    maxdiff=float(diff.max()) if both_val.height else 0.0
    val_match=int((diff<=1e-9).sum()) if both_val.height else 0
    # gap alignment: rows where ref is null vs v1 null
    gap_match=int((j["v1"].is_null()==j["ref"].is_null()).sum())
    ok = (val_match==both_val.height) and (gap_match==n)
    allok = allok and ok
    print(f"{col:22}{n:>8}{val_match:>10}{maxdiff:>12.2e}{gap_match:>10} {'OK' if ok else 'MISMATCH'}")
print(f"\nPARITY: {'ALL MATCH (within 1e-9)' if allok else 'SOME MISMATCH - investigate'}")
