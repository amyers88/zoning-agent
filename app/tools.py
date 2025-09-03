import pandas as pd
from typing import Dict

def budget_compare(paths: Dict[str, str]) -> str:
    """paths: {'budget': 'data/examples/budget.csv', 'draw': 'data/examples/draw.csv'}"""
    b = pd.read_csv(paths["budget"])
    d = pd.read_csv(paths["draw"])
    # Expect columns: LineItem, Amount
    m = b.merge(d, on="LineItem", suffixes=("_budget","_draw"), how="outer").fillna(0)
    m["Variance"] = m["Amount_draw"] - m["Amount_budget"]
    over = m[m["Variance"]>0][["LineItem","Amount_budget","Amount_draw","Variance"]]
    if over.empty:
        return "No overruns detected."
    return "Overruns (LineItem, Budget, Draw, Variance):\n" + over.to_string(index=False)

