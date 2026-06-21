"""
scripts/detection_validity.py: a second supervised model, separate from the
forecaster. It predicts which detections are likely to be rejected on review, so
enforcement can auto-triage probable false/contested reports instead of chasing them.

Unlike the forecaster (where a base rate explains much of the signal), this task has
real per-record labels (validation_status) and the model finds genuine structure. We
train on reviewed records only (approved vs rejected), hold out a stratified test
split, and report ROC-AUC, PR-AUC, and an operational triage table (flag the top X%
most-suspect reports, and see how many real rejections that catches).

Excludes data_sent_to_scita to avoid review-time leakage.
Reads data/parkpulse_clean_records.parquet. Writes outputs/detection_metrics.md + .json.
"""
from __future__ import annotations
import json
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
import lightgbm as lgb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(ROOT, "data", "parkpulse_clean_records.parquet")
FLAGS = ["f_main_road", "f_double", "f_crossing", "f_signal", "f_footpath", "f_bsh"]
CATS = ["vehicle_class", "police_station", "month"]


def load():
    df = pd.read_parquet(PARQUET)
    df = df[df["validation_status"].isin(["approved", "rejected"])].copy()
    df["y"] = (df["validation_status"] == "rejected").astype(int)
    lat = "latitude" if "latitude" in df.columns else "lat"
    lon = "longitude" if "longitude" in df.columns else "lon"
    num = ["obstruct_w", "pcu", "expo_weight", "hour", "dow", lat, lon]
    df["is_peak"] = df["is_peak"].astype(int)
    df["is_weekend"] = df["is_weekend"].astype(int)
    num += ["is_peak", "is_weekend"]
    feats = num + FLAGS + CATS
    feats = [c for c in feats if c in df.columns]
    X = df[feats].copy()
    for c in CATS:
        if c in X.columns:
            X[c] = X[c].astype("category")
    for c in FLAGS:
        if c in X.columns:
            X[c] = X[c].astype(int)
    return X, df["y"].values, [c for c in CATS if c in X.columns]


def triage_table(y_true, p):
    order = np.argsort(-p)
    n = len(p)
    total_rej = y_true.sum()
    rows = []
    for frac in (0.10, 0.20, 0.30):
        k = int(n * frac)
        sel = order[:k]
        caught = y_true[sel].sum()
        rows.append({"flag_pct": int(frac * 100), "precision": caught / k,
                     "recall": caught / total_rej, "lift": (caught / k) / (total_rej / n)})
    return rows


def main():
    X, y, cats = load()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    clf = lgb.LGBMClassifier(
        n_estimators=400, learning_rate=0.05, num_leaves=48, subsample=0.8,
        colsample_bytree=0.8, min_child_samples=80, random_state=42, n_jobs=-1, verbose=-1)
    clf.fit(Xtr, ytr, categorical_feature=cats)
    p = clf.predict_proba(Xte)[:, 1]

    auc = roc_auc_score(yte, p)
    ap = average_precision_score(yte, p)
    base = yte.mean()
    tri = triage_table(yte, p)
    imp = (pd.Series(clf.feature_importances_, index=X.columns)
           .sort_values(ascending=False).head(10))

    out = {"n_train": int(len(ytr)), "n_test": int(len(yte)), "base_rate": float(base),
           "roc_auc": float(auc), "pr_auc": float(ap), "triage": tri,
           "top_features": [{"f": k, "gain": int(v)} for k, v in imp.items()]}
    with open(os.path.join(ROOT, "outputs", "detection_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)

    L = ["# ParkPulse: detection-validity model\n",
         "A separate supervised model that predicts whether a detection will be rejected "
         "on review, from the report's own attributes (vehicle, location, time, violation "
         "type). It auto-triages probable false or contested reports so patrols are not sent "
         "to chase them. Trained on reviewed records only, with a stratified hold-out.\n",
         f"- Reviewed records: {len(y):,} (train {len(ytr):,} / test {len(yte):,}). "
         f"Rejection base rate: **{base*100:.1f}%**.",
         f"- **ROC-AUC {auc:.3f}**, **PR-AUC {ap:.3f}** (vs {base:.3f} for a no-skill model). "
         "Real structure, not a base rate.\n",
         "## Triage: flag the most-suspect reports\n",
         "| Flag the top | Precision (are really rejected) | Recall (of all rejections) | Lift |",
         "|---|--:|--:|--:|"]
    for r in tri:
        L.append(f"| {r['flag_pct']}% most-suspect | {r['precision']*100:.0f}% | "
                 f"{r['recall']*100:.0f}% | {r['lift']:.1f}x |")
    L.append("\n## Top features (gain)\n")
    for k, v in imp.items():
        L.append(f"- `{k}`")
    with open(os.path.join(ROOT, "outputs", "detection_metrics.md"), "w") as f:
        f.write("\n".join(L))

    print(f"ROC-AUC {auc:.3f} | PR-AUC {ap:.3f} | base {base:.3f}")
    for r in tri:
        print(f"  top {r['flag_pct']}% flagged -> precision {r['precision']*100:.0f}%, "
              f"recall {r['recall']*100:.0f}%, lift {r['lift']:.1f}x")
    print("top features:", list(imp.index[:6]))
    print("-> outputs/detection_metrics.md/.json")


if __name__ == "__main__":
    main()
