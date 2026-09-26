import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

complaints = pd.read_csv(r"c:\Users\maxh6\Downloads\Northwind_Challenge_Data\northwind_complaints.csv")

kpis = pd.read_csv(r"c:\Users\maxh6\Downloads\Northwind_Challenge_Data\northwind_monthly_kpis.csv")

costs = pd.read_csv(r"c:\Users\maxh6\Downloads\Northwind_Challenge_Data\northwind_unit_costs.csv")


Accounts = 1800000
Months_To_Project = 12

def _r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot

def regressions(kpis):
    kpis = kpis.copy()
    kpis["net"] = kpis["complaints_opened"]-kpis["complaints_closed"]
    kpis["backlog"]=kpis["net"].cumsum()

    x1 = kpis["avg_days_to_close"].values
    y1 = kpis["regulator_satisfaction_score_of_5"]
    slope1, intercept1 = np.polyfit(x1,y1,1)
    r2_1 = _r_squared(y1, intercept1 + slope1 * x1)

    x2 = kpis["backlog"].values
    y2 = kpis["avg_days_to_close"].values
    slope2, intercept2 = np.polyfit(x2, y2, 1)
    r2_2 = _r_squared(y2, intercept2 + slope2 * x2)
    
    x3 = kpis["avg_days_to_close"].values
    y3 = kpis["cost_to_serve_per_account"].values
    slope3, intercept3 = np.polyfit(x3, y3, 1)
    r2_3 = _r_squared(y3, intercept3 + slope3 * x3)

    return (slope1, intercept1, r2_1,
        slope2, intercept2, r2_2,
        slope3, intercept3, r2_3)



(slope1, intercept1, r2_1,
 slope2, intercept2, r2_2,
 slope3, intercept3, r2_3) = regressions(kpis)


print("=== Fitted regressions (this IS the model — no black box) ===")
print(f"  regulator_score      = {intercept1:.4f} + {slope1:.5f} * avg_days_to_close   (R^2={r2_1:.3f})")
print(f"  avg_days_to_close    = {intercept2:.4f} + {slope2:.6f} * backlog             (R^2={r2_2:.3f})")
print(f"  cost_to_serve/acct   = {intercept3:.4f} + {slope3:.4f} * avg_days_to_close    (R^2={r2_3:.3f})")
print()