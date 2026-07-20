import numpy as np
import plotly.graph_objects as go
import streamlit as st
import os
import experiments as ex
import pandas as pd
from Engine import *
import Optimizer as op
import permutations as pm

ASSET_OPTIONS = ["AAPL", "MSFT", "NVDA", "SPY", "XLE", "XLF", "XLV", "XLK", "QQQ", "IWM"]
STRATEGY_REGISTRY = {
    "Moving Average": MovingAverage,
}
OPTIMIZATION_GOALS = ["Sharpe Ratio", "Max Drawdown", "Loss Rate", "Trade Expectancy", "Average Loss", "Average Win"]
VIEW_TYPES = ["Expandable Table"]


def initialize_page():
    st.set_page_config(page_title="Trading Research Dashboard", layout="wide")
    st.title("Trading Research Dashboard", text_alignment="center")


def get_sidebar_inputs():
    st.sidebar.header("Strategy Settings")
    testing_choice = st.sidebar.selectbox(
        "What kind of testing will you be doing?",
        ["Backtesting", "Optimization", "View Experiments"],
    )
    assets = st.sidebar.multiselect("Asset", ASSET_OPTIONS, default=["AAPL", "SPY"])
    balance = st.sidebar.number_input("Your Starting Balance", min_value=1000, value=10000, step=1000)
    start_date = st.sidebar.text_input("Start Date", "2020-01-01")
    end_date = st.sidebar.text_input("End Date", "2025-01-01")
    
    optimization_goal = None
    if testing_choice == "Optimization":
        optimization_goal = st.sidebar.selectbox(
            "Pick the result you want to Optimize",
            OPTIMIZATION_GOALS,
        )
    perms = None
    permutation_choice = st.sidebar.toggle("Run Permutation Tests?")
    st.session_state.permutation_choice = permutation_choice
    if permutation_choice:
        perms = st.sidebar.slider("How many Permutations", 1, 2500, 1000)
    view_type = None
    if testing_choice == "View Experiments":
        view_type = st.selectbox("What kind of Data View would you like:", VIEW_TYPES)
    return {
        "assets": assets,
        "balance": balance,
        "start_date": start_date,
        "end_date": end_date,
        "testing_choice": testing_choice,
        "optimization_goal": optimization_goal,
        "view_type": view_type,
        "perms": perms
    }


def get_weights(assets):
    if not assets:
        st.sidebar.warning("Select at least one asset to continue.")
        return None

    weights = []
    for asset in assets:
        weight = st.sidebar.number_input(
            f"{asset} weight:",
            min_value=0.0,
            max_value=1.0,
            value=1 / len(assets),
            step=0.01,
        )
        weights.append(weight)

    if abs(sum(weights) - 1) > 0.02 or sum(weights) > 1.0:
        st.sidebar.error("Sum of the weights must be close to 1.")
        return None

    st.sidebar.success("Valid weights")
    return weights


def get_strategy_settings():
    strategy_name = st.sidebar.selectbox("Select your strategy", list(STRATEGY_REGISTRY))
    strategy_class = STRATEGY_REGISTRY[strategy_name]

    if strategy_name == "Moving Average":
        fast = st.sidebar.slider("Pick the range of days for Fast MA", min_value=1, max_value=10)
        slow = st.sidebar.slider("Pick the range of days for Slow MA", min_value=20, max_value=50)
        return strategy_class, [fast, slow], strategy_name

    return strategy_class, []


def load_price_data(assets, start_date, end_date):
    generator = AssetChoosing(assets=assets, start=start_date, end=end_date)
    return generator.data, generator.dates, generator.assets


def normalize_weights(raw_weights):
    raw_weights = np.array(raw_weights, dtype=float)
    total = np.sum(raw_weights)
    if total == 0:
        return np.array([1 / len(raw_weights)] * len(raw_weights), dtype=float)
    return raw_weights / total


def create_equity_curve_figure(execution):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(execution.data.dates),
            y=list(np.sum(execution.results.equity_curves, axis=1)),
            mode="lines",
            name="Equity",
        )
    )
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Date",
        yaxis_title="Equity",
        dragmode="pan",
    )
    return fig


