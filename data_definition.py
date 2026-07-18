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
        for asset in self.assets:
            data = yf.download(asset, start=self.start, end=self.end)["Close"]
            if isinstance(data, pd.DataFrame):
                series = data.iloc[:, 0]
            else:
                series = data
            price_frames.append(series.to_frame(name=asset))

        combined = pd.concat(price_frames, axis=1, join="inner").dropna()
        self.data = combined.to_numpy(dtype=float)
        self.dates = combined.index
        self.assets = list(combined.columns)

