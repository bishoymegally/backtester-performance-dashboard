import numpy as np
import pandas as pd
import yfinance as yf
from data_definition import *
import Engine as en

def shuffle_returns(config, strategy_param, weights):
    Data = AssetChoosing(config["assets"], config["start_date"], config["end_date"])
    prices = Data.data
    returns = ((prices[1:, :] - prices[:-1, :])/ prices[:-1, :]) + 1
    new_returns = np.random.permutation(returns)
    buy_and_hold_test = np.prod(new_returns, axis=0)
    print(buy_and_hold_test)
    returns_to_prices = np.cumprod(new_returns, axis=0)
    print(prices[0:1, :].shape, returns_to_prices.shape)
    new_prices = np.vstack((prices[0:1,:], (prices[0:1,:] * returns_to_prices)))
    random_execution = en.Execution(new_prices, Data.dates, config["assets"], config["balance"], weights, en.MovingAverage(*strategy_param))
    random_execution.execute()
    random_execution.results.stats()
    random_equity_curve = np.sum(random_execution.results.equity_curves, axis= 1)
    return {"equity_curve": random_equity_curve,
            "sharpe": random_execution.results.sharpe,
            "profit_factor": random_equity_curve[-1]/random_equity_curve[0] - 1,
            "dates": Data.dates,
            "execution": random_execution}