def render_trade_metrics(execution, label):
    st.subheader(f"Trade Info for {label}", text_alignment="center")
    st.write(f"Total number of trades: {execution.results.trade_count}")
    st.write(f"The average win: ${execution.results.avg_win:.2f}")
    st.write(f"The average loss: ${execution.results.avg_loss:.2f}")
    st.write(f"The win rate: {execution.results.win_rate * 100:.2f}%")
    st.write(f"The loss rate: {execution.results.loss_rate * 100:.2f}%")
    st.write(f"Trade Expectancy: ${execution.results.expectancy:.2f}")
    st.write(f"Total Commissions: ${execution.results.commissions:.2f}")
    st.write(f"Maximum Drawdown: {execution.results.max_drawdown * 100:.2f}%")
    st.write(f"Drawdown starts: {execution.results.drawdown_start}")
    st.write(f"Drawdown Ends: {execution.results.drawdown_end}")


def render_position_metrics(execution, label):
    st.subheader(f"Metrics for {label}", text_alignment="center")
    st.write(f"Mean of Returns: {execution.results.mean_return * 100:.6f}%")
    st.write(f"Standard Deviation: {execution.results.std_return * 100:.6f}%")
    st.write(f"IQR: {execution.results.iqr:.6f}")
    st.write(f"The Sharpe Ratio: {execution.results.sharpe:.2f}")
    st.write(f"Total Profit: {execution.results.total_profit:.2f}")
    st.write(f"Percent Gain By Strategy: {execution.results.percent_gain:.2f}")


def render_backtest_results(execution, assets):
    asset_labels = assets + [None]
    for asset_name in asset_labels:
        asset_index = assets.index(asset_name) if asset_name is not None else None
        execution.results.stats(asset_index)

        label = f"Asset {asset_name}" if asset_name is not None else "assets Combined"
        st.subheader(f"Metrics for {label}", text_alignment="center")
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            render_trade_metrics(execution, asset_name if asset_name is not None else "All")

        with col2:
            if asset_name is not None:
                st.subheader(f"Here are the trades for {asset_name}", text_alignment="center")
                fig = execution.results.show_trades(asset_index)
            else:
                st.subheader("Here is the equity curve for these assets combined", text_alignment="center")
                fig = create_equity_curve_figure(execution)

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False},
            )

        with col3:
            render_position_metrics(execution, asset_name if asset_name is not None else "All")
            if asset_name is not None:
                st.write(f"Percent Gain By Asset: {execution.results.raw_asset_return:.2f}")

        st.divider()
        st.write("")
        st.write("")
        st.write("")
        st.write("")
    st.write(st.session_state.save_backtest)




def save_loadout(execution, assets, config):
    execution.results.stats(None)
    metrics = {
            "assets": assets,
            "start_date": str(config["start_date"]),
            "end_date": str(config["end_date"]),
            "balance": config["balance"],
            "weights": [f"{weight * 100:.2f}%" for weight in config["weights"]],
            "strategy_name": config["strategy_name"],
            "trade_count": execution.results.trade_count,
            "avg_win": f"{execution.results.avg_win:.2f}",
            "avg_loss": f"{execution.results.avg_loss:.2f}",
            "win_rate": f"{execution.results.win_rate * 100:.2f}%",
            "loss rate": f"{execution.results.loss_rate * 100:.2f}%",
            "expectancy": f"{execution.results.expectancy:.2f}",
            "commissions": f"{execution.results.commissions:.2f}",
            "max_drawdown": f"{execution.results.max_drawdown * 100:.2f}%",
            "drawdown_start": str(execution.results.drawdown_start),
            "drawdown_end": str(execution.results.drawdown_end),
            "mean_return": f"{execution.results.mean_return:.4f}",
            "std": f"{execution.results.std_return:.4f}",
            "iqr": f"{execution.results.iqr:.4f}",
            "sharpe": f"{execution.results.sharpe:.2f}",
            "total_profit": f"{execution.results.total_profit:.2f}",
            "percent_gain":f"{execution.results.percent_gain:.2f}%",
            "equity_curve": list(np.sum(execution.results.equity_curves, axis=1))
        }
    st.subheader("Save this backtest run with a name. If the name exists, it'll save the run under the existing folder", text_alignment="center")

    with st.form("save_backtest_form", clear_on_submit=False):

        name = st.text_input(
            "Experiment Name",
            key="experiment_name",
            placeholder="experiment_001",
        )
        submitted = st.form_submit_button("Add this run", use_container_width=True)

        if submitted:
            if name.strip():
                if name.strip() in os.listdir("experiments"):
                    st.success(f"Saved experiment as {name.strip()} to existing folder")
                else:
                    st.success(f"Saved experiment as {name.strip()} to new folder")
                ex.save_metrics(metrics, name)
                st.session_state.form_save = True
            else:
                st.warning("Please enter an experiment name before saving.")
          




