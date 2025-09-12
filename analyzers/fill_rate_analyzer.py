import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_analyzer import BaseAnalyzer, AnalysisResult


def format_time(timestamp):
    """Convert timestamp like 940000000 to readable format like 9:40"""
    if timestamp == -1:
        return "PREV"
    
    # Convert timestamp to string and extract hour/minute
    time_str = str(int(timestamp))
    if len(time_str) >= 9:  # Format: 940000000
        hour = int(time_str[0:2]) if len(time_str) >= 10 else int(time_str[0:1])
        minute = int(time_str[-8:-6])
        return f"{hour}:{minute:02d}"
    else:
        return str(timestamp)


class FillRateAnalyzer(BaseAnalyzer):
    """
    Fill Rate Analyzer: Compares alpha targets at time T with position changes at time T+1

    Supports all 4 interfaces:
    - Overview: High-level fill rate statistics across all data
    - Time Event: Fill rates for all tickers at specific time
    - Ticker Timeline: Fill rate trends for specific ticker over time
    - Deep Analysis: Detailed breakdown for specific ti+ticker
    """

    def _get_output_dir(self):
        """Get output directory from analyzer instance or default to /tmp"""
        if hasattr(self, 'analyzer_instance') and hasattr(self.analyzer_instance, 'output_dir'):
            return str(self.analyzer_instance.output_dir)
        return "/tmp"

    def _generate_detail_report(self, analysis_result, fill_data_df, 
                               incheck_alpha_df, merged_df, split_alpha_df, 
                               realtime_pos_df, market_df, analysis_type, 
                               ti=None, ticker=None):
        """Generate comprehensive detail report with all analysis data and source CSV"""
        report_path = f"{self._get_output_dir()}/detail_report.txt"
        
        with open(report_path, 'w') as f:
            # Header
            f.write("="*80 + "\n")
            f.write("FILL RATE ANALYSIS - DETAILED REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Analysis Type: {analysis_type}\n")
            if ti is not None:
                f.write(f"Time Filter: {ti} ({format_time(ti)})\n")
            if ticker is not None:
                f.write(f"Ticker Filter: {ticker}\n")
            f.write("\n")
            
            # Analysis Summary
            f.write("-"*50 + "\n")
            f.write("ANALYSIS SUMMARY\n")
            f.write("-"*50 + "\n")
            f.write(f"Summary: {analysis_result.summary}\n")
            if analysis_result.details:
                f.write(f"\nDetails:\n{analysis_result.details}\n")
            f.write(f"Plot Generated: {analysis_result.plot_path}\n\n")
            
            # Fill Data Analysis
            if not fill_data_df.empty:
                f.write("-"*50 + "\n")
                f.write("FILL DATA ANALYSIS\n")
                f.write("-"*50 + "\n")
                f.write(f"Total Records: {len(fill_data_df)}\n")
                finite_df = fill_data_df[np.isfinite(fill_data_df["fill_rate"])]
                f.write(f"Analyzable Records: {len(finite_df)}\n")
                
                if not finite_df.empty:
                    f.write(f"Mean Fill Rate: {finite_df['fill_rate'].mean():.6f}\n")
                    f.write(f"Std Fill Rate: {finite_df['fill_rate'].std():.6f}\n")
                    f.write(f"Min Fill Rate: {finite_df['fill_rate'].min():.6f}\n")
                    f.write(f"Max Fill Rate: {finite_df['fill_rate'].max():.6f}\n")
                    f.write(f"Total Intended Trades: {finite_df['intended_trade'].sum():,.0f}\n")
                    f.write(f"Total Actual Trades: {finite_df['actual_trade'].sum():,.0f}\n")
                    f.write(f"Net Fill Rate: {finite_df['actual_trade'].sum() / finite_df['intended_trade'].sum():.6f}\n")
                    
                    # Top performers
                    if len(finite_df) >= 5:
                        f.write("\nTop 5 Performers (by fill rate):\n")
                        top_performers = finite_df.nlargest(5, 'fill_rate')
                        for i, (_, row) in enumerate(top_performers.iterrows(), 1):
                            f.write(f"  {i}. {row['ticker']} ({format_time(row['time_from'])}→{format_time(row['time_to'])}): "
                                   f"{row['fill_rate']:.3f} (intended: {row['intended_trade']:,.0f}, actual: {row['actual_trade']:,.0f})\n")
                        
                        f.write("\nBottom 5 Performers (by fill rate):\n")
                        bottom_performers = finite_df.nsmallest(5, 'fill_rate')
                        for i, (_, row) in enumerate(bottom_performers.iterrows(), 1):
                            f.write(f"  {i}. {row['ticker']} ({format_time(row['time_from'])}→{format_time(row['time_to'])}): "
                                   f"{row['fill_rate']:.3f} (intended: {row['intended_trade']:,.0f}, actual: {row['actual_trade']:,.0f})\n")
                
                f.write("\n" + "-"*30 + "\n")
                f.write("COMPLETE FILL DATA\n")
                f.write("-"*30 + "\n")
                for _, row in fill_data_df.iterrows():
                    f.write(f"Time: {format_time(row['time_from'])}→{format_time(row['time_to'])} | "
                           f"Ticker: {row['ticker']} | AlphaID: {row['alphaid']} | "
                           f"Target Pos: {row['target_alpha']:,.0f} | Current Pos: {row['current_position']:,.0f} | "
                           f"Intended Trade: {row['intended_trade']:,.0f} | Actual Trade: {row['actual_trade']:,.0f} | "
                           f"Fill Rate: {row['fill_rate']:.6f}\n")
                f.write("\n")
            
            # Source Data Section
            f.write("="*80 + "\n")
            f.write("SOURCE DATA\n")
            f.write("="*80 + "\n")
            
            # Market Data
            if market_df is not None and not market_df.empty:
                f.write("-"*50 + "\n")
                f.write("MARKET DATA (MarketDataEv.csv)\n")
                f.write("-"*50 + "\n")
                f.write(f"Records: {len(market_df)}\n")
                f.write("Format: event|alphaid|time|ticker|last_price|prev_close_price\n\n")
                for _, row in market_df.iterrows():
                    f.write(f"{row['event']}|{row['alphaid']}|{row['time']}|{row['ticker']}|"
                           f"{row['last_price']}|{row['prev_close_price']}\n")
                f.write("\n")
            
            # Split Alpha Data
            if not split_alpha_df.empty:
                f.write("-"*50 + "\n")
                f.write("SPLIT ALPHA DATA (SplitAlphaEv.csv)\n")
                f.write("-"*50 + "\n")
                f.write(f"Records: {len(split_alpha_df)}\n")
                f.write("Format: event|alphaid|time|ticker|volume\n\n")
                for _, row in split_alpha_df.iterrows():
                    f.write(f"{row['event']}|{row['alphaid']}|{row['time']}|{row['ticker']}|{row['volume']}\n")
                f.write("\n")
            
            # Merged Alpha Data
            if not merged_df.empty:
                f.write("-"*50 + "\n")
                f.write("MERGED ALPHA DATA (MergedAlphaEv.csv)\n")
                f.write("-"*50 + "\n")
                f.write(f"Records: {len(merged_df)}\n")
                f.write("Format: event|alphaid|time|ticker|volume\n\n")
                for _, row in merged_df.iterrows():
                    f.write(f"{row['event']}|{row['alphaid']}|{row['time']}|{row['ticker']}|{row['volume']}\n")
                f.write("\n")
            
            # Realtime Position Data
            if not realtime_pos_df.empty:
                f.write("-"*50 + "\n")
                f.write("REALTIME POSITION DATA (SplitCtxEv.csv)\n")
                f.write("-"*50 + "\n")
                f.write(f"Records: {len(realtime_pos_df)}\n")
                f.write("Format: event|alphaid|time|ticker|realtime_pos\n\n")
                for _, row in realtime_pos_df.iterrows():
                    f.write(f"{row['event']}|{row['alphaid']}|{row['time']}|{row['ticker']}|{row['realtime_pos']}\n")
                f.write("\n")
            
            # InCheck Alpha Data
            if not incheck_alpha_df.empty:
                f.write("-"*50 + "\n")
                f.write("INCHECK ALPHA DATA (InCheckAlphaEv.csv)\n")
                f.write("-"*50 + "\n")
                f.write(f"Records: {len(incheck_alpha_df)}\n")
                f.write("Format: event|alphaid|time|ticker|volume\n\n")
                for _, row in incheck_alpha_df.iterrows():
                    f.write(f"{row['event']}|{row['alphaid']}|{row['time']}|{row['ticker']}|{row['volume']}\n")
                f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")
        
        return report_path

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
                    current_position = curr_pos["realtime_pos"].iloc[0]
                    next_position = next_pos["realtime_pos"].iloc[0]
                    
                    # CORRECT: Alpha is target position, not trade volume
                    intended_trade = target_alpha - current_position
                    actual_trade = next_position - current_position
                    
                    # Calculate fill rate based on trade volume, not alpha signal
                    fill_rate = (
                        actual_trade / intended_trade if abs(intended_trade) > 1e-6 else 0
                    )

                    fill_data.append(
                        {
                            "time_from": t_current,
                            "time_to": t_next,
                            "alphaid": alphaid,
                            "ticker": ticker,
                            "target_alpha": target_alpha,
                            "current_position": current_position,
                            "intended_trade": intended_trade,
                            "actual_trade": actual_trade,
                            "fill_rate": fill_rate,
                        }
                    )

        df = pd.DataFrame(fill_data)

        # Apply filters
        if ti_filter is not None:
            # When ti_filter is provided, analyze execution leading TO that time
            # e.g., ti=940000000 should analyze execution from 930000000->940000000
            df = df[df["time_to"] == ti_filter]
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
        plot_path = f"{self._get_output_dir()}/fill_rate_overview.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        result = AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )
        
        # Generate detailed report
        report_path = self._generate_detail_report(
            result, df, incheck_alpha_df, merged_df, split_alpha_df, 
            realtime_pos_df, market_df, "Overview Analysis"
        )
        result.details += f"\n\nDetailed report generated: {report_path}"
        
        return result

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
        
        # For ti-specific analysis, we need unfiltered data to find consecutive time periods
        # Try to get CSV directory from the analyzer that loaded the data
        csv_dir = getattr(self, '_csv_dir', None)
        
        # If we have access to the original data directory, load unfiltered data
        if hasattr(self, 'analyzer_instance') and hasattr(self.analyzer_instance, 'csv_dir'):
            from pathlib import Path
            import pandas as pd
            
            csv_dir = self.analyzer_instance.csv_dir
            split_path = Path(csv_dir) / "SplitAlphaEv.csv"
            pos_path = Path(csv_dir) / "SplitCtxEv.csv"
            
            if split_path.exists() and pos_path.exists():
                # Load unfiltered data
                unfiltered_split = pd.read_csv(split_path, delimiter="|")
                unfiltered_pos = pd.read_csv(pos_path, delimiter="|")
                
                # Preprocess time columns
                unfiltered_split["time"] = pd.to_numeric(unfiltered_split["time"], errors="coerce").fillna(-1).astype(int)
                unfiltered_pos["time"] = pd.to_numeric(unfiltered_pos["time"], errors="coerce").fillna(-1).astype(int)
                
                df = self._get_fill_data(unfiltered_split, unfiltered_pos, ti_filter=ti)
            else:
                # Fallback to filtered data
                df = self._get_fill_data(split_alpha_df, realtime_pos_df, ti_filter=ti)
        else:
            # Fallback to filtered data
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

        # Get the time_from to show the interval being analyzed
        time_from = finite_df['time_from'].iloc[0] if not finite_df.empty else 'unknown'
        
        summary = (
            f"ti={time_from}→{ti}: {len(ticker_stats)} tickers analyzed | "
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
        ax.set_title(f"Fill Rate by Ticker ({time_from}→{ti})")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plot_path = f"{self._get_output_dir()}/fill_rate_ti_{ti}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        result = AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )
        
        # Generate detailed report
        report_path = self._generate_detail_report(
            result, df, incheck_alpha_df, merged_df, split_alpha_df, 
            realtime_pos_df, market_df, "Time Event Analysis", ti=ti
        )
        result.details += f"\n\nDetailed report generated: {report_path}"
        
        return result

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
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        
        # Format time labels for x-axis
        time_labels = [format_time(t) for t in time_stats.index]
        x_positions = range(len(time_stats))
        
        ax.plot(x_positions, time_stats["mean"], marker="o", linewidth=2, markersize=6)
        ax.axhline(y=1.0, color="red", linestyle="--", label="Perfect Fill")
        
        # Set time labels on x-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(time_labels, rotation=45, ha='right')
        
        ax.set_xlabel("Time Period")
        ax.set_ylabel("Mean Fill Rate")
        ax.set_title(f"Fill Rate Timeline ({ticker})")
        ax.legend()
        plt.tight_layout()
        plot_path = f"{self._get_output_dir()}/fill_rate_{ticker}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        result = AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )
        
        # Generate detailed report
        report_path = self._generate_detail_report(
            result, df, incheck_alpha_df, merged_df, split_alpha_df, 
            realtime_pos_df, market_df, "Ticker Timeline Analysis", ticker=ticker
        )
        result.details += f"\n\nDetailed report generated: {report_path}"
        
        return result

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
        
        # For ti-specific analysis, we need unfiltered data to find consecutive time periods
        # Try to get CSV directory from the analyzer that loaded the data
        csv_dir = getattr(self, '_csv_dir', None)
        
        # If we have access to the original data directory, load unfiltered data
        if hasattr(self, 'analyzer_instance') and hasattr(self.analyzer_instance, 'csv_dir'):
            from pathlib import Path
            import pandas as pd
            
            csv_dir = self.analyzer_instance.csv_dir
            split_path = Path(csv_dir) / "SplitAlphaEv.csv"
            pos_path = Path(csv_dir) / "SplitCtxEv.csv"
            
            if split_path.exists() and pos_path.exists():
                # Load unfiltered data
                unfiltered_split = pd.read_csv(split_path, delimiter="|")
                unfiltered_pos = pd.read_csv(pos_path, delimiter="|")
                
                # Preprocess time columns
                unfiltered_split["time"] = pd.to_numeric(unfiltered_split["time"], errors="coerce").fillna(-1).astype(int)
                unfiltered_pos["time"] = pd.to_numeric(unfiltered_pos["time"], errors="coerce").fillna(-1).astype(int)
                
                df = self._get_fill_data(unfiltered_split, unfiltered_pos, ti_filter=ti, ticker_filter=ticker)
            else:
                # Fallback to filtered data
                df = self._get_fill_data(split_alpha_df, realtime_pos_df, ti_filter=ti, ticker_filter=ticker)
        else:
            # Fallback to filtered data
            df = self._get_fill_data(split_alpha_df, realtime_pos_df, ti_filter=ti, ticker_filter=ticker)
        finite_df = df[np.isfinite(df["fill_rate"])]

        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades for ti={ti}, ticker={ticker}",
            )

        net_fill_rate = finite_df['actual_trade'].sum() / finite_df['intended_trade'].sum() if finite_df['intended_trade'].sum() != 0 else 0
        summary = (
            f"ti={ti}, ticker={ticker}: {len(finite_df)} trades | "
            f"Net fill rate: {net_fill_rate:.3f}"
        )

        # Trade-by-trade breakdown
        details = "Trade-by-trade breakdown:\\n"
        for _, trade in finite_df.iterrows():
            details += (
                f"  {trade['alphaid']}: intended_trade={trade['intended_trade']:.0f}, "
                f"actual_trade={trade['actual_trade']:.0f}, fill_rate={trade['fill_rate']:.3f}\\n"
            )

        # Detailed 2x2 plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # Intended vs actual trade scatter
        ax1.scatter(
            finite_df["intended_trade"], finite_df["actual_trade"], s=100, alpha=0.7
        )
        max_val = max(
            finite_df["intended_trade"].max(), finite_df["actual_trade"].max()
        )
        min_val = min(
            finite_df["intended_trade"].min(), finite_df["actual_trade"].min()
        )
        ax1.plot([min_val, max_val], [min_val, max_val], "r--", label="Perfect Fill")
        ax1.set_xlabel("Intended Trade Volume")
        ax1.set_ylabel("Actual Trade Volume")
        ax1.set_title("Intended vs Actual Execution")
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

        # Trade volumes
        ax3.bar(
            range(len(finite_df)),
            finite_df["actual_trade"],
            color="orange",
            alpha=0.7,
            label="Actual",
        )
        ax3.bar(
            range(len(finite_df)),
            finite_df["intended_trade"],
            alpha=0.5,
            color="blue",
            label="Intended",
        )
        ax3.set_xlabel("Trade Index")
        ax3.set_ylabel("Trade Volume")
        ax3.set_title("Intended vs Actual Trade Volume")
        ax3.legend()

        # Summary metrics
        ax4.axis("off")
        net_fill_rate = finite_df['actual_trade'].sum() / finite_df['intended_trade'].sum() if finite_df['intended_trade'].sum() != 0 else 0
        metrics_text = f"""Summary Metrics:

Total Trades: {len(finite_df)}
Mean Fill Rate: {finite_df['fill_rate'].mean():.3f}
Std Fill Rate: {finite_df['fill_rate'].std():.3f}
Min Fill Rate: {finite_df['fill_rate'].min():.3f}
Max Fill Rate: {finite_df['fill_rate'].max():.3f}

Total Intended: {finite_df['intended_trade'].sum():.0f}
Total Actual: {finite_df['actual_trade'].sum():.0f}
Net Fill Rate: {net_fill_rate:.3f}
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
        plot_path = f"{self._get_output_dir()}/fill_rate_detailed_{ti}_{ticker}.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        result = AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path,
            details=details,
        )
        
        # Generate detailed report
        report_path = self._generate_detail_report(
            result, df, incheck_alpha_df, merged_df, split_alpha_df, 
            realtime_pos_df, market_df, "Deep Analysis", ti=ti, ticker=ticker
        )
        result.details += f"\n\nDetailed report generated: {report_path}"
        
        return result
