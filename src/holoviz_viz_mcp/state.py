"""In-memory state management for datasets and plots."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import pandas as pd


class StateManager:
    """Manages datasets and plot state with versioning."""

    def __init__(self) -> None:
        self.datasets: dict[str, pd.DataFrame] = {}
        self.plots: dict[str, dict[str, Any]] = {}

    # ── Datasets ──────────────────────────────────────────────────

    def store_dataset(self, df: pd.DataFrame, name: str | None = None) -> str:
        data_id = name or f"data_{uuid.uuid4().hex[:8]}"
        self.datasets[data_id] = df
        return data_id

    def get_dataset(self, name: str) -> pd.DataFrame:
        if name not in self.datasets:
            available = list(self.datasets.keys())
            raise KeyError(f"Dataset '{name}' not found. Available: {available}")
        return self.datasets[name]

    def list_datasets(self) -> dict[str, tuple[int, int, list[str]]]:
        return {
            name: (df.shape[0], df.shape[1], list(df.columns))
            for name, df in self.datasets.items()
        }

    # ── Plots ─────────────────────────────────────────────────────

    def save_plot(
        self, obj: Any, spec: dict, data_ref: str, plot_id: str | None = None
    ) -> str:
        pid = plot_id or f"plot_{uuid.uuid4().hex[:8]}"
        if pid not in self.plots:
            self.plots[pid] = {"versions": [], "current": 0}
        entry = self.plots[pid]
        entry["versions"].append(
            {
                "obj": obj,
                "spec": spec,
                "data_ref": data_ref,
                "timestamp": datetime.now().isoformat(),
            }
        )
        entry["current"] = len(entry["versions"]) - 1
        return pid

    def get_plot(self, plot_id: str, version: int | None = None) -> dict:
        if plot_id not in self.plots:
            available = list(self.plots.keys())
            raise KeyError(f"Plot '{plot_id}' not found. Available: {available}")
        entry = self.plots[plot_id]
        idx = version if version is not None else entry["current"]
        return entry["versions"][idx]

    def undo_plot(self, plot_id: str) -> dict:
        if plot_id not in self.plots:
            raise KeyError(f"Plot '{plot_id}' not found.")
        entry = self.plots[plot_id]
        if entry["current"] <= 0:
            raise ValueError("Nothing to undo — already at first version.")
        entry["current"] -= 1
        return entry["versions"][entry["current"]]

    def list_plots(self) -> dict[str, dict]:
        result = {}
        for pid, entry in self.plots.items():
            ver = entry["versions"][entry["current"]]
            result[pid] = {
                "spec": ver["spec"],
                "n_versions": len(entry["versions"]),
                "current": entry["current"],
            }
        return result


# Global instance shared across tool modules
state = StateManager()