def run_backtest_dashboard(config):
    weights = get_weights(config["assets"])
    if weights is None:
        return
    config['weights']= weights

    strategy_class, strategy_params, config["strategy_name"] = get_strategy_settings()
    config["strategy_name"] += f": ({strategy_params[0]}, {strategy_params[1]})"
    if not config["assets"]:
        st.warning("Select at least one asset to run a backtest.")
        return
    st.columns(3, vertical_alignment="center")
    if st.sidebar.button("Run Backtest", type="primary", use_container_width=True) or st.session_state.save_backtest:
        st.session_state.creating_backtest = True
        prices, dates, assets = load_price_data(config["assets"], config["start_date"], config["end_date"])
        strategy = strategy_class(*strategy_params)
        execution = Execution(
            prices,
            dates=dates,
            assets=assets,
            balance=config["balance"],
            weights=weights,
            strategy=strategy,
        )
        execution.execute()
        execution.results.stats()
        equity_curve = np.sum(execution.results.equity_curves, axis=1)
        sharpe = execution.results.sharpe
        profit_factor = equity_curve[-1]/equity_curve[0] - 1
        original_metrics = [sharpe, profit_factor, dates, equity_curve]
        
        
        render_backtest_results(execution, assets)    
        st.session_state.save_backtest = True
        save_loadout(execution, assets, config)
        if st.session_state.permutation_choice:
            st.title("Permutation Testing")
            permutation_graphs(config, strategy_params, weights, original_metrics, config["perms"])


def run_optimization_dashboard(config):
    if st.sidebar.button("Start Optimization Testing"):
        prices, dates, assets = load_price_data(config["assets"], config["start_date"], config["end_date"])
        goal = config["optimization_goal"] or "Sharpe Ratio"
        out = op.Optimize(prices, dates, assets, config["balance"], MovingAverage, goal)

        st.subheader("Optimal Results for this Time Period")
        st.write(f"Optimal Fast MA: {int(round(out.x[0]))} days")
        st.write(f"Optimal Slow MA: {int(round(out.x[1]))} days")

        raw_weights = np.array(out.x[2:], dtype=float)
        weights = normalize_weights(raw_weights)
        for i, asset in enumerate(config["assets"]):
            st.write(f"Best Weight for {asset}: {weights[i]: .2f}")
        config["weights"] = weights

        optimized_execution = Execution(
            prices,
            dates=dates,
            assets=assets,
            balance=config["balance"],
            weights=weights,
            strategy=MovingAverage(int(round(out.x[0])), int(round(out.x[1]))),
        )
        optimized_execution.execute()
        optimized_execution.results.stats()
        original_equity_curve = np.sum(optimized_execution.results.equity_curves, axis = 1)
        profit_factor = original_equity_curve[-1] / original_equity_curve[0] - 1

        original_metrics = [abs(optimized_execution.results.sharpe), profit_factor, optimized_execution.data.dates, original_equity_curve ]
        strategy_param = [int(round(out.x[0])), int(round(out.x[1]))]


        optimization_dict = {
            "Sharpe Ratio": abs(optimized_execution.results.sharpe),
            "Max Drawdown": -abs(optimized_execution.results.max_drawdown),
            "Loss Rate": abs(optimized_execution.results.loss_rate),
            "Trade Expectancy": abs(optimized_execution.results.expectancy),
            "Average Loss": -abs(optimized_execution.results.avg_loss),
            "Average Win": abs(optimized_execution.results.avg_win),
        }
        st.write(f"Best {goal} Calculated: {optimization_dict[goal]:.2f}")
        if st.session_state.permutation_choice:
            permutation_graphs(config, strategy_param, weights, original_metrics, iterations = config["perms"])



