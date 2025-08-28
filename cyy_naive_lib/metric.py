from dataclasses import dataclass, fields
import pandas as pd


import numpy as np


@dataclass(kw_only=True)
class SamplesMetrics:
    samples: np.ndarray

    percentiles: np.ndarray | None = None
    std: float | None = None
    mean: float | None = None
    max: float | None = None
    min: float | None = None
    median: float | None = None

    def __post_init__(self):
        assert len(self.samples.shape) == 1
        self.compute()

    def compute(self) -> None:
        if self.percentiles is None:
            q = list(range(101))
            res = np.percentile(a=self.samples, q=q)
            self.percentiles = res
            # dict(zip(q, res, strict=False))
        if self.std is None:
            self.std = float(np.std(a=self.samples))
        if self.mean is None:
            self.mean = float(np.mean(a=self.samples))
        if self.max is None:
            self.max = float(np.max(a=self.samples))
        if self.min is None:
            self.min = float(np.min(a=self.samples))
        if self.median is None:
            self.median = float(np.median(a=self.samples))


@dataclass(kw_only=True)
class SamplesMetricsGroup:
    elements: list[SamplesMetrics]

    def __post_init__(self):
        assert len(self.elements) > 1

    def to_df(self, element_labels: list[str]):
        assert len(self.elements) == len(element_labels)
        res = {"label": element_labels}
        for field in fields(SamplesMetrics):
            if field.name == "percentiles":
                continue
            res[field.name] = [getattr(e, field.name) for e in self.elements]
        df1 = pd.DataFrame(data=res)
        df2 = pd.DataFrame(
            np.array([e.percentiles for e in self.elements]), columns=element_labels
        )
        return df1, df2
