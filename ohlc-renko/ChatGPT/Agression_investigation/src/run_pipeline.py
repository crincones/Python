"""
Pipeline reproduzivel completo (secao 31 do CLAUDE.md).

    CSV -> VALIDACAO -> FEATURES -> TARGETS -> EDA -> BASELINES ->
    WALK-FORWARD -> CATBOOST -> IMPORTANCIA -> ROBUSTEZ -> THRESHOLD ->
    SIMULACAO ECONOMICA -> EXPORT -> NTSL

Uso:
    python run_pipeline.py                 # tudo
    python run_pipeline.py --skip-slow     # sem grid search nem teste nulo
    python run_pipeline.py --only 04 06    # apenas as etapas listadas
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime

from config import PROJECT_ROOT, RESULTS_DIR, SEED

STEPS = [
    ("01", "validacao + dataset", "fast"),
    ("02", "teste de vazamento", "fast"),
    ("04", "analise exploratoria", "fast"),
    ("05", "baselines por grupo de informacao", "medium"),
    ("06", "grid search CatBoost + sensibilidade", "slow"),
    ("07", "importancia e estabilidade", "medium"),
    ("08", "threshold + teste final out-of-sample", "medium"),
    ("09", "robustez + teste nulo", "slow"),
    ("12", "export NTSL + auditoria", "medium"),
]


def environment() -> dict:
    import catboost
    import numpy
    import pandas
    import sklearn
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        rev = ""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "python": sys.version, "platform": platform.platform(),
        "seed": SEED, "git_rev": rev,
        "versions": {"pandas": pandas.__version__, "numpy": numpy.__version__,
                     "scikit-learn": sklearn.__version__,
                     "catboost": catboost.__version__},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    def wanted(code, speed):
        if args.only:
            return code in args.only
        return not (args.skip_slow and speed == "slow")

    log = {"environment": environment(), "steps": []}
    t_all = time.time()

    for code, name, speed in STEPS:
        if not wanted(code, speed):
            log["steps"].append({"step": code, "name": name,
                                 "status": "pulado"})
            print(f"[{code}] {name}: PULADO")
            continue
        print(f"\n[{code}] {name} ...")
        t0 = time.time()
        try:
            _run_step(code)
            st = "ok"
        except Exception as e:                       # noqa: BLE001
            st = f"erro: {type(e).__name__}: {e}"
            print(f"    FALHOU: {st}")
        dt = round(time.time() - t0, 1)
        log["steps"].append({"step": code, "name": name, "status": st,
                             "seconds": dt})
        print(f"    {st} ({dt}s)")

    log["total_seconds"] = round(time.time() - t_all, 1)
    (RESULTS_DIR / "00_pipeline_run.json").write_text(
        json.dumps(log, indent=2), encoding="utf-8")
    print(f"\nconcluido em {log['total_seconds']}s — "
          f"log em results/00_pipeline_run.json")


def _run_step(code: str) -> None:
    if code == "01":
        import build_dataset
        build_dataset.build()
    elif code == "02":
        import leakage_test
        leakage_test.assert_no_future_dependency()
    elif code == "04":
        import eda
        eda.run()
    elif code == "05":
        import baselines
        for suf in ("p2c2", "p3c2", "p2c3", "p3c3"):
            baselines.run(suf)
    elif code == "06":
        import train_catboost as tc
        grid_res, best = {}, {}
        for t in ("p2c2", "p3c2"):
            g = tc.grid_search(t)
            grid_res[t] = g
            best[t] = g.iloc[0].to_dict()
        lag_res = tc.lag_sensitivity("p2c2")
        ma_res = tc.ma_period_sensitivity("p2c2")
        tc._write_md(grid_res, lag_res, ma_res, best)
        (RESULTS_DIR / "06_best_config.json").write_text(
            json.dumps(best, indent=2, default=float), encoding="utf-8")
    elif code == "07":
        import explain
        explain.run()
    elif code == "08":
        import final_model
        final_model.run("p2c2", "STRUCT+AGG",
                        dict(depth=4, learning_rate=0.02, l2_leaf_reg=10.0), 5)
    elif code == "09":
        import robustness
        robustness.run("p2c2", n_perm=20)
    elif code == "12":
        import export_ntsl
        export_ntsl.run()
    else:
        raise ValueError(code)


if __name__ == "__main__":
    main()