def permutation_graphs(config, strategy_param, weights, original_metrics, iterations = 50):
    # permutation file should return the data needed, this function should take that data and create the graphs needed
    # this function should be looping for N permutations, the for loop should not be in the permutations file, that file should run the permutation once
    
    
    sharpes = [original_metrics[0]]
    profit_factors = [original_metrics[1]]
    fig = go.Figure()

    for i in range(iterations):
        print("\n\nIteration", i, "\n\n")
        permuted_results = pm.shuffle_returns(config, strategy_param, weights)
        if i in (90000, 90001):
            render_backtest_results(permuted_results["execution"], config["assets"])
        sharpes.append(permuted_results["sharpe"])
        profit_factors.append(permuted_results["profit_factor"])
        fig.add_trace(go.Scatter(
            x = list(permuted_results["dates"]),
            y = list(permuted_results["equity_curve"]),
            mode = "lines",
            name = f"Random Equity Curve {i}",
            line = dict(color = "grey")
        ))
        fig.add_trace(go.Scatter(
            x = list(original_metrics[2]),
            y = list(original_metrics[3]),
            mode = "lines",
            name = "Original Equity Curve",
            line = dict(color = "purple")
        ))

    fig.update_layout(
        title = "Equity Curve Permutations",
        xaxis_title = "Date",
        yaxis_title = "Equity",
        dragmode = "pan"
    )

    st.plotly_chart(
                fig,
                use_container_width=True,
                config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False}
                )
    
    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=sharpes, nbinsx= 300, name="Distribution of Sharpes"))
        fig.add_vline(x = sharpes[0], line_color = "red", line_width = 3, annotation_text = "Original")
        fig.update_layout(dragmode = "pan", xaxis_title = "Sharpes", yaxis_title = "Count")
        st.plotly_chart(
            fig, 
            config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False}
)
        better = np.sum(sharpes[1:] > sharpes[0])
        total = len(sharpes[1:])
        st.write(f"{better} permutations out of {total} were better than the original")

    with right:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=profit_factors, nbinsx= 300, name="Distribution of Profits"))
        fig.add_vline(x = profit_factors[0], line_color = "red", line_width = 3, annotation_text = "Original")
        fig.update_layout(dragmode = "pan", xaxis_title = "Profit Factors", yaxis_title = "Count")

        st.plotly_chart(
            fig, 
            config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False}
)
        better = np.sum(profit_factors[1:] > profit_factors[0])
        total = len(profit_factors[1:])
        st.write(f"{better} permutations out of {total} were better than the original")




def expandable():
    lex = ex.load_metrics()
    data_frame_config = {"start_date": st.column_config.DateColumn("Start Date", format= "MMM DD YYYY"),
                         "end_date": st.column_config.DateColumn("End Date", format= "MMM DD YYYY"),
                         "drawdown_start": st.column_config.DateColumn("Drawdown Starts", format= "MMM DD YYYY"),
                         "drawdown_end": st.column_config.DateColumn("Drawdown Ends", format= "MMM DD YYYY"),
                         "balance": st.column_config.NumberColumn("Starting Blance", format="$%d"),
                         "equity_curve": st.column_config.LineChartColumn("Equity Curve",color="violet"),
                         "assets": st.column_config.ListColumn("Assets", disabled=False, pinned=True),
                         "weights": st.column_config.ListColumn("Weights", disabled=False, pinned=True),
                         "expectancy": st.column_config.NumberColumn("Trade Expectancy", format="$%d"),
                         "total_profit": st.column_config.NumberColumn("Profit", format="$%d"),
                         "avg_win": st.column_config.NumberColumn("Average Win", format="$%d"),
                         "avg_loss": st.column_config.NumberColumn("Average Loss", format="$%d"),
                         "commissions": st.column_config.NumberColumn("Commissions", format="$%d"),
                         "strategy_name": st.column_config.TextColumn("Strategy")



                         }
    for experiment in lex:
        ex_name = experiment[0]
        df = pd.DataFrame(experiment[1])
        with st.expander(f"{ex_name}"):
            st.dataframe(df,column_config=data_frame_config, row_height= 40, )

def main():
    initialize_page()
    config = get_sidebar_inputs()

    if config["testing_choice"] == "Backtesting":
        if "save_backtest" not in st.session_state:
            st.session_state.save_backtest = False
        run_backtest_dashboard(config)
        
    elif config["testing_choice"] == "Optimization":
        st.session_state.save_backtest = False
        run_optimization_dashboard(config)
    elif config["testing_choice"] == "View Experiments":
        st.session_state.save_backtest = False
        view_type_dict = {
    "Expandable Table" : expandable
}
        view_type_dict[config['view_type']]()



if __name__ == "__main__":
    main()


    