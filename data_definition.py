import numpy as np
import pandas as pd
import yfinance as yf


class AssetChoosing:
    def __init__(self, assets: list[str], start, end):
        self.assets = assets
        self.start = start
        self.end = end
        self.data_generation()

    def data_generation(self):
        price_frames = []
        high_frames = []
        low_frames = []
        for asset in self.assets:
            data = yf.download(asset, start=self.start, end=self.end)["Close"]
            highs = yf.download(asset, start=self.start, end=self.end)["High"]
            lows = yf.download(asset, start=self.start, end=self.end)["Low"]
            if isinstance(data, pd.DataFrame):
                series = data.iloc[:, 0]
                highs = highs.iloc[:, 0]
                lows = lows.iloc[:, 0]
            else:
                series = data


            price_frames.append(series.to_frame(name=asset))
            high_frames.append(highs.to_frame(name=asset))
            low_frames.append(lows.to_frame(name=asset))


        combined = pd.concat(price_frames, axis=1, join="inner").dropna()
        combined_highs = pd.concat(high_frames, axis=1, join="inner").dropna()
        combined_lows = pd.concat(low_frames, axis=1, join="inner").dropna()

        self.close = combined.to_numpy(dtype=float)
        self.highs = combined_highs.to_numpy(dtype=float)
        self.lows = combined_lows.to_numpy(dtype=float)
        self.data = [self.close, self.highs, self.lows]
        self.dates = combined.index
        self.assets = list(combined.columns)

