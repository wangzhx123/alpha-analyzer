import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_analyzer import BaseAnalyzer, AnalysisResult


class FillRateAnalyzer(BaseAnalyzer):
    """
    Fill Rate Analyzer: Compares alpha targets at time T with position changes at time T+1

    Supports all 4 interfaces:
    - Overview: High-level fill rate statistics across all data
    - Time Event: Fill rates for all tickers at specific time
    - Ticker Timeline: Fill rate trends for specific ticker over time
    - Deep Analysis: Detailed breakdown for specific ti+ticker
    """

    @property
    def name(self) -> str:
        return "Fill Rate Analysis"

    def _get_fill_data(
        self,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        ti_filter=None,
        ticker_filter=None,
    ):
        """Common logic to calculate fill rates"""
        # Sort data
        split_df = split_alpha_df.sort_values(["alphaid", "ticker", "time"])
        pos_df = realtime_pos_df.sort_values(["alphaid", "ticker", "time"])

        # Get unique times
        times = sorted(split_df["time"].unique())
        fill_data = []

        for i in range(len(times) - 1):
            t_current = times[i]
            t_next = times[i + 1]

            # Get alpha at current time and positions at both times
            alphas = split_df[split_df["time"] == t_current]
            pos_current = pos_df[pos_df["time"] == t_current]
            pos_next = pos_df[pos_df["time"] == t_next]

            for _, alpha_row in alphas.iterrows():
                alphaid, ticker = alpha_row["alphaid"], alpha_row["ticker"]
                target_alpha = alpha_row["volume"]

                # Find positions
                curr_pos = pos_current[
                    (pos_current["alphaid"] == alphaid)
                    & (pos_current["ticker"] == ticker)
                ]
                next_pos = pos_next[
                    (pos_next["alphaid"] == alphaid) & (pos_next["ticker"] == ticker)
                ]

                if not curr_pos.empty and not next_pos.empty:
                    pos_change = (
                        next_pos["realtime_pos"].iloc[0]
                        - curr_pos["realtime_pos"].iloc[0]
                    )
                    fill_rate = (
                        pos_change / target_alpha if abs(target_alpha) > 1e-6 else 0
                    )

                    fill_data.append(
                        {
                            "time_from": t_current,
                            "time_to": t_next,
                            "alphaid": alphaid,
                            "ticker": ticker,
                            "target_alpha": target_alpha,
                            "position_change": pos_change,
                            "fill_rate": fill_rate,
                        }
                    )

        df = pd.DataFrame(fill_data)

        # Apply filters
        if ti_filter is not None:
            df = df[df["time_from"] == ti_filter]
        if ticker_filter is not None:
            df = df[df["ticker"] == ticker_filter]

        return df

    def _analyze_overview(
        self,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Overview: All tickers, all times"""
        df = self._get_fill_data(split_alpha_df, realtime_pos_df)
        finite_df = df[np.isfinite(df["fill_rate"])]

        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="No analyzable trades found",
                details="All trades had zero target alpha",
            )

        # High-level statistics
        best_performer = finite_df.loc[finite_df["fill_rate"].idxmax()]
        worst_performer = finite_df.loc[finite_df["fill_rate"].idxmin()]

        summary = (
            f"Total trades: {len(df)} | Analyzable: {len(finite_df)} | "
            f"Mean fill rate: {finite_df['fill_rate'].mean():.3f}"
        )

        details = (
            f"Best performer: {best_performer['ticker']} ({best_performer['fill_rate']:.3f})\\n"
            f"Worst performer: {worst_performer['ticker']} ({worst_performer['fill_rate']:.3f})"
        )

        # Simple histogram
        fig, ax = plt.subplots(1, 1, figsize=(8, 5))
        ax.hist(finite_df["fill_rate"], bins=20, alpha=0.7, color="skyblue")
        ax.axvline(x=1.0, color="red", linestyle="--", label="Perfect Fill")
        ax.set_xlabel("Fill Rate")
        ax.set_ylabel("Count")
        ax.set_title("Fill Rate Distribution (All)")
        ax.legend()
        plt.tight_layout()
        plot_path = "/tmp/fill_rate_overview.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )

    def _analyze_time_event(
        self,
        ti: int,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Time Event: All tickers at specific time"""
        df = self._get_fill_data(split_alpha_df, realtime_pos_df, ti_filter=ti)
        finite_df = df[np.isfinite(df["fill_rate"])]

        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades found for ti={ti}",
            )

        # Group by ticker
        ticker_stats = (
            finite_df.groupby("ticker")["fill_rate"].agg(["mean", "count"]).round(3)
        )

        summary = (
            f"ti={ti}: {len(ticker_stats)} tickers analyzed | "
            f"Overall mean: {finite_df['fill_rate'].mean():.3f}"
        )

        details = "Per-ticker performance:\\n"
        for ticker, stats in ticker_stats.iterrows():
            details += f"  {ticker}: {stats['mean']:.3f} ({stats['count']} trades)\\n"

        # Bar chart by ticker
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        ticker_stats["mean"].plot(kind="bar", ax=ax, color="lightcoral")
        ax.axhline(y=1.0, color="red", linestyle="--", label="Perfect Fill")
        ax.set_xlabel("Ticker")
        ax.set_ylabel("Mean Fill Rate")
        ax.set_title(f"Fill Rate by Ticker (ti={ti})")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plot_path = f"/tmp/fill_rate_ti_{ti}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )

    def _analyze_ticker_timeline(
        self,
        ticker: str,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Ticker Timeline: Specific ticker across all times"""
        df = self._get_fill_data(split_alpha_df, realtime_pos_df, ticker_filter=ticker)
        finite_df = df[np.isfinite(df["fill_rate"])]

        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades found for ticker={ticker}",
            )

        # Group by time
        time_stats = (
            finite_df.groupby("time_from")["fill_rate"].agg(["mean", "count"]).round(3)
        )

        summary = (
            f"ticker={ticker}: {len(time_stats)} time periods | "
            f"Overall mean: {finite_df['fill_rate'].mean():.3f}"
        )

        details = "Timeline performance:\\n"
        for time_period, stats in time_stats.iterrows():
            details += (
                f"  ti={time_period}: {stats['mean']:.3f} ({stats['count']} trades)\\n"
            )

        # Timeline plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        time_stats.index = range(len(time_stats))  # Sequential index for plotting
        ax.plot(
            time_stats.index, time_stats["mean"], marker="o", linewidth=2, markersize=6
        )
        ax.axhline(y=1.0, color="red", linestyle="--", label="Perfect Fill")
        ax.set_xlabel("Time Period")
        ax.set_ylabel("Mean Fill Rate")
        ax.set_title(f"Fill Rate Timeline ({ticker})")
        ax.legend()
        plt.tight_layout()
        plot_path = f"/tmp/fill_rate_{ticker}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )

    def _analyze_deep(
        self,
        ti: int,
        ticker: str,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Deep Analysis: Specific ti+ticker combination"""
        df = self._get_fill_data(
            split_alpha_df, realtime_pos_df, ti_filter=ti, ticker_filter=ticker
        )
        finite_df = df[np.isfinite(df["fill_rate"])]

        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades for ti={ti}, ticker={ticker}",
            )

        summary = (
            f"ti={ti}, ticker={ticker}: {len(finite_df)} trades | "
            f"Net fill rate: {finite_df['position_change'].sum() / finite_df['target_alpha'].sum():.3f}"
        )

        # Trade-by-trade breakdown
        details = "Trade-by-trade breakdown:\\n"
        for _, trade in finite_df.iterrows():
            details += (
                f"  {trade['alphaid']}: target={trade['target_alpha']:.0f}, "
                f"actual={trade['position_change']:.0f}, fill_rate={trade['fill_rate']:.3f}\\n"
            )

        # Detailed 2x2 plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # Target vs actual scatter
        ax1.scatter(
            finite_df["target_alpha"], finite_df["position_change"], s=100, alpha=0.7
        )
        max_val = max(
            finite_df["target_alpha"].max(), finite_df["position_change"].max()
        )
        min_val = min(
            finite_df["target_alpha"].min(), finite_df["position_change"].min()
        )
        ax1.plot([min_val, max_val], [min_val, max_val], "r--", label="Perfect Fill")
        ax1.set_xlabel("Target Alpha")
        ax1.set_ylabel("Position Change")
        ax1.set_title("Target vs Actual")
        ax1.legend()

        # Fill rate by alphaid
        if len(finite_df) > 1:
            finite_df.set_index("alphaid")["fill_rate"].plot(
                kind="bar", ax=ax2, color="lightgreen"
            )
        else:
            ax2.bar(["Trade"], [finite_df["fill_rate"].iloc[0]], color="lightgreen")
        ax2.axhline(y=1.0, color="red", linestyle="--", label="Perfect Fill")
        ax2.set_xlabel("Alpha ID")
        ax2.set_ylabel("Fill Rate")
        ax2.set_title("Fill Rate by Alpha ID")
        ax2.legend()

        # Position changes
        ax3.bar(
            range(len(finite_df)),
            finite_df["position_change"],
            color="orange",
            alpha=0.7,
            label="Actual",
        )
        ax3.bar(
            range(len(finite_df)),
            finite_df["target_alpha"],
            alpha=0.5,
            color="blue",
            label="Target",
        )
        ax3.set_xlabel("Trade Index")
        ax3.set_ylabel("Volume")
        ax3.set_title("Target vs Actual Volume")
        ax3.legend()

        # Summary metrics
        ax4.axis("off")
        metrics_text = f"""Summary Metrics:

Total Trades: {len(finite_df)}
Mean Fill Rate: {finite_df['fill_rate'].mean():.3f}
Std Fill Rate: {finite_df['fill_rate'].std():.3f}
Min Fill Rate: {finite_df['fill_rate'].min():.3f}
Max Fill Rate: {finite_df['fill_rate'].max():.3f}

Total Target: {finite_df['target_alpha'].sum():.0f}
Total Actual: {finite_df['position_change'].sum():.0f}
Net Fill Rate: {finite_df['position_change'].sum() / finite_df['target_alpha'].sum():.3f}
        """
        ax4.text(
            0.1,
            0.9,
            metrics_text,
            transform=ax4.transAxes,
            fontsize=10,
            verticalalignment="top",
            fontfamily="monospace",
        )

        plt.tight_layout()
        plot_path = f"/tmp/fill_rate_detailed_{ti}_{ticker}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )
