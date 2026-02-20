from collections.abc import Sequence
from dataclasses import dataclass, fields

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


@dataclass(kw_only=True)
class SamplesMetrics:
    samples: np.ndarray | Sequence

    percentiles: np.ndarray | None = None
    std: float | None = None
    mean: float | None = None
    max: float | None = None
    min: float | None = None
    median: float | None = None
    label: str | None = None

    def __post_init__(self):
        if not isinstance(self.samples, np.ndarray):
            self.samples = np.asarray(self.samples)
        assert len(self.samples.shape) == 1
        self.compute()

    def compute(self) -> None:
        if self.percentiles is None:
            q = list(range(101))
            res = np.percentile(a=self.samples, q=q)
            self.percentiles = res
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

    def to_df(self, new_label: str | None = None):
        label = self.label if new_label is None else new_label
        res: dict[str, list] = {}
        if label is not None:
            res["label"] = [label]
        for field in fields(SamplesMetrics):
            if field.name in ("samples", "percentiles"):
                continue
            res[field.name] = [getattr(self, field.name)]
        df1 = pd.DataFrame(data=res)

        res2: dict[str, list | np.ndarray | None] = {
            "percentile": list(range(101)),
            "percentile_value": self.percentiles,
        }
        if label is not None:
            res2["label"] = [label] * 101
        df2 = pd.DataFrame(data=res2)
        return df1, df2


@dataclass(kw_only=True)
class SamplesMetricsGroup:
    elements: list[SamplesMetrics]

    def __post_init__(self):
        assert len(self.elements) > 1

    def to_df(self):
        sub_df1s = []
        sub_df2s = []
        for e in self.elements:
            df1, df2 = e.to_df()
            sub_df1s.append(df1)
            sub_df2s.append(df2)
        return pd.concat(sub_df1s, ignore_index=True), pd.concat(
            sub_df2s, ignore_index=True
        )
