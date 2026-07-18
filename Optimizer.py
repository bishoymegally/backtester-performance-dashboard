import numpy as np
import scipy.optimize as sco
from Engine import *

def Objective(x, prices, dates, assets, balance, strategy, goal):
    fast = int(round(x[0]))
    slow = int(round(x[1]))
    weights = np.array(x[2:], dtype=float)
    weights = weights / np.sum(weights)
    O = Execution(prices,
        dates = dates,
        assets = assets,
        balance = balance,
        weights = weights,
        strategy =  strategy(fast, slow)
        )
    O.execute()
    O.results.stats()
    optimzation_dict = {
    "Sharpe Ratio": -1 * O.results.sharpe,
    "Max Drawdown": -1 * O.results.max_drawdown,
    "Loss Rate": O.results.loss_rate,
    "Trade Expectancy": -1 * O.results.expectancy,
    "Average Loss": -1 * O.results.avg_loss,
    "Average Win": -1 * O.results.avg_win

}
    goal = optimzation_dict[goal]
    print(goal)
    print(fast)
    print(slow)
    print(weights)
    return goal

def Optimize(prices, dates, assets, balance, strategy, goal):
    n_assets = len(assets)
    x = np.array([5, 20, *([1/n_assets] * n_assets)], dtype=float)
    bounds = [(5, 10), (20, 30)] + [(0.05, 0.5) for _ in range(n_assets)]
    constraints = ({
        "type": "eq",
        "fun": lambda x: np.sum(x[2:]) - 1.0
    })
    result = sco.minimize(
    Objective,
    x,
    args=(prices, dates, assets, balance, strategy, goal),
    method='Powell',
    bounds=bounds,
    constraints=constraints
)
    print(len(x[2:]))
    print(list(x[2:]))
    print(len(list(x[2:])))
    return result





