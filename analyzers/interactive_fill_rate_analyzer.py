"""
Interactive Fill Rate Analyzer with Plotly Integration

This analyzer creates interactive plots where hovering over points shows detailed information:
- Ticker, time, fill rate, volume, target alpha, trader details
- Zoom, pan, selection, and range filtering
- Web-based plots that open in browser
"""

import pandas as pd
import numpy as np
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


try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class InteractiveFillRateAnalyzer(BaseAnalyzer):
    
    def _get_output_dir(self):
        """Get output directory from analyzer instance or default to /tmp"""
        if hasattr(self, 'analyzer_instance') and hasattr(self.analyzer_instance, 'output_dir'):
            return str(self.analyzer_instance.output_dir)
        return "/tmp"

    @property
    def name(self) -> str:
        return "Interactive Fill Rate Analysis"

    def analyze_overview(
        self, 
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None
    ) -> AnalysisResult:
        """Overview: Interactive dashboard with all tickers and times"""
        
        if not PLOTLY_AVAILABLE:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="❌ Plotly not installed. Run: pip install plotly"
            )
        
        # Get fill rate data
        df = self._get_fill_data(split_alpha_df, realtime_pos_df)
        finite_df = df[np.isfinite(df["fill_rate"])]
        
        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="No analyzable trades found for overview analysis"
            )
        
        # Create interactive dashboard
        plot_path = self._create_overview_dashboard(finite_df)
        
        # Summary stats
        total_trades = len(finite_df)
        mean_fill_rate = finite_df["fill_rate"].mean()
        
        best_performer = finite_df.loc[finite_df["fill_rate"].idxmax()]
        worst_performer = finite_df.loc[finite_df["fill_rate"].idxmin()]
        
        summary = (f"Interactive overview: {total_trades:,} trades analyzed | "
                  f"Mean fill rate: {mean_fill_rate:.3f}\n"
                  f"   Best: {best_performer['ticker']} ({best_performer['fill_rate']:.3f}) | "
                  f"Worst: {worst_performer['ticker']} ({worst_performer['fill_rate']:.3f})")
        
        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path
        )

    def analyze_time_event(
        self,
        ti: int,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Time Event: Interactive analysis for specific time with all tickers"""
        
        if not PLOTLY_AVAILABLE:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="❌ Plotly not installed. Run: pip install plotly"
            )
        
        # For ti-specific analysis, we need unfiltered data to find consecutive time periods
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
                summary=f"No analyzable trades found for ti={ti}"
            )
        
        # Create interactive time event plot
        plot_path = self._create_time_event_plot(finite_df, ti)
        
        # Summary
        ticker_count = finite_df['ticker'].nunique()
        mean_fill_rate = finite_df["fill_rate"].mean()
        
        summary = (f"Interactive time analysis (ti={ti}): {ticker_count} tickers | "
                  f"Mean fill rate: {mean_fill_rate:.3f}")
        
        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path
        )

    def analyze_ticker_timeline(
        self,
        ticker: str,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Ticker Timeline: Interactive analysis for specific ticker across all times"""
        
        if not PLOTLY_AVAILABLE:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="❌ Plotly not installed. Run: pip install plotly"
            )
        
        df = self._get_fill_data(split_alpha_df, realtime_pos_df, ticker_filter=ticker)
        finite_df = df[np.isfinite(df["fill_rate"])]
        
        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades found for {ticker}"
            )
        
        # Create interactive timeline plot
        plot_path = self._create_ticker_timeline_plot(finite_df, ticker)
        
        # Summary
        time_periods = finite_df['time_from'].nunique()
        mean_fill_rate = finite_df["fill_rate"].mean()
        
        summary = (f"Interactive timeline ({ticker}): {time_periods} time periods | "
                  f"Mean fill rate: {mean_fill_rate:.3f}")
        
        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path
        )

    def analyze_deep(
        self,
        ti: int,
        ticker: str,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> AnalysisResult:
        """Deep Analysis: Interactive detailed view for specific time + ticker"""
        
        if not PLOTLY_AVAILABLE:
            return AnalysisResult(
                analyzer_name=self.name,
                summary="❌ Plotly not installed. Run: pip install plotly"
            )
        
        df = self._get_fill_data(split_alpha_df, realtime_pos_df, ti_filter=ti, ticker_filter=ticker)
        finite_df = df[np.isfinite(df["fill_rate"])]
        
        if finite_df.empty:
            return AnalysisResult(
                analyzer_name=self.name,
                summary=f"No analyzable trades found for ti={ti}, ticker={ticker}"
            )
        
        # Create interactive deep analysis plot
        plot_path = self._create_deep_analysis_plot(finite_df, ti, ticker)
        
        # Summary
        trader_count = len(finite_df)
        mean_fill_rate = finite_df["fill_rate"].mean()
        
        summary = (f"Interactive deep analysis (ti={ti}, {ticker}): {trader_count} traders | "
                  f"Mean fill rate: {mean_fill_rate:.3f}")
        
        return AnalysisResult(
            analyzer_name=self.name,
            summary=summary,
            plot_path=plot_path
        )

    def _get_fill_data(self, split_alpha_df, realtime_pos_df, ti_filter=None, ticker_filter=None):
        """Get fill rate data with optional filtering (same as original analyzer)"""
        
        # Apply filters if specified
        if ti_filter is not None:
            # For ti filtering, we want alphas from previous time that should be executed by ti_filter
            # Find the previous time interval
            all_times = sorted(split_alpha_df['time'].unique())
            try:
                ti_index = all_times.index(ti_filter)
                if ti_index > 0:
                    prev_time = all_times[ti_index - 1]
                    split_alpha_df = split_alpha_df[split_alpha_df['time'] == prev_time]
                    realtime_pos_df = realtime_pos_df[realtime_pos_df['time'].isin([prev_time, ti_filter])]
                else:
                    # No previous time available
                    split_alpha_df = split_alpha_df.iloc[0:0]  # Empty dataframe
                    realtime_pos_df = realtime_pos_df.iloc[0:0]  # Empty dataframe
            except ValueError:
                # ti_filter not found in times
                split_alpha_df = split_alpha_df.iloc[0:0]  # Empty dataframe
                realtime_pos_df = realtime_pos_df.iloc[0:0]  # Empty dataframe
        
        if ticker_filter is not None:
            split_alpha_df = split_alpha_df[split_alpha_df['ticker'] == ticker_filter]
            realtime_pos_df = realtime_pos_df[realtime_pos_df['ticker'] == ticker_filter]
        
        # Merge split alphas with position changes
        merged_data = []
        
        for _, alpha_row in split_alpha_df.iterrows():
            alphaid = alpha_row['alphaid']
            time_from = alpha_row['time']
            ticker = alpha_row['ticker']
            target_alpha = alpha_row['volume']
            
            # Get position at T and T+1
            pos_from = realtime_pos_df[
                (realtime_pos_df['alphaid'] == alphaid) & 
                (realtime_pos_df['time'] == time_from) &
                (realtime_pos_df['ticker'] == ticker)
            ]
            
            # Find next time period  
            if ti_filter is not None:
                # When ti_filter is used, time_to should be ti_filter
                time_to = ti_filter
            else:
                # Normal case: find next time period (10-minute intervals with proper time arithmetic)
                time_to = self._get_next_time(time_from)
                
            pos_to = realtime_pos_df[
                (realtime_pos_df['alphaid'] == alphaid) & 
                (realtime_pos_df['time'] == time_to) &
                (realtime_pos_df['ticker'] == ticker)
            ]
            
            if not pos_from.empty and not pos_to.empty:
                pos_change = pos_to.iloc[0]['realtime_pos'] - pos_from.iloc[0]['realtime_pos']
                fill_rate = pos_change / target_alpha if target_alpha != 0 else np.inf
                
                merged_data.append({
                    'alphaid': alphaid,
                    'ticker': ticker,
                    'time_from': time_from,
                    'time_to': time_to,
                    'target_alpha': target_alpha,
                    'pos_from': pos_from.iloc[0]['realtime_pos'],
                    'pos_to': pos_to.iloc[0]['realtime_pos'],
                    'pos_change': pos_change,
                    'fill_rate': fill_rate
                })
        
        return pd.DataFrame(merged_data)

    def _create_overview_dashboard(self, df):
        """Create interactive overview dashboard"""
        
        # Convert time to readable format
        df['time_str'] = df['time_from'].apply(lambda x: self._format_time(x))
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Fill Rate Timeline', 'Fill Rate Distribution', 
                           'Performance by Ticker', 'Volume vs Fill Rate'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Plot 1: Timeline scatter
        fig.add_trace(
            go.Scatter(
                x=df['time_str'],
                y=df['fill_rate'],
                mode='markers',
                marker=dict(
                    size=df['target_alpha']/1000,
                    color=df['fill_rate'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Fill Rate")
                ),
                text=df['ticker'],
                hovertemplate="<b>%{text}</b><br>" +
                             "Time: %{customdata[0]}<br>" +
                             "Fill Rate: %{y:.3f}<br>" +
                             "Target: %{customdata[1]:,}<br>" +
                             "Position Change: %{customdata[2]:+,}<br>" +
                             "Trader: %{customdata[3]}<br>" +
                             "<extra></extra>",
                customdata=df[['time_str', 'target_alpha', 'pos_change', 'alphaid']],
                name='Trades'
            ),
            row=1, col=1
        )
        
        # Plot 2: Distribution
        fig.add_trace(
            go.Histogram(
                x=df['fill_rate'],
                nbinsx=20,
                hovertemplate="Fill Rate Range: %{x}<br>" +
                             "Count: %{y}<br>" +
                             "<extra></extra>",
                name='Distribution'
            ),
            row=1, col=2
        )
        
        # Plot 3: Box plot by ticker (top 10 most active)
        top_tickers = df['ticker'].value_counts().head(10).index
        for ticker in top_tickers:
            ticker_data = df[df['ticker'] == ticker]
            fig.add_trace(
                go.Box(
                    y=ticker_data['fill_rate'],
                    name=ticker,
                    hovertemplate=f"<b>{ticker}</b><br>" +
                                 "Q1: %{q1:.3f}<br>" +
                                 "Median: %{median:.3f}<br>" +
                                 "Q3: %{q3:.3f}<br>" +
                                 "Value: %{y:.3f}<br>" +
                                 "<extra></extra>"
                ),
                row=2, col=1
            )
        
        # Plot 4: Volume vs Fill Rate
        fig.add_trace(
            go.Scatter(
                x=df['target_alpha'],
                y=df['fill_rate'],
                mode='markers',
                marker=dict(color=df['ticker'].astype('category').cat.codes, opacity=0.6),
                text=df['ticker'],
                hovertemplate="<b>%{text}</b><br>" +
                             "Target Volume: %{x:,}<br>" +
                             "Fill Rate: %{y:.3f}<br>" +
                             "Trader: %{customdata}<br>" +
                             "<extra></extra>",
                customdata=df['alphaid'],
                name='Volume vs Fill Rate'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Interactive Fill Rate Dashboard",
            showlegend=False,
            hovermode='closest',
            height=800
        )
        
        # Save plot
        plot_path = f"{self._get_output_dir()}/interactive_fill_rate_dashboard.html"
        fig.write_html(plot_path)
        return plot_path

    def _create_time_event_plot(self, df, ti):
        """Create interactive plot for specific time event"""
        
        df['time_str'] = df['time_from'].apply(lambda x: self._format_time(x))
        
        # Create bar chart with hover details
        fig = px.bar(
            df,
            x='ticker',
            y='fill_rate',
            color='alphaid',
            title=f'Fill Rate by Ticker (Time: {self._format_time(ti)})',
            hover_data={
                'ticker': True,
                'fill_rate': ':.3f',
                'target_alpha': ':,',
                'pos_change': ':+,',
                'alphaid': True
            },
            labels={
                'fill_rate': 'Fill Rate',
                'ticker': 'Ticker',
                'alphaid': 'Trader'
            }
        )
        
        fig.update_layout(
            hovermode='closest',
            xaxis_title="Ticker",
            yaxis_title="Fill Rate"
        )
        
        plot_path = f"{self._get_output_dir()}/interactive_fill_rate_ti_{ti}.html"
        fig.write_html(plot_path)
        return plot_path

    def _create_ticker_timeline_plot(self, df, ticker):
        """Create interactive timeline for specific ticker"""
        
        df['time_str'] = df['time_from'].apply(lambda x: self._format_time(x))
        
        # Create timeline with different traders
        fig = px.line(
            df,
            x='time_from',
            y='fill_rate',
            color='alphaid',
            markers=True,
            title=f'Fill Rate Timeline: {ticker}',
            hover_data={
                'fill_rate': ':.3f',
                'target_alpha': ':,',
                'pos_change': ':+,',
                'alphaid': True,
                'time_str': True
            },
            labels={
                'fill_rate': 'Fill Rate',
                'time_from': 'Time',
                'alphaid': 'Trader'
            }
        )
        
        fig.update_layout(
            hovermode='closest',
            xaxis_title="Time",
            yaxis_title="Fill Rate"
        )
        
        plot_path = f"{self._get_output_dir()}/interactive_fill_rate_{ticker.replace('.', '_')}.html"
        fig.write_html(plot_path)
        return plot_path

    def _create_deep_analysis_plot(self, df, ti, ticker):
        """Create detailed interactive analysis for specific time+ticker"""
        
        df['time_str'] = df['time_from'].apply(lambda x: self._format_time(x))
        
        # Create detailed trader comparison
        fig = px.bar(
            df,
            x='alphaid',
            y=['target_alpha', 'pos_change'],
            title=f'Detailed Analysis: {ticker} at {self._format_time(ti)}',
            barmode='group',
            hover_data={
                'target_alpha': ':,',
                'pos_change': ':+,',
                'fill_rate': ':.3f'
            }
        )
        
        # Add fill rate as secondary trace
        fig.add_trace(
            go.Scatter(
                x=df['alphaid'],
                y=df['fill_rate'],
                mode='markers+text',
                marker=dict(size=15, color='red'),
                text=df['fill_rate'].round(3),
                textposition="top center",
                name='Fill Rate',
                yaxis='y2',
                hovertemplate="<b>%{x}</b><br>" +
                             "Fill Rate: %{y:.3f}<br>" +
                             "<extra></extra>"
            )
        )
        
        # Update layout with secondary y-axis
        fig.update_layout(
            yaxis2=dict(
                title="Fill Rate",
                overlaying="y",
                side="right"
            ),
            hovermode='closest'
        )
        
        plot_path = f"{self._get_output_dir()}/interactive_fill_rate_deep_{ti}_{ticker.replace('.', '_')}.html"
        fig.write_html(plot_path)
        return plot_path

    def _get_next_time(self, time_from):
        """Get next 10-minute interval time"""
        time_str = str(time_from)
        if time_from < 100000000:
            # Format: HMMSSSS (e.g., 93000000 = 9:30:00)
            hour = int(time_str[0])
            minute = int(time_str[1:3])
        else:
            # Format: HHMMSSSS (e.g., 1000000000 = 10:00:00)
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
        
        # Add 10 minutes
        minute += 10
        if minute >= 60:
            minute -= 60
            hour += 1
        
        # Format back
        if hour < 10:
            return int(f"{hour}{minute:02d}000000")
        else:
            return int(f"{hour}{minute:02d}000000")

    def _format_time(self, time_int):
        """Convert time integer to readable format"""
        time_str = str(time_int)
        if time_int < 100000000:
            hour = int(time_str[0])
            minute = int(time_str[1:3])
        else:
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
        return f"{hour:02d}:{minute:02d}"