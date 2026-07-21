import copy

import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from data_definition import *
#imported outside stuff first

 

#Define a class to handle the data, including validation and retrieval of prices
class Data:

    def __init__(self, data, dates, assets):
        self.is_valid_data(data) 
        self.prices, self.highs, self.lows = data
        self.dates = dates
        self.assets = assets

#Validate the data to ensure it's a numpy array and has no NaN values
    def is_valid_data(self, data):
        if not isinstance(data, list) and False:
            raise TypeError("Array must be numpy array")
        elif np.any(np.isnan(data)):
            raise ValueError("Prices Array shouldn't have any NAN values")
        else:
            return True

#Checks if there is more data available for the given day    
    def has_next(self, day):
        return day < len(self.prices) - 1

#Parent Strategy Class With update function
class Strategy:
    def __init__(self):
        self.history = []
        self.highs = []
        self.lows = []
        self.TR = []
        self.ATR = []

    
    def  update_history(self, price, high, low):
        self.history.append(price)
        self.highs.append(high)
        self.lows.append(low) 
        if len(self.history) > 1:
            range_1 = self.highs[-1] - self.lows[-1]
            range_2 = self.highs[-1] - self.history[-2]
            range_3 = self.lows[-1] - self.history[-2]
            true_range = max([range_1, range_2, range_3])
            self.TR.append(true_range)
        if len(self.TR) >= 14:
            self.ATR.append(np.mean(self.TR[-14:]))
#Strategy Checks if 5 day MA is greater than 20 day and places an order
class MovingAverage(Strategy):
    def __init__(self, fast, slow):
        super().__init__()
        self.fast = fast
        self.slow = slow

    def get_signal(self, in_position = False):
        if len(self.history) < self.slow or len(self.ATR) < 2:
            return {
                "action": None
            }
        
        if self.buy_criteria(fast=self.fast, slow=self.slow) and not in_position:
            return{
                'price':self.history[-1],
                'action': 'buy'
            }
        elif self.sell_criteria(fast= self.fast, slow= self.slow) and in_position:
            return {
                'price':self.history[-1],
                'action': 'sell'
            }
        else:
            return {
                'action': None
                }

    def ATR_Checker(self):
        if len(self.ATR) < 2:
            return 0.0
        lookback = min(50, len(self.ATR))
        ATR_MA = np.mean(self.ATR[-lookback:])
        if ATR_MA == 0:
            return 0.0
        return self.ATR[-1] / ATR_MA


    

    def buy_criteria(self, fast = 5, slow = 20):
        buy = False
        if len(self.history) < slow or len(self.ATR) < 2:
            return buy
        if np.mean(self.history[-fast:]) > np.mean(self.history[-slow:]) and self.ATR_Checker() > 1.2:
            buy = True
        return buy 
    
    def sell_criteria(self, fast, slow):
        sell = False
        if len(self.ATR) < 2:
            return False
        if not np.mean(self.history[-fast:]) > np.mean(self.history[-slow:]) or self.ATR_Checker() < 0.7:
            sell = True
        return sell


class Portfolio:
    
    def __init__(self, starting_balance):
        self.equity_curve = []
        self.trades = []
    
    def add_trade(self, data):
        self.trades.append(data)

class Results:
    def __init__(self, trades, curves, data):
        self.equity_curves = np.array(curves, dtype=float).T
        self.trades = trades
        self.data = data

    def print_all_trades(self, asset):
        print('Print all trades ran')
        print('Trades for asset:' , self.data.assets[asset])
        for i, trade in enumerate(self.trades[asset]):
            print(f'\n----------------------\nTrade {i}\n')
            for key, value in (trade.items()):
                if key == 'entry_date' or key == 'exit_date':
                    print(f'{key.title()}: {value}')
                else:
                    print(f'{key.title()}: {value:.2f}')

        self.stats(asset)
    
    def boxplot(self, asset = None):
        if asset is None:
            combined_equity = np.sum(self.equity_curves, axis = 1)
            returns = combined_equity[1:] / combined_equity[:-1] - 1
        else:
            returns = self.equity_curves[1:, asset] / self.equity_curves[:-1, asset] - 1        
        plt.boxplot(
            returns,
            showmeans=True,
            showfliers=True,
            patch_artist=True,
            boxprops=dict(facecolor="lightblue"),
            medianprops=dict(color="red"),
            meanprops=dict(marker="o", markerfacecolor="green", markersize=6),
            whiskerprops=dict(color="gray"),
            capprops=dict(color="gray")
        )
        plt.title("Strategy Return Distribution")
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def equity_chart(self, asset = None):
        if asset is not None:
            y = self.equity_curves[:, asset]
        else:
            y = np.sum(self.equity_curves, axis=1)
        plt.plot(y)
        plt.show()
    
    def histogram(self, asset = None):
        if asset is None:
            combined_equity = np.sum(self.equity_curves, axis = 1)
            returns = combined_equity[1:] / combined_equity[:-1] - 1
        else:
            returns = self.equity_curves[1:, asset] / self.equity_curves[:-1, asset] - 1
        plt.hist(returns, bins=100, edgecolor='black', alpha=0.7)
        plt.title("Strategy Return Distribution for" , self.data.assets[asset])
        plt.xlabel("Returns")
        plt.ylabel("Frequency")
        plt.grid(True, alpha=0.3)
        plt.show()

    def show_trades(self, asset):
        self.stats(asset)
        if True:
            fig = go.Figure()

            # price line
            fig.add_trace(go.Scatter(
                x=list(self.data.dates),
                y=list(np.squeeze(self.data.prices[:,asset])),
                mode="lines",
                name="Price"
            ))

            for trade in self.trades[asset]:
                fig.add_trace(go.Scatter(
                    x=[trade["entry_date"]],
                    y=[trade["entry_price"]],
                    mode="markers",
                    marker=dict(color="green", size=10, symbol="triangle-up"),
                    name="Entry"
                ))

                fig.add_trace(go.Scatter(
                    x=[trade["exit_date"]],
                    y=[trade["exit_price"]],
                    mode="markers",
                    marker=dict(color="black", size=10, symbol="x"),
                    name="Exit"
                ))

                # optional line connecting trade
                fig.add_trace(go.Scatter(
                    x=[trade["entry_date"], trade["exit_date"]],
                    y=[trade["entry_price"], trade["exit_price"]],
                    mode="lines",
                    line=dict(dash="dot"),
                    showlegend=False
                ))

            fig.update_layout(
                title=f"Backtest Visualization {self.data.assets[asset]}",
                xaxis_title="Date",
                yaxis_title="Price",
                dragmode = "pan"            
                )
        return fig



    def _compute_metrics(self, equity_curve, returns, trades, asset_name=None, raw_asset_return=None):
        self.mean_return = np.mean(returns)
        self.std_return = np.std(returns)
        self.iqr = np.percentile(returns, 75) - np.percentile(returns, 25)
        self.sharpe = (self.mean_return / self.std_return * np.sqrt(252)) if self.std_return != 0 else np.nan
        self.total_profit = equity_curve[-1] - equity_curve[0]
        self.percent_gain = (equity_curve[-1] / equity_curve[0] - 1) * 100 if equity_curve[0] != 0 else np.nan
        self.raw_asset_return = raw_asset_return

        wins = losses = wins_count = loss_count = commission = 0
        for trade in trades:
            if trade['pnl'] > 0:
                wins += trade['pnl']
                wins_count += 1
            elif trade['pnl'] < 0:
                losses += trade['pnl']
                loss_count += 1
            commission += trade['total_commission']

        self.avg_win = wins / wins_count if wins_count else 0.0
        self.avg_loss = losses / loss_count if loss_count else 0.0
        self.win_rate = wins_count / (wins_count + loss_count) if (wins_count + loss_count) else 0.0
        self.loss_rate = 1 - self.win_rate
        self.trade_count = wins_count + loss_count
        self.commissions = commission
        self.expectancy = ((self.win_rate * self.avg_win) + (self.loss_rate * self.avg_loss)) + (self.commissions/self.trade_count if self.trade_count != 0 else 0)

        self.max_drawdown = np.nan
        self.drawdown_start = None
        self.drawdown_end = None
        if len(equity_curve) > 1:
            peak = np.maximum.accumulate(equity_curve)
            drawdowns = (equity_curve - peak) / peak
            end_idx = np.argmin(drawdowns)
            start_idx = np.argmax(equity_curve[:end_idx + 1])
            self.max_drawdown = drawdowns[end_idx]
            self.drawdown_start = self.data.dates[start_idx]
            self.drawdown_end = self.data.dates[end_idx]

        self.asset_name = asset_name

    def _print_metrics(self):
        print(f'\n\nThe metrics for {self.asset_name}:')
        print(f'\nMean of returns is: {self.mean_return * 100:.6f}%')
        print(f'Standard Deviation is: {self.std_return * 100:.6f}%')
        print(f'IQR is: {self.iqr:.6f}')
        print(f'Sharpe Ratio is: {self.sharpe:.2f}')
        print(f'Total Profit: {self.total_profit:.2f}')
        print(f'Percent Gain: {self.percent_gain:.2f}%')

        if self.raw_asset_return is not None:
            print(f'Percent Gain by raw Asset Price: {self.raw_asset_return:.2f}%')

        print(f'Trade Count: {self.trade_count} Trades')
        print(f'Average Win: ${self.avg_win:.2f}')
        print(f'Probability of a win: {self.win_rate * 100:.2f}%')
        print(f'Average Loss: ${self.avg_loss:.2f}')
        print(f'Probability of a loss: {self.loss_rate * 100:.2f}%')
        print(f'Trade expectancy: ${self.expectancy:.2f}\n')

        print(f'Max drawdown: {self.max_drawdown * 100:.2f}%')
        if self.drawdown_start is not None:
            print('Start of Drawdown:', self.drawdown_start)
            print('End of Drawdown:', self.drawdown_end, '\n\n')

    def stats(self, asset = None):
        if asset is None:
            equity_curve = np.sum(self.equity_curves, axis=1)
            returns = equity_curve[1:] / equity_curve[:-1] - 1
            trades = [trade for asset_idx in range(self.equity_curves.shape[1]) for trade in self.trades[asset_idx]]
            self._compute_metrics(equity_curve, returns, trades, asset_name='All Assets')
        else:
            equity_curve = self.equity_curves[:, asset]
            returns = equity_curve[1:] / equity_curve[:-1] - 1
            trades = self.trades[asset]
            raw_asset_return = (self.data.prices[-1, asset] / self.data.prices[0, asset] - 1) * 100
            self._compute_metrics(equity_curve, returns, trades, asset_name=self.data.assets[asset], raw_asset_return=raw_asset_return)

        self._print_metrics()


class Execution:
    def __init__(self, data, dates, assets, balance, weights, strategy : Strategy): # Strategy MUST be an instance of the strategy class, NOT just a call without ()
        self.balance = balance
        self.weights = weights #should be a list of weights 0 to 1
        self.data = Data(data, dates, assets)
        self.Portfolio = Portfolio
        self.strategy_class = strategy
        self.validate(data,balance,weights,strategy)
        self.in_position = False
        self.index_equity = 0.0
        self.equity_curves = []
        self.trades = []

    def validate(self, data, balance, weights, strategy):
        if not isinstance(data, list) and False:
            raise TypeError("Prices must be turned into a numpy array")
        else:
            print('Valid Data')
        if not isinstance(balance, (int,float)) or balance <= 0:
            raise TypeError('Balance must be a valid number and non negative')
        else:
            print('Valid Balance')
        if not isinstance(weights, (list, np.ndarray)):
            raise TypeError('Weights must be a list')
        else:
            print('Valid Weights type')
        if not all(isinstance(weight, (int, float)) for weight in weights):
            raise TypeError('All items in the weights list must a valid number')
        else:
            print('Valid weight items')
        if abs(sum(weights) - 1) > 0.02:
            if False:
                raise ValueError('Sum of the weights must equal 1')
        else:
            print('Valid weights sum')
        if len(weights) != (self.data.prices.shape[1] if self.data.prices.ndim > 1 else 1):
            raise IndexError('Weights must have as many items as assets used')
        else:
            print('Valid amount of weights')

            

    
    def execute(self):
        data = self.data
        num_assets = data.prices.shape[1]
        actions = {
            'buy': self.buy,
            'sell': self.sell
        }
        
        for asset in range(num_assets):
            # for each asset, its balance is defined as the total portfolio balance times the weight chosen for the balance, the first item in the asset curve is the balance, the asset curve updates by adding the profit from each day, NOT by multiplying the balance by the returns.
            balance = self.balance * self.weights[asset]
            portfolio = self.Portfolio(balance)
            self.current_trade = {}
            self.in_position = False
            self.index_equity = 0.0
            strategy = copy.deepcopy(self.strategy_class)
            if hasattr(strategy, "history"):
                strategy.history = []
                strategy.highs = []
                strategy.lows = []
                strategy.TR = []
                strategy.ATR = []
            day = -1
            while data.has_next(day):
                day += 1
                strategy.update_history(data.prices[day, asset], data.highs[day, asset], data.lows[day, asset])

                if self.in_position:
                    price_now = data.prices[day, asset]
                    price_yesterday = data.prices[day - 1, asset]
                    daily_return = price_now / price_yesterday - 1
                    self.index_equity *= ((daily_return + 1))
                    portfolio.equity_curve.append((portfolio.equity_curve[-1] + self.index_equity * daily_return))  # the next item in the equity curve is the previous item plus the profit for the day (profit caluclated as returns time equity invested)
                else:
                    if len(portfolio.equity_curve) == 0:
                        portfolio.equity_curve.append(balance)
                    else:
                        portfolio.equity_curve.append(portfolio.equity_curve[-1])
                order = strategy.get_signal(self.in_position)
                if order['action'] is not None:  # and eventually risk not breached
                    actions[order['action']](order['price'], portfolio, day)

            if self.in_position:
                self.sell(strategy.history[-1], portfolio, day)
            self.trades.append(portfolio.trades)
            self.equity_curves.append(portfolio.equity_curve)
            portfolio = None

        self.results = Results(self.trades, self.equity_curves, self.data)


                
                
    def buy(self, price, portfolio, day):
        self.in_position = True
        self.current_trade['entry_date'] = self.data.dates[day]
        self.current_trade['shares'] = int(portfolio.equity_curve[-1] // price)
        self.current_trade['start_equity'] = self.current_trade['shares'] * price
        self.current_trade['entry_price'] = price
        self.current_trade['entry_commission'] = -0.005 * self.current_trade['shares']
        portfolio.equity_curve[-1] += self.current_trade['entry_commission']
        self.index_equity = self.current_trade['start_equity']





    def sell(self, price, portfolio, day):
        self.in_position = False
        self.current_trade['exit_price'] = price
        self.current_trade['exit_date'] = self.data.dates[day]
        self.current_trade['returns'] = self.current_trade['exit_price'] / self.current_trade['entry_price'] - 1 # everyitme we close a trade we record price and day and returns but most importantly, we store the trade into the portfolio trades and reset current trade to None
        self.current_trade['exit_commission'] = -0.005 * self.current_trade['shares']
        portfolio.equity_curve[-1] += self.current_trade['exit_commission']

        self.current_trade['total_commission'] = (self.current_trade['exit_commission'] + self.current_trade["exit_commission"])
        self.current_trade['pnl'] = (self.current_trade['exit_price'] - self.current_trade['entry_price']) * self.current_trade['shares']
        portfolio.trades.append(self.current_trade)
        self.current_trade = {}
        self.index_equity = 0.0
 
















       




