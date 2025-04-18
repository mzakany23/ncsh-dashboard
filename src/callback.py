from dash import callback_context
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta, date
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sqlite3
import dash  # Make sure dash is imported for dash.no_update
from src.db import get_db_connection, get_team_groups, create_team_group, update_team_group, delete_team_group
from src.queries import (
    get_key_west_team_filter,
    get_debug_key_west_query,
    get_combined_matches_query,
    get_team_matches_query,
    get_team_group_filter,
    get_team_group_matches_query,
    get_opponent_query_for_key_west,
    get_opponent_query_for_team,
    get_opponent_query_for_team_group
)
from src.util import (
    normalize_team_names_in_dataframe,
    filter_matches_by_opponents,
    identify_worthy_opponents
)
from dash import callback, html, dcc, no_update
import json
import time
from urllib.parse import parse_qs, urlencode
import os
import sys
import logging
from src.claude_summary import generate_summary
import dash_bootstrap_components as dbc
from src.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)

def init_callbacks(app, teams, team_groups_param, conn):
    # Make team_groups properly accessible as a global variable within all callbacks
    global team_groups
    # Store the initial team_groups from the parameter to the global variable
    team_groups = team_groups_param

    @app.callback(
        [
            Output('games-played', 'children'),
            Output('win-rate', 'children'),
            Output('loss-rate-display', 'children'),
            Output('goals-scored', 'children'),
            Output('goals-conceded-display', 'children'),
            Output('goal-difference', 'children'),
            Output('goal-diff-time-chart', 'figure'),  # Moved here to be first in Performance Over Time section
            Output('performance-trend', 'figure'),
            Output('day-of-week-chart', 'figure'),  # New day of week performance chart
            Output('match-results-table', 'data'),
            Output('goal-stats-chart', 'figure'),
            Output('goal-stats-pie', 'figure'),
            Output('opponent-analysis-text', 'children'),
            Output('opponent-comparison-chart', 'figure'),
            Output('opponent-goal-diff-chart', 'figure'),
            Output('opponent-analysis-section', 'style'),
            Output('full-match-results-data', 'data')
        ],
        [
            Input('team-dropdown', 'value'),
            Input('team-group-dropdown', 'value'),
            Input('team-selection-type', 'value'),
            Input('date-range', 'start_date'),
            Input('date-range', 'end_date'),
            Input('initial-load', 'children'),
            Input('opponent-filter-type', 'value'),
            Input('opponent-selection', 'value'),
            Input('opponent-team-groups', 'value'),
            Input('competitiveness-threshold', 'value')
        ]
    )
    def update_dashboard(team, team_group, selection_type, start_date, end_date, initial_load,
                         opponent_filter_type, opponent_selection, opponent_team_groups, competitiveness_threshold):
        # Set default values for inputs
        start_date = start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')

        # Handle different selection types
        if selection_type == 'individual':
            display_name = team
        else:  # 'group'
            team_group = team_group or (next(iter(team_groups.keys())) if team_groups else None)
            display_name = f"Group: {team_group}" if team_group else "No group selected"

        # Create date filter condition for SQL queries
        filter_conditions = f"date >= '{start_date}' AND date <= '{end_date}'"
        logger.debug(f"Date range selected: {start_date} to {end_date}")
        logger.debug(f"Selection type: {selection_type}, Team: {team}, Team Group: {team_group}")
        logger.debug(f"Opponent filter: {opponent_filter_type}, Opponents: {opponent_selection}, Opponent Groups: {opponent_team_groups}")

        # Run debug queries to check data
        run_debug_queries(conn, filter_conditions)

        # Get match data based on selection type
        if selection_type == 'individual':
            matches_df = get_team_match_data(conn, team, filter_conditions)
        else:  # 'group'
            matches_df = get_team_group_match_data(conn, team_group, filter_conditions)

        # Apply opponent filtering
        filtered_matches_df, display_opponent_analysis = filter_matches_by_filter_type(
            matches_df,
            opponent_filter_type,
            opponent_selection,
            opponent_team_groups,
            competitiveness_threshold
        )

        # Calculate dashboard metrics
        dashboard_metrics = calculate_dashboard_metrics(filtered_matches_df)

        # Generate visualizations - use display_name for proper titles
        visualizations = generate_visualizations(filtered_matches_df, display_name, dashboard_metrics)

        # Generate opponent analysis
        opponent_analysis = generate_opponent_analysis(
            filtered_matches_df,
            opponent_filter_type,
            opponent_selection,
            opponent_team_groups,
            competitiveness_threshold
        )

        # Combine results and return
        return (
            dashboard_metrics['games_played'],
            dashboard_metrics['win_rate_value'],
            dashboard_metrics['loss_rate_value'],
            str(dashboard_metrics['goals_scored']),
            str(dashboard_metrics['goals_conceded']),
            str(dashboard_metrics['goal_diff']),
            visualizations['goal_diff_time_chart'],  # Moved here to be first in Performance Over Time section
            visualizations['performance_fig'],
            visualizations['day_of_week_chart'],  # New day of week performance chart
            dashboard_metrics['table_data'],
            visualizations['goal_fig'],
            visualizations['pie_fig'],
            opponent_analysis['analysis_text'],
            opponent_analysis['comparison_chart'],
            opponent_analysis['goal_diff_chart'],
            display_opponent_analysis,
            dashboard_metrics['table_data'] # Store full data in hidden div
        )

    def run_debug_queries(conn, filter_conditions):
        """Run debug queries to check data quality and availability."""
        # Debug query for 2025 games
        debug_2025_query = """
        SELECT date, home_team, away_team, home_score, away_score
        FROM soccer_data
        WHERE EXTRACT(YEAR FROM date) = 2025
        ORDER BY date
        """
        debug_2025_df = conn.execute(debug_2025_query).fetchdf()
        logger.debug(f"Found {len(debug_2025_df)} games in 2025 before filtering")
        for _, row in debug_2025_df.iterrows():
            logger.debug(f"2025 Game - {row['date']} - {row['home_team']} vs {row['away_team']}")

        # Debug query for team name variations
        debug_team_names_query = """
        SELECT DISTINCT home_team FROM soccer_data WHERE LOWER(home_team) LIKE '%k%w%' OR LOWER(home_team) LIKE '%key%'
        UNION
        SELECT DISTINCT away_team FROM soccer_data WHERE LOWER(away_team) LIKE '%k%w%' OR LOWER(away_team) LIKE '%key%'
        """
        debug_team_names_df = conn.execute(debug_team_names_query).fetchdf()
        logger.debug(f"Possible Key West team name variations:")
        for _, row in debug_team_names_df.iterrows():
            team_name = row[0]
            logger.debug(f"Possible team name: {team_name}")

    def get_team_match_data(conn, team, filter_conditions):
        """Get match data for the selected team."""
        matches_query = get_team_matches_query(team, filter_conditions)
        return conn.execute(matches_query).fetchdf()

    def get_team_group_match_data(conn, group_name, filter_conditions):
        """Get match data for the selected team group."""
        if not group_name or group_name not in team_groups:
            logger.debug(f"Debug: Team group '{group_name}' not found or empty")
            return pd.DataFrame()  # Return an empty DataFrame

        # Get the teams in the group
        teams = team_groups.get(group_name, [])
        if not teams:
            logger.debug(f"Debug: Team group '{group_name}' has no teams")
            return pd.DataFrame()  # Return an empty DataFrame

        logger.debug(f"Debug: Getting matches for team group '{group_name}' with {len(teams)} teams: {teams}")

        # Generate and execute the query
        matches_query = get_team_group_matches_query(teams, filter_conditions)

        # Debug - log the query
        logger.debug(f"Debug: Team group query first 200 chars: {matches_query[:200]}...")

        return conn.execute(matches_query).fetchdf()

    def filter_matches_by_filter_type(matches_df, filter_type, opponent_selection, opponent_team_groups, competitiveness_threshold):
        """
        Filter matches based on the selected filter type.

        Args:
            matches_df: DataFrame containing match data
            filter_type: Type of filter to apply ('specific', 'worthy', 'team_groups' or 'all')
            opponent_selection: List of selected opponent teams
            opponent_team_groups: List of selected opponent team groups
            competitiveness_threshold: Threshold for worthy opponents

        Returns:
            Tuple of (filtered_matches_df, display_opponent_analysis)
        """
        filtered_matches_df = matches_df.copy()
        display_opponent_analysis = {'display': 'block'}

        if filter_type == 'specific' and opponent_selection and len(opponent_selection) > 0:
            # Filter to include only matches against specific opponents
            if not filtered_matches_df.empty:
                filtered_matches_df = normalize_team_names_in_dataframe(filtered_matches_df)
                filtered_matches_df = filter_matches_by_opponents(filtered_matches_df, opponent_selection)
                logger.debug(f"Debug: Selected specific opponents: {opponent_selection}, found {len(filtered_matches_df)} matches")
            else:
                logger.debug("Debug: No matches found in the initial dataset")

        elif filter_type == 'team_groups' and opponent_team_groups and len(opponent_team_groups) > 0:
            # Filter to include only matches against opponents in selected team groups
            if not filtered_matches_df.empty:
                # Get all teams from the selected team groups
                all_opponent_teams = []
                for group_name in opponent_team_groups:
                    if group_name in team_groups:
                        group_teams = team_groups.get(group_name, [])
                        all_opponent_teams.extend(group_teams)

                # Remove duplicates
                all_opponent_teams = list(set(all_opponent_teams))

                if all_opponent_teams:
                    filtered_matches_df = normalize_team_names_in_dataframe(filtered_matches_df)
                    filtered_matches_df = filter_matches_by_opponents(filtered_matches_df, all_opponent_teams)
                    logger.debug(f"Debug: Filtering by {len(all_opponent_teams)} teams from {len(opponent_team_groups)} team groups")
                    logger.debug(f"Debug: Found {len(filtered_matches_df)} matches against teams in selected groups")
                else:
                    # If no teams in the selected groups, return empty DataFrame
                    filtered_matches_df = pd.DataFrame(columns=filtered_matches_df.columns)
                    logger.debug(f"Debug: No teams found in the selected team groups")
            else:
                logger.debug("Debug: No matches found in the initial dataset")

        elif filter_type == 'worthy':
            if not filtered_matches_df.empty:
                # Normalize team names for consistent matching
                filtered_matches_df = normalize_team_names_in_dataframe(filtered_matches_df)

                # If specific opponents are selected, these are our worthy opponents
                if opponent_selection and len(opponent_selection) > 0 and '' not in opponent_selection:
                    logger.debug(f"Debug: Using manually selected worthy opponents: {opponent_selection}")
                    worthy_opponents = opponent_selection
                else:
                    # Auto-identify worthy opponents from the filtered dataset
                    worthy_opponents = identify_worthy_opponents(filtered_matches_df, competitiveness_threshold)

                    # Add Key West teams if they're in our filtered dataset
                    key_west_teams = [team for team in filtered_matches_df['opponent_team'].unique()
                                     if 'key west' in str(team).lower() and team not in worthy_opponents]

                    if key_west_teams:
                        logger.debug(f"Debug: Adding Key West teams as worthy opponents: {key_west_teams}")
                        worthy_opponents.extend(key_west_teams)

                    logger.debug(f"Debug: Auto-identified worthy opponents: {worthy_opponents}")

                # Now filter to matches against only the worthy opponents
                if worthy_opponents:
                    # Use exact match on the original opponent names first, then fall back to normalized matching
                    logger.debug(f"Debug: Filtering matches against worthy opponents: {worthy_opponents}")

                    # Use the improved filter_matches_by_opponents function
                    filtered_matches_df = filter_matches_by_opponents(filtered_matches_df, worthy_opponents)

                    logger.debug(f"Debug: After filtering, found {len(filtered_matches_df)} matches against {len(worthy_opponents)} worthy opponents")
                    # Print each opponent and the number of matches against them
                    if not filtered_matches_df.empty:
                        for opponent in worthy_opponents:
                            match_count = len(filtered_matches_df[filtered_matches_df['opponent_team'] == opponent])
                            logger.debug(f"Debug: Found {match_count} matches against worthy opponent '{opponent}'")
                else:
                    # No worthy opponents found
                    filtered_matches_df = pd.DataFrame(columns=filtered_matches_df.columns)
                    logger.debug(f"Debug: No worthy opponents found with threshold {competitiveness_threshold}")
            else:
                logger.debug("Debug: No matches found in the initial dataset")

        # Remove the normalized_opponent column if it exists before further processing
        if 'normalized_opponent' in filtered_matches_df.columns:
            filtered_matches_df = filtered_matches_df.drop(columns=['normalized_opponent'])

        # Only hide opponent analysis if truly no data after filtering
        if len(filtered_matches_df) == 0:
            display_opponent_analysis = {'display': 'none'}
            logger.debug("Debug: No matches after filtering, hiding opponent analysis")
        else:
            logger.debug(f"Debug: Found {len(filtered_matches_df)} matches after filtering, showing opponent analysis")

        return filtered_matches_df, display_opponent_analysis

    def calculate_dashboard_metrics(filtered_matches_df):
        """
        Calculate dashboard metrics from the filtered matches data.

        Args:
            filtered_matches_df: DataFrame containing filtered match data

        Returns:
            Dictionary of calculated metrics
        """
        # Filter out NA results for metrics calculations
        valid_matches_df = filtered_matches_df[filtered_matches_df['result'] != 'NA']
        games_played = len(valid_matches_df)

        if games_played > 0:
            wins = len(valid_matches_df[valid_matches_df['result'] == 'Win'])
            losses = len(valid_matches_df[valid_matches_df['result'] == 'Loss'])
            win_rate = (wins / games_played) * 100
            loss_rate = (losses / games_played) * 100

            # Format metrics with proper formatting
            win_rate_value = f"{win_rate:.1f}%"
            loss_rate_value = f"{loss_rate:.1f}%"

            # Only sum scores for matches with valid scores
            goals_scored = valid_matches_df['team_score'].sum()
            goals_conceded = valid_matches_df['opponent_score'].sum()
            goal_diff = goals_scored - goals_conceded
        else:
            # If no valid games after filtering, set default values
            win_rate_value = "0.0%"
            loss_rate_value = "0.0%"
            goals_scored = 0
            goals_conceded = 0
            goal_diff = 0

        # Prepare data for the match results table from the filtered dataset
        table_data = []
        for _, row in filtered_matches_df.iterrows():
            score_text = "<NA> - <NA>" if row['result'] == 'NA' else f"{row['home_score']} - {row['away_score']}"
            table_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'score': score_text,
                'result': row['result'],
                'opponent': row['opponent_team']
            })

        return {
            'games_played': games_played,
            'win_rate_value': win_rate_value,
            'loss_rate_value': loss_rate_value,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'goal_diff': goal_diff,
            'table_data': table_data
        }

    def generate_visualizations(filtered_matches_df, team, dashboard_metrics):
        """
        Generate visualizations for the dashboard.

        Args:
            filtered_matches_df: DataFrame containing filtered match data
            team: Selected team name
            dashboard_metrics: Dictionary of calculated metrics

        Returns:
            Dictionary of visualization figures
        """
        # Sort data by date (newest first)
        if not filtered_matches_df.empty:
            sorted_df = filtered_matches_df.sort_values(by='date', ascending=True)  # Sort in chronological order for charts
        else:
            sorted_df = pd.DataFrame(columns=filtered_matches_df.columns)  # Empty DataFrame with same columns

        # Create goal differential time chart (moved from opponent analysis)
        goal_diff_time_chart = create_goal_differential_time_chart(sorted_df, team)

        # Create performance trend chart
        performance_fig = create_performance_trend_chart(sorted_df, team)

        # Create day of week performance chart with time dimension
        day_stats_df, time_day_stats_df = calculate_day_of_week_stats(filtered_matches_df)
        day_of_week_chart = create_day_of_week_chart(day_stats_df, time_day_stats_df, team)

        # Create goal statistics chart
        goal_fig = create_goal_stats_chart(filtered_matches_df,
                                          dashboard_metrics['goals_scored'],
                                          dashboard_metrics['goals_conceded'],
                                          dashboard_metrics['goal_diff'])

        # Create goal statistics pie chart
        pie_fig = create_result_distribution_pie_chart(filtered_matches_df)

        return {
            'goal_diff_time_chart': goal_diff_time_chart,
            'performance_fig': performance_fig,
            'day_of_week_chart': day_of_week_chart,
            'goal_fig': goal_fig,
            'pie_fig': pie_fig
        }

    def create_performance_trend_chart(sorted_df, team):
        """Create a performance trend chart showing cumulative wins, draws, and losses."""
        performance_fig = go.Figure()

        if not sorted_df.empty:
            sorted_df['cumulative_wins'] = (sorted_df['result'] == 'Win').cumsum()
            sorted_df['cumulative_draws'] = (sorted_df['result'] == 'Draw').cumsum()
            sorted_df['cumulative_losses'] = (sorted_df['result'] == 'Loss').cumsum()
            sorted_df['match_number'] = range(1, len(sorted_df) + 1)

            # Add traces with improved styling
            performance_fig.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['cumulative_wins'],
                mode='lines+markers',
                name='Wins',
                line=dict(color='#44B78B', width=3),  # Superset success color
                marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')),
                hovertemplate='Date: %{x}<br>Wins: %{y}<extra></extra>'
            ))
            performance_fig.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['cumulative_draws'],
                mode='lines+markers',
                name='Draws',
                line=dict(color='#FCC700', width=3),  # Superset warning color
                marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')),
                hovertemplate='Date: %{x}<br>Draws: %{y}<extra></extra>'
            ))
            performance_fig.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['cumulative_losses'],
                mode='lines+markers',
                name='Losses',
                line=dict(color='#E04355', width=3),  # Superset danger color
                marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')),
                hovertemplate='Date: %{x}<br>Losses: %{y}<extra></extra>'
            ))
        else:
            # Create empty chart with message
            performance_fig.add_annotation(
                text="No matches found with the current filters",
                showarrow=False,
                font=dict(size=14, color="#20A7C9"),  # Superset primary color
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )

        display_team = 'Key West (Combined)' if team == 'Key West (Combined)' else team

        # Apply improved chart styling with unified colors
        performance_fig.update_layout(
            title={
                'text': f'{display_team} Performance Over Time',
                'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}  # Superset font
            },
            xaxis_title={
                'text': 'Date',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            yaxis_title={
                'text': 'Cumulative Count',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'size': 12, 'family': 'Inter, Helvetica Neue, Arial, sans-serif'},
                'bgcolor': 'rgba(255, 255, 255, 0.8)',
                'bordercolor': '#E0E0E0',
                'borderwidth': 1
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='closest',
            margin=dict(l=60, r=30, t=80, b=60),
            xaxis=dict(
                showgrid=True,
                gridcolor='#F5F5F5',
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12, color='#323232')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#F5F5F5',
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12, color='#323232')
            )
        )

        return performance_fig

    def create_goal_stats_chart(filtered_matches_df, goals_scored, goals_conceded, goal_diff):
        """Create a goal statistics chart."""
        goal_stats = pd.DataFrame([
            {'Metric': 'Goals Scored', 'Value': goals_scored},
            {'Metric': 'Goals Conceded', 'Value': goals_conceded},
            {'Metric': 'Goal Difference', 'Value': goal_diff}
        ])

        # Define custom colors that match the Superset palette
        colors = ['#44B78B', '#E04355', '#20A7C9']  # success, danger, primary

        # Create a more visually appealing bar chart
        goal_fig = go.Figure()

        if not filtered_matches_df.empty:
            for i, row in goal_stats.iterrows():
                goal_fig.add_trace(go.Bar(
                    x=[row['Metric']],
                    y=[row['Value']],
                    name=row['Metric'],
                    marker_color=colors[i],
                    text=[row['Value']],
                    textposition='auto',
                    textfont={'color': 'white' if i != 2 or row['Value'] < 0 else '#323232'},
                    hovertemplate='%{x}: %{y}<extra></extra>'
                ))
        else:
            # Create empty chart with message
            goal_fig.add_annotation(
                text="No matches found with the current filters",
                showarrow=False,
                font=dict(size=14, color="#20A7C9"),  # Superset primary color
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )

        # Apply chart layout with Superset styling
        goal_fig.update_layout(
            title={
                'text': f'Goal Statistics',
                'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            xaxis_title={
                'text': 'Metric',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            yaxis_title={
                'text': 'Count',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            legend_title_text='',
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=30, t=80, b=60),
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=14, color='#323232')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#F5F5F5',
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12, color='#323232'),
                zerolinecolor='#E0E0E0'
            ),
            bargap=0.3
        )

        return goal_fig

    def create_result_distribution_pie_chart(filtered_matches_df):
        """Create a pie chart showing the distribution of match results."""
        pie_fig = go.Figure()

        if not filtered_matches_df.empty:
            # Filter out NA results for the pie chart
            valid_matches_df = filtered_matches_df[filtered_matches_df['result'] != 'NA']
            results_count = valid_matches_df['result'].value_counts()

            # Create a better visualization with results distribution using Superset colors
            pie_fig.add_trace(go.Pie(
                labels=['Wins', 'Draws', 'Losses'],
                values=[
                    results_count.get('Win', 0),
                    results_count.get('Draw', 0),
                    results_count.get('Loss', 0)
                ],
                hole=0.4,
                marker=dict(colors=['#44B78B', '#FCC700', '#E04355']),  # Superset colors
                textinfo='label+percent',
                textfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=14),
                hoverinfo='label+value',
                pull=[0.05, 0, 0]
            ))
        else:
            # Create empty chart with message
            pie_fig.add_annotation(
                text="No matches found with the current filters",
                showarrow=False,
                font=dict(size=14, color="#20A7C9"),  # Superset primary color
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )

        # Apply chart layout with Superset styling
        pie_fig.update_layout(
            title={
                'text': f'Match Result Distribution',
                'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
                font=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=80, b=40)
        )

        return pie_fig

    def calculate_day_of_week_stats(filtered_matches_df):
        """
        Calculate performance statistics by day of week with time dimension.

        Args:
            filtered_matches_df: DataFrame containing filtered match data

        Returns:
            Tuple of (DataFrame with day of week statistics, DataFrame with time-based day of week statistics)
        """
        # Create empty DataFrames if no matches
        if filtered_matches_df.empty:
            empty_df = pd.DataFrame(columns=['day', 'total_matches', 'win_rate', 'ci_lower', 'ci_upper', 'day_order'])
            empty_time_df = pd.DataFrame(columns=['day', 'time_period', 'total_matches', 'win_rate', 'ci_lower', 'ci_upper', 'day_order'])
            return empty_df, empty_time_df

        # Extract day of week from date
        filtered_matches_df = filtered_matches_df.copy()
        filtered_matches_df['day_of_week'] = pd.to_datetime(filtered_matches_df['date']).dt.dayofweek
        filtered_matches_df['date_obj'] = pd.to_datetime(filtered_matches_df['date'])

        # Add time period (quarter-year)
        filtered_matches_df['year'] = filtered_matches_df['date_obj'].dt.year
        filtered_matches_df['quarter'] = filtered_matches_df['date_obj'].dt.quarter
        filtered_matches_df['time_period'] = filtered_matches_df['year'].astype(str) + '-Q' + filtered_matches_df['quarter'].astype(str)

        # Map numeric day to name (0=Monday in pandas)
        day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                   4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        filtered_matches_df['day_name'] = filtered_matches_df['day_of_week'].map(day_map)

        # Filter out NA results for win rate calculations
        valid_matches_df = filtered_matches_df[filtered_matches_df['result'] != 'NA']

        # Define day order for sorting
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_order_map = {day: i for i, day in enumerate(day_order)}

        # 1. Calculate overall day of week statistics (for backward compatibility)
        day_groups = valid_matches_df.groupby('day_name')
        day_stats = []

        for day, group in day_groups:
            total_matches = len(group)
            wins = len(group[group['result'] == 'Win'])
            win_rate = wins / total_matches if total_matches > 0 else 0

            # Calculate confidence interval using Wilson score interval
            if total_matches > 0:
                z = 1.96  # 95% confidence
                # Wilson score interval formula
                denominator = 1 + z**2/total_matches
                center = (win_rate + z**2/(2*total_matches))/denominator
                err = z * ((win_rate*(1-win_rate) + z**2/(4*total_matches))/total_matches)**0.5/denominator
                ci_lower = max(0, center - err)
                ci_upper = min(1, center + err)
            else:
                ci_lower, ci_upper = 0, 0

            day_stats.append({
                'day': day,
                'total_matches': total_matches,
                'win_rate': win_rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            })

        # Convert to DataFrame and sort by day of week
        day_stats_df = pd.DataFrame(day_stats)

        # Add all days of the week if some are missing
        all_days = set(day_map.values())
        days_in_data = set(day_stats_df['day']) if not day_stats_df.empty else set()
        missing_days = all_days - days_in_data

        # Add missing days with zero values
        for day in missing_days:
            day_stats_df = pd.concat([day_stats_df, pd.DataFrame([{
                'day': day,
                'total_matches': 0,
                'win_rate': 0,
                'ci_lower': 0,
                'ci_upper': 0
            }])], ignore_index=True)

        day_stats_df['day_order'] = day_stats_df['day'].map(day_order_map)
        day_stats_df = day_stats_df.sort_values('day_order')

        # 2. Calculate day of week statistics by time period
        time_day_groups = valid_matches_df.groupby(['time_period', 'day_name'])
        time_day_stats = []

        for (time_period, day), group in time_day_groups:
            total_matches = len(group)
            wins = len(group[group['result'] == 'Win'])
            win_rate = wins / total_matches if total_matches > 0 else 0

            # Calculate confidence interval using Wilson score interval
            if total_matches > 0:
                z = 1.96  # 95% confidence
                # Wilson score interval formula
                denominator = 1 + z**2/total_matches
                center = (win_rate + z**2/(2*total_matches))/denominator
                err = z * ((win_rate*(1-win_rate) + z**2/(4*total_matches))/total_matches)**0.5/denominator
                ci_lower = max(0, center - err)
                ci_upper = min(1, center + err)
            else:
                ci_lower, ci_upper = 0, 0

            time_day_stats.append({
                'time_period': time_period,
                'day': day,
                'total_matches': total_matches,
                'win_rate': win_rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            })

        # Convert to DataFrame
        time_day_stats_df = pd.DataFrame(time_day_stats)

        if not time_day_stats_df.empty:
            # Add day order for sorting
            time_day_stats_df['day_order'] = time_day_stats_df['day'].map(day_order_map)

            # Sort by time period and day order
            time_day_stats_df = time_day_stats_df.sort_values(['time_period', 'day_order'])

        return day_stats_df, time_day_stats_df

    def create_day_of_week_chart(day_stats_df, time_day_stats_df, team_name):
        """
        Create a visualization showing win rates by day of week with time dimension.

        Args:
            day_stats_df: DataFrame containing overall day of week statistics
            time_day_stats_df: DataFrame containing day of week statistics by time period
            team_name: Name of the team for chart title

        Returns:
            Plotly figure object
        """
        # Create a subplot with 2 rows
        day_of_week_chart = go.Figure()

        # Check if we have data
        if time_day_stats_df.empty or time_day_stats_df['total_matches'].sum() == 0:
            # Create empty chart with message
            day_of_week_chart.add_annotation(
                text="No matches found with the current filters",
                showarrow=False,
                font=dict(size=14, color="#20A7C9"),  # Superset primary color
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )

            # Apply basic styling
            day_of_week_chart.update_layout(
                title={
                    'text': f'{team_name} Performance by Day of Week Over Time',
                    'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
                },
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=60, t=80, b=60)
            )

            return day_of_week_chart

        # Get unique time periods and sort them chronologically
        time_periods = sorted(time_day_stats_df['time_period'].unique())

        # Get days of week in correct order
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Create a heatmap for win rates over time
        # Prepare data for heatmap
        heatmap_data = []
        hover_texts = []

        for day in days:
            win_rates = []
            hover_text_row = []

            for period in time_periods:
                # Find the data for this day and period
                match = time_day_stats_df[(time_day_stats_df['day'] == day) &
                                         (time_day_stats_df['time_period'] == period)]

                if not match.empty:
                    win_rate = match['win_rate'].values[0] * 100  # Convert to percentage
                    matches = match['total_matches'].values[0]
                    ci_lower = match['ci_lower'].values[0] * 100
                    ci_upper = match['ci_upper'].values[0] * 100

                    win_rates.append(win_rate)

                    # Create detailed hover text with confidence intervals and match count
                    hover_text = (f"Day: {day}<br>"
                                 f"Period: {period}<br>"
                                 f"Win Rate: {win_rate:.1f}%<br>"
                                 f"95% CI: [{ci_lower:.1f}%, {ci_upper:.1f}%]<br>"
                                 f"Matches: {matches}")
                    hover_text_row.append(hover_text)
                else:
                    win_rates.append(None)  # No data for this combination
                    hover_text_row.append(f"Day: {day}<br>Period: {period}<br>No matches")

            heatmap_data.append(win_rates)
            hover_texts.append(hover_text_row)

        # Create the heatmap
        day_of_week_chart.add_trace(go.Heatmap(
            z=heatmap_data,
            x=time_periods,
            y=days,
            colorscale=[
                [0, "#E04355"],  # Red for 0% win rate
                [0.5, "#FCC700"],  # Yellow for 50% win rate
                [1, "#44B78B"]   # Green for 100% win rate
            ],
            zmin=0,
            zmax=100,
            text=hover_texts,
            hoverinfo="text",
            colorbar=dict(
                title="Win Rate (%)",
                title_font=dict(color="#44B78B"),
                tickfont=dict(color="#44B78B"),
                title_side="right"
            )
        ))

        # Add a second subplot for the traditional bar chart view
        # Create a subplot with 2 rows
        day_of_week_chart = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(
                f"{team_name} Performance by Day of Week Over Time",
                f"{team_name} Overall Performance by Day of Week"
            ),
            vertical_spacing=0.2,
            specs=[
                [{"type": "heatmap"}],
                [{"secondary_y": True}]
            ]
        )

        # Add heatmap to first subplot
        day_of_week_chart.add_trace(
            go.Heatmap(
                z=heatmap_data,
                x=time_periods,
                y=days,
                colorscale=[
                    [0, "#E04355"],  # Red for 0% win rate
                    [0.5, "#FCC700"],  # Yellow for 50% win rate
                    [1, "#44B78B"]   # Green for 100% win rate
                ],
                zmin=0,
                zmax=100,
                text=hover_texts,
                hoverinfo="text",
                colorbar=dict(
                    title="Win Rate (%)",
                    title_font=dict(color="#44B78B"),
                    tickfont=dict(color="#44B78B"),
                    title_side="right"
                )
            ),
            row=1, col=1
        )

        # Add traditional bar chart to second subplot
        if not day_stats_df.empty and day_stats_df['total_matches'].sum() > 0:
            # Add win rate bars
            day_of_week_chart.add_trace(
                go.Bar(
                    x=day_stats_df['day'],
                    y=day_stats_df['win_rate'] * 100,  # Convert to percentage
                    name='Win Rate',
                    marker_color='#44B78B',  # Superset success color
                    text=[f"{wr*100:.1f}%" for wr in day_stats_df['win_rate']],
                    textposition='auto',
                    hovertemplate='%{x}<br>Win Rate: %{text}<extra></extra>'
                ),
                row=2, col=1
            )

            # Add error bars for confidence intervals
            day_of_week_chart.add_trace(
                go.Scatter(
                    x=day_stats_df['day'],
                    y=day_stats_df['win_rate'] * 100,
                    mode='markers',
                    marker=dict(color='rgba(0,0,0,0)'),  # Invisible markers
                    error_y=dict(
                        type='data',
                        symmetric=False,
                        array=(day_stats_df['ci_upper'] - day_stats_df['win_rate']) * 100,
                        arrayminus=(day_stats_df['win_rate'] - day_stats_df['ci_lower']) * 100,
                        color='#323232'
                    ),
                    showlegend=False,
                    hoverinfo='none'
                ),
                row=2, col=1
            )

            # Add total matches as a secondary axis
            day_of_week_chart.add_trace(
                go.Bar(
                    x=day_stats_df['day'],
                    y=day_stats_df['total_matches'],
                    name='Matches Played',
                    marker_color='#20A7C9',  # Superset primary color
                    text=day_stats_df['total_matches'],
                    textposition='auto',
                    hovertemplate='%{x}<br>Matches: %{y}<extra></extra>'
                ),
                row=2, col=1, secondary_y=True
            )

        # Update layout for both subplots
        day_of_week_chart.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5
            ),
            margin=dict(l=60, r=60, t=120, b=60),
            height=800  # Increase height to accommodate both charts
        )

        # Update axes for heatmap
        day_of_week_chart.update_xaxes(
            title={
                'text': 'Time Period',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            row=1, col=1
        )

        day_of_week_chart.update_yaxes(
            title={
                'text': 'Day of Week',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            row=1, col=1
        )

        # Update axes for bar chart
        day_of_week_chart.update_xaxes(
            title={
                'text': 'Day of Week',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            row=2, col=1
        )

        day_of_week_chart.update_yaxes(
            title={
                'text': 'Win Rate (%)',
                'font': {'color': '#44B78B'}
            },
            tickformat='.0f',
            range=[0, 110],
            row=2, col=1
        )

        day_of_week_chart.update_yaxes(
            title={
                'text': 'Matches Played',
                'font': {'color': '#20A7C9'}
            },
            range=[0, max(day_stats_df['total_matches']) * 1.2] if len(day_stats_df) > 0 and day_stats_df['total_matches'].max() > 0 else [0, 10],
            row=2, col=1,
            secondary_y=True
        )

        return day_of_week_chart

    def generate_opponent_analysis(filtered_matches_df, opponent_filter_type, opponent_selection, opponent_team_groups, competitiveness_threshold):
        """
        Generate opponent analysis visualizations and text.

        Args:
            filtered_matches_df: DataFrame containing filtered match data
            opponent_filter_type: Type of opponent filter applied
            opponent_selection: List of selected opponents
            opponent_team_groups: List of selected opponent team groups
            competitiveness_threshold: Threshold for worthy opponents

        Returns:
            Dictionary of opponent analysis components
        """
        # Set default empty visualization objects
        opponent_comparison_chart = go.Figure()
        opponent_goal_diff_chart = go.Figure()
        # goal_diff_time_chart removed (moved to Performance Over Time section)

        # Generate appropriate analysis text based on filter type
        if opponent_filter_type == 'all':
            opponent_analysis_text = f"Analysis of all {len(filtered_matches_df['opponent_team'].unique())} opponents"
        elif opponent_filter_type == 'worthy' and opponent_selection:
            opponent_analysis_text = f"Analysis of selected worthy adversaries: {', '.join(opponent_selection)}"
        elif opponent_filter_type == 'worthy':
            opponent_analysis_text = f"Analysis of worthy adversaries (competitiveness ≥ {competitiveness_threshold}%)"
        elif opponent_filter_type == 'specific' and opponent_selection:
            opponent_analysis_text = f"Analysis of selected opponent(s): {', '.join(opponent_selection)}"
        elif opponent_filter_type == 'team_groups' and opponent_team_groups:
            group_names = ", ".join(opponent_team_groups)
            opponent_analysis_text = f"Analysis of opponents in team group(s): {group_names}"
        else:
            opponent_analysis_text = "No opponent filter selected"

        # Generate opponent charts if we have data
        if len(filtered_matches_df) > 0:
            # Create opponent comparison charts using the filtered data
            opponent_stats_df = generate_opponent_stats_dataframe(filtered_matches_df)

            if not opponent_stats_df.empty:
                opponent_comparison_chart = create_opponent_comparison_chart(opponent_stats_df)
                opponent_goal_diff_chart = create_opponent_goal_diff_chart(opponent_stats_df)

                # Goal differential time chart creation removed (moved to generate_visualizations function)
        else:
            # Empty figures with appropriate messages
            for chart in [opponent_comparison_chart, opponent_goal_diff_chart]:
                chart.update_layout(
                    title="No match data available",
                    xaxis=dict(showticklabels=False),
                    yaxis=dict(showticklabels=False)
                )

        return {
            'analysis_text': opponent_analysis_text,
            'comparison_chart': opponent_comparison_chart,
            'goal_diff_chart': opponent_goal_diff_chart
            # 'goal_diff_time_chart' removed (moved to generate_visualizations function)
        }

    def generate_opponent_stats_dataframe(filtered_matches_df):
        """Generate a DataFrame with opponent statistics."""
        # Group data by opponent
        opponent_groups = filtered_matches_df.groupby('opponent_team')

        # Collect opponent stats
        opponent_stats_list = []

        for opponent, group in opponent_groups:
            total_matches = len(group)
            total_wins = len(group[group['result'] == 'Win'])
            total_losses = len(group[group['result'] == 'Loss'])
            total_draws = len(group[group['result'] == 'Draw'])

            win_rate_opp = total_wins / total_matches if total_matches > 0 else 0
            loss_rate_opp = total_losses / total_matches if total_matches > 0 else 0
            draw_rate_opp = total_draws / total_matches if total_matches > 0 else 0

            total_goals_for = group['team_score'].sum()
            total_goals_against = group['opponent_score'].sum()
            goal_difference = total_goals_for - total_goals_against

            opponent_stats_list.append({
                'opponent': opponent,
                'total_matches': total_matches,
                'wins': total_wins,
                'losses': total_losses,
                'draws': total_draws,
                'win_rate': win_rate_opp,
                'loss_rate': loss_rate_opp,
                'draw_rate': draw_rate_opp,
                'goals_for': total_goals_for,
                'goals_against': total_goals_against,
                'goal_difference': goal_difference
            })

        # Create DataFrame from stats
        return pd.DataFrame(opponent_stats_list)

    def create_opponent_comparison_chart(opponent_stats_df):
        """Create a comparison chart of win rate vs. matches played by opponent."""
        # Sort by win rate for the comparison chart
        opponent_stats_df = opponent_stats_df.sort_values('win_rate', ascending=False)

        opponent_comparison_chart = go.Figure()

        opponent_comparison_chart.add_trace(go.Bar(
            x=opponent_stats_df['opponent'],
            y=opponent_stats_df['win_rate'] * 100,  # Convert to percentage value
            name='Win Rate',
            marker_color='#44B78B',  # Superset success color
            text=[f"{wr*100:.1f}%" for wr in opponent_stats_df['win_rate']],  # Format as percentage
            textposition='auto',
            hovertemplate='%{x}<br>Win Rate: %{text}<extra></extra>'
        ))

        opponent_comparison_chart.add_trace(go.Bar(
            x=opponent_stats_df['opponent'],
            y=opponent_stats_df['total_matches'],
            name='Matches Played',
            marker_color='#20A7C9',  # Superset primary color
            text=opponent_stats_df['total_matches'],
            textposition='auto',
            yaxis='y2',
            hovertemplate='%{x}<br>Matches: %{y}<extra></extra>'
        ))

        opponent_comparison_chart.update_layout(
            title={
                'text': 'Performance Against Opponents',
                'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            xaxis_title={
                'text': 'Opponent',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            yaxis=dict(
                title={
                    'text': 'Win Rate',
                    'font': {'color': '#44B78B'}
                },
                tickformat='.0f',
                range=[0, 110],
                side='left',
                tickfont=dict(color='#44B78B')
            ),
            yaxis2=dict(
                title={
                    'text': 'Matches Played',
                    'font': {'color': '#20A7C9'}
                },
                range=[0, max(opponent_stats_df['total_matches']) * 1.2] if len(opponent_stats_df) > 0 else [0, 10],
                side='right',
                overlaying='y',
                tickfont=dict(color='#20A7C9')
            ),
            barmode='group',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5
            ),
            margin=dict(l=60, r=60, t=80, b=60)
        )

        return opponent_comparison_chart


    def create_opponent_goal_diff_chart(opponent_stats_df):
        """Create a goal statistics chart by opponent."""
        # Sort by goal difference
        opponent_stats_df = opponent_stats_df.sort_values('goal_difference', ascending=False)

        opponent_goal_diff_chart = go.Figure()

        opponent_goal_diff_chart.add_trace(go.Bar(
            x=opponent_stats_df['opponent'],
            y=opponent_stats_df['goals_for'],
            name='Goals Scored',
            marker_color='#44B78B',  # Superset success color
            text=opponent_stats_df['goals_for'],
            textposition='auto',
            hovertemplate='%{x}<br>Goals Scored: %{y}<extra></extra>'
        ))

        opponent_goal_diff_chart.add_trace(go.Bar(
            x=opponent_stats_df['opponent'],
            y=opponent_stats_df['goals_against'],
            name='Goals Conceded',
            marker_color='#E04355',  # Superset danger color
            text=opponent_stats_df['goals_against'],
            textposition='auto',
            hovertemplate='%{x}<br>Goals Conceded: %{y}<extra></extra>'
        ))

        opponent_goal_diff_chart.update_layout(
            title={
                'text': 'Goal Performance by Opponent',
                'font': {'size': 20, 'color': '#20A7C9', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            xaxis_title={
                'text': 'Opponent',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            yaxis_title={
                'text': 'Goals',
                'font': {'size': 14, 'color': '#323232', 'family': 'Inter, Helvetica Neue, Arial, sans-serif'}
            },
            barmode='group',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5
            ),
            margin=dict(l=60, r=30, t=80, b=60)
        )

        return opponent_goal_diff_chart

    def create_goal_differential_time_chart(filtered_matches_df, team_name):
        """Create a time series chart showing goal differential over time for each match."""
        goal_diff_time_chart = go.Figure()

        if not filtered_matches_df.empty:
            # Sort matches by date (chronological order)
            sorted_df = filtered_matches_df.sort_values(by='date', ascending=True)

            # Calculate goal differential for each match
            sorted_df['goal_diff'] = sorted_df['team_score'] - sorted_df['opponent_score']

            # Create a cumulative goal differential line
            # First replace NA values with 0 for cumulative calculation purposes
            sorted_df['goal_diff_clean'] = sorted_df['goal_diff'].fillna(0)
            sorted_df['cumulative_goal_diff'] = sorted_df['goal_diff_clean'].cumsum()

            # Calculate 10-match rolling average (skip NA values)
            sorted_df['rolling_avg'] = sorted_df['goal_diff'].rolling(window=10, min_periods=1).mean()

            # Extract year for season grouping
            sorted_df['season'] = pd.to_datetime(sorted_df['date']).dt.year

            # Add match result for coloring - safely handle NA values
            def get_result_color(row):
                if pd.isna(row['goal_diff']):
                    return '#CCCCCC'  # Gray for NA values
                elif row['goal_diff'] > 0:
                    return '#44B78B'  # Green for positive
                elif row['goal_diff'] == 0:
                    return '#FCC700'  # Yellow for draw
                else:
                    return '#E04355'  # Red for negative

            sorted_df['result_color'] = sorted_df.apply(get_result_color, axis=1)

            # Find significant matches (goal diff >= 5 or <= -3) - filter out NAs
            significant_matches = sorted_df[
                (~pd.isna(sorted_df['goal_diff'])) & (
                    (sorted_df['goal_diff'] >= 5) |
                    (sorted_df['goal_diff'] <= -3)
                )
            ]

            # Draw season separators and labels
            seasons = sorted_df['season'].unique()
            for i, season in enumerate(seasons):
                if i > 0:  # Skip the first season's left boundary
                    # Find first match of this season
                    season_start = sorted_df[sorted_df['season'] == season].iloc[0]['date']

                    # Add vertical line for season boundary
                    goal_diff_time_chart.add_shape(
                        type="line",
                        x0=season_start,
                        y0=0,
                        x1=season_start,
                        y1=sorted_df['cumulative_goal_diff'].max() * 0.95,
                        line=dict(color="#20A7C9", width=2, dash="dash"),
                    )

                    # Add season label
                    goal_diff_time_chart.add_annotation(
                        x=season_start,
                        y=sorted_df['cumulative_goal_diff'].max() * 0.98,
                        text=f"{season} Season",
                        showarrow=False,
                        font=dict(color="#20A7C9", size=14),
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor="#20A7C9",
                        borderwidth=1,
                        borderpad=4
                    )

            # Create custom hover text with match details - safely handle NA values
            def get_hover_text(row):
                if pd.isna(row['goal_diff']) or pd.isna(row['team_score']) or pd.isna(row['opponent_score']):
                    return f"Date: {row['date']}<br>Opponent: {row['opponent_team']}<br>Score: NA<br>Goal Diff: NA<br>Result: NA"

                goal_diff = int(row['goal_diff'])
                result_text = 'Win' if goal_diff > 0 else ('Draw' if goal_diff == 0 else 'Loss')

                return (f"Date: {row['date']}<br>" +
                        f"Opponent: {row['opponent_team']}<br>" +
                        f"Score: {int(row['team_score'])} - {int(row['opponent_score'])}<br>" +
                        f"Goal Diff: {goal_diff}<br>" +
                        f"Result: {result_text}")

            sorted_df['hover_text'] = sorted_df.apply(get_hover_text, axis=1)

            # Add individual match goal differentials as a scatter plot instead of bars
            # This makes them more visible against the trending lines
            goal_diff_time_chart.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['goal_diff'],
                mode='markers',
                name='Match Goal Diff',
                marker=dict(
                    color=sorted_df['result_color'],
                    size=sorted_df['goal_diff'].fillna(0).abs() * 1.5 + 5,  # Size based on magnitude, handle NAs
                    symbol='circle',
                    line=dict(width=1, color='white')
                ),
                hovertext=sorted_df['hover_text'],
                hoverinfo='text'
            ))

            # Add 10-match rolling average trend line
            goal_diff_time_chart.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['rolling_avg'],
                mode='lines',
                name='10-Match Avg',
                line=dict(color='#FF7F44', width=2, dash='dot'),  # Orange line
                hovertemplate='%{x}<br>10-Match Avg: %{y:.1f}<extra></extra>'
            ))

            # Add cumulative goal differential line
            goal_diff_time_chart.add_trace(go.Scatter(
                x=sorted_df['date'],
                y=sorted_df['cumulative_goal_diff'],
                mode='lines',
                name='Cumulative Goal Diff',
                line=dict(color='#20A7C9', width=3),  # Superset primary color
                hovertemplate='%{x}<br>Cumulative Goal Diff: %{y}<extra></extra>'
            ))

            # Add annotations for significant matches
            for idx, row in significant_matches.iterrows():
                goal_diff_time_chart.add_annotation(
                    x=row['date'],
                    y=row['goal_diff'],
                    text=f"{int(row['goal_diff'])}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="#323232",
                    font=dict(size=10, color="#FFFFFF"),
                    bgcolor=row['result_color'],
                    bordercolor="#FFFFFF",
                    borderwidth=1,
                    borderpad=3,
                    opacity=0.8
                )
        else:
            # Create empty chart with message
            goal_diff_time_chart.add_annotation(
                text="No matches found with the current filters",
                showarrow=False,
                font=dict(size=14, color="#20A7C9"),  # Superset primary color
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )

        # Format the team name for display
        display_team = team_name

        # Apply chart styling
        goal_diff_time_chart.update_layout(
            title=dict(
                text=f'{display_team} Goal Differential Over Time',
                font=dict(size=20, color='#20A7C9', family='Inter, Helvetica Neue, Arial, sans-serif')
            ),
            xaxis=dict(
                title=dict(
                    text='Date',
                    font=dict(size=14, color='#323232', family='Inter, Helvetica Neue, Arial, sans-serif')
                ),
                showgrid=True,
                gridcolor='#F5F5F5',
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12, color='#323232')
            ),
            yaxis=dict(
                title=dict(
                    text='Goal Differential',
                    font=dict(size=14, color='#323232', family='Inter, Helvetica Neue, Arial, sans-serif')
                ),
                showgrid=True,
                gridcolor='#F5F5F5',
                showline=True,
                linecolor='#E0E0E0',
                tickfont=dict(family='Inter, Helvetica Neue, Arial, sans-serif', size=12, color='#323232'),
                zeroline=True,
                zerolinecolor='#E0E0E0',
                zerolinewidth=2
            ),
            yaxis2=dict(
                title=dict(
                    text='Cumulative Goal Differential',
                    font=dict(color='#20A7C9')
                ),
                tickfont=dict(color='#20A7C9'),
                anchor='x',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=12, family='Inter, Helvetica Neue, Arial, sans-serif'),
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#E0E0E0',
                borderwidth=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='closest',
            margin=dict(l=60, r=30, t=80, b=60)
        )

        # Update the cumulative goal diff to use the secondary y-axis if needed
        # Handle NA values safely
        if (not filtered_matches_df.empty and
            not sorted_df['cumulative_goal_diff'].empty and
            not pd.isna(sorted_df['cumulative_goal_diff'].max()) and
            sorted_df['cumulative_goal_diff'].max() > 20):
            goal_diff_time_chart.data[2]['yaxis'] = 'y2'

        return goal_diff_time_chart

    # Callback to ensure data loads on initial page load
    @app.callback(
        Output('initial-load', 'children'),
        [Input('date-preset-dropdown', 'value')]
    )
    def set_initial_load(date_preset):
        # Just return something to trigger the update_dashboard callback
        return 'loaded'

    # Callback to update the date picker based on the preset selection
    @app.callback(
        [Output('date-range', 'start_date'),
        Output('date-range', 'end_date')],
        [Input('date-preset-dropdown', 'value')]
    )
    def update_date_range(preset):
        today = date.today()

        if preset == 'last_30_days':
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif preset == 'last_90_days':
            start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif preset == 'this_year':
            start_date = date(today.year, 1, 1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif preset == 'last_year':
            start_date = date(today.year - 1, 1, 1).strftime('%Y-%m-%d')
            end_date = date(today.year - 1, 12, 31).strftime('%Y-%m-%d')
        elif preset == 'all_time':
            # Use a very early date and future date to cover all possible data
            start_date = '2000-01-01'
            end_date = '2030-12-31'
        elif preset.startswith('year_'):
            year = int(preset.split('_')[1])
            start_date = date(year, 1, 1).strftime('%Y-%m-%d')
            end_date = date(year, 12, 31).strftime('%Y-%m-%d')
        else:
            # Default to current year
            start_date = date(today.year, 1, 1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

        return start_date, end_date

    # Callback to show/hide opponent filter controls
    @app.callback(
        [
            Output('opponent-selection-div', 'style'),
            Output('worthy-adversaries-controls', 'style'),
            Output('team-groups-opponent-div', 'style'),
            Output('opponent-selection-label', 'children'),
            Output('opponent-selection', 'style')
        ],
        [Input('opponent-filter-type', 'value')]
    )
    def toggle_opponent_controls(filter_type):
        # Default dropdown style that allows proper multi-selection display
        multi_select_style = {
            'min-height': '38px',
            'height': 'auto',
            'margin-bottom': '10px',
            'position': 'relative',
            'zIndex': 1000,
            'display': 'block',
            'width': '100%'
        }

        if filter_type == 'specific':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, "Select Opponent(s):", multi_select_style
        elif filter_type == 'worthy':
            return {'display': 'block'}, {'display': 'block'}, {'display': 'none'}, "Worthy Adversaries:", multi_select_style
        elif filter_type == 'team_groups':
            return {'display': 'block'}, {'display': 'none'}, {'display': 'block'}, "Select Opponent(s):", {'display': 'none'}
        else:  # 'all' or any other value
            return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, "Select Opponent(s):", multi_select_style

    @app.callback(
        [Output('opponent-selection', 'options'),
         Output('opponent-selection', 'value')],
        [
            Input('opponent-filter-type', 'value'),
            Input('team-dropdown', 'value'),
            Input('team-group-dropdown', 'value'),
            Input('team-selection-type', 'value'),
            Input('date-range', 'start_date'),
            Input('date-range', 'end_date'),
            Input('competitiveness-threshold', 'value')
        ],
        [State('opponent-selection', 'value')]  # Add this to preserve current selection
    )
    def update_opponent_options(filter_type, team, team_group, selection_type, start_date, end_date, competitiveness_threshold, current_selection):
        # Default opponents (all teams except selected team/group)
        if selection_type == 'individual':
            all_opponents = [{'label': t, 'value': t} for t in teams if t != team]
        else:  # 'group'
            if not team_group or team_group not in team_groups:
                return [], []  # No valid group selected
            group_teams = team_groups.get(team_group, [])
            if not group_teams:
                return [], []  # Empty group
            all_opponents = [{'label': t, 'value': t} for t in teams if t not in group_teams]

        # For 'specific' option, return all opponents and preserve current selection
        if filter_type == 'specific':
            # Ensure current_selection is a list
            if current_selection and not isinstance(current_selection, list):
                current_selection = [current_selection]
            # Filter out any invalid selections
            valid_values = [opt['value'] for opt in all_opponents]
            current_selection = [v for v in (current_selection or []) if v in valid_values]
            return all_opponents, current_selection

        # If filter type is 'worthy', compute worthy opponents
        elif filter_type == 'worthy':
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Get data for the selected team or team group
            filter_conditions = f"date >= '{start_date}' AND date <= '{end_date}'"

            if selection_type == 'individual':
                opponent_query = get_opponent_query_for_team(team, filter_conditions)
            else:  # 'group'
                if not team_group or team_group not in team_groups:
                    return [], []  # No valid group selected

                group_teams = team_groups.get(team_group, [])
                if not group_teams:
                    return [], []  # Empty group

                opponent_query = get_opponent_query_for_team_group(group_teams, filter_conditions)

            # Execute query and get opponent data
            opponent_df = conn.execute(opponent_query).fetchdf()

            # Rename 'opponent' column to 'opponent_team' for consistency
            if 'opponent' in opponent_df.columns and 'opponent_team' not in opponent_df.columns:
                opponent_df = opponent_df.rename(columns={'opponent': 'opponent_team'})

            # Calculate competitiveness for each opponent
            worthy_opponents = []
            worthy_opponent_values = []
            opponents_with_wins = set()

            # Special handling for Key West teams
            key_west_teams = []
            for team_name in opponent_df['opponent_team'].unique():
                if 'key west' in str(team_name).lower():
                    key_west_teams.append(team_name)

            if not opponent_df.empty:
                # Normalize team names for consistent matching
                opponent_df = normalize_team_names_in_dataframe(opponent_df, 'opponent_team')
                opponent_groups = opponent_df.groupby('normalized_opponent')

                # Create a mapping of normalized names to original names
                name_mapping = {}
                for norm_name, group in opponent_groups:
                    name_mapping[norm_name] = group['opponent_team'].iloc[0]

                # First identify opponents who have defeated us
                for norm_opponent, group in opponent_groups:
                    display_name = name_mapping[norm_opponent]
                    opponent_wins = len(group[group['result'] == 'Loss'])
                    total_matches = len(group)

                    if opponent_wins > 0:
                        opponents_with_wins.add(norm_opponent)
                        worthy_opponents.append({
                            'label': f"{display_name} ({total_matches} matches, defeated us {opponent_wins} times)",
                            'value': display_name
                        })
                        worthy_opponent_values.append(display_name)

                # Add Key West teams as worthy opponents
                for team_name in set(key_west_teams):
                    if team_name not in worthy_opponent_values:
                        worthy_opponents.append({
                            'label': f"{team_name} (Key West team)",
                            'value': team_name
                        })
                        worthy_opponent_values.append(team_name)

                # Evaluate other opponents based on competitiveness
                for norm_opponent, group in opponent_groups:
                    if norm_opponent in opponents_with_wins:
                        continue

                    display_name = name_mapping[norm_opponent]
                    if display_name in worthy_opponent_values:
                        continue

                    if len(group) >= 1:
                        total_matches = len(group)
                        losses = len(group[group['result'] == 'Loss'])
                        loss_rate = losses / total_matches

                        group['goal_diff'] = abs(group['team_score'] - group['opponent_score'])
                        avg_goal_diff = group['goal_diff'].mean()

                        loss_factor = loss_rate * 100
                        margin_factor = max(0, 100 - min(avg_goal_diff * 20, 100))
                        competitiveness_score = (loss_factor * 0.7) + (margin_factor * 0.3)

                        if competitiveness_score >= competitiveness_threshold:
                            worthy_opponents.append({
                                'label': f"{display_name} ({total_matches} matches, {competitiveness_score:.0f}% competitive)",
                                'value': display_name
                            })
                            worthy_opponent_values.append(display_name)

                worthy_opponents = sorted(worthy_opponents, key=lambda x: x['label'])

                if worthy_opponents:
                    # Ensure current_selection contains only valid worthy opponents
                    if current_selection and not isinstance(current_selection, list):
                        current_selection = [current_selection]
                    valid_values = [opt['value'] for opt in worthy_opponents]
                    current_selection = [v for v in (current_selection or []) if v in valid_values]
                    return worthy_opponents, current_selection
                else:
                    return [{'label': 'No worthy opponents found with current threshold', 'value': ''}], []

        # Default: return empty when 'all' is selected
        return [], []

    # Add callback to hide loading spinner after initial load
    @app.callback(
        Output("loading-spinner-container", "style"),
        [Input('initial-load', 'children')]
    )
    def hide_loading_after_initial_load(initial_load):
        # Hide loading spinner container after initial load
        return {"display": "none"}

    # Callback to toggle between individual team and team group selection
    @app.callback(
        [Output('team-dropdown', 'style'),
        Output('team-group-selection-div', 'style')],
        [Input('team-selection-type', 'value')]
    )
    def toggle_team_selection_type(selection_type):
        if selection_type == 'individual':
            return {'display': 'block'}, {'display': 'none'}
        else:  # 'group'
            return {'display': 'none'}, {'display': 'block'}

    @app.callback(
        [Output('edit-teams-for-group', 'value'),
         Output('edit-group-dropdown', 'options'),
         Output('edit-group-name', 'value')],
        [Input('edit-group-dropdown', 'value'),
         Input('group-management-status', 'children')]  # Use this to trigger refresh when team groups change
    )
    def populate_edit_teams(group_name, status_change):
        """Populate the edit teams dropdown with the teams from the selected group."""
        # First update the dropdown options with all available team groups
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Get all team groups for the dropdown with debug info
            cursor.execute("SELECT id, name FROM team_groups ORDER BY name")
            all_groups = cursor.fetchall()
            logger.debug(f"Database contains {len(all_groups)} team groups: {all_groups}")

            group_names = [group[1] for group in all_groups]
            group_options = [{'label': name, 'value': name} for name in group_names]
            logger.debug(f"Refreshed edit-group-dropdown with {len(group_names)} options: {group_names}")

            # Update the global team_groups dictionary (important for consistency)
            logger.debug(f"Updated global team_groups, now contains: {list(team_groups.keys())}")
        except sqlite3.Error as e:
            logger.error(f"Error getting team groups: {str(e)}")
            group_options = []
        finally:
            conn.close()

        # Early return if no group is selected
        if not group_name:
            return [], group_options, ""

        # Query the database directly to get the team members
        logger.debug(f"Retrieving team members for group '{group_name}'")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Get the group ID
            cursor.execute("SELECT id FROM team_groups WHERE name = ?", (group_name,))
            group_row = cursor.fetchone()

            if not group_row:
                logger.debug(f"Group '{group_name}' not found in database")
                return [], group_options, ""

            group_id = group_row[0]

            # Get all teams in the group
            cursor.execute("SELECT team_name FROM team_group_members WHERE group_id = ? ORDER BY team_name", (group_id,))
            teams = [row[0] for row in cursor.fetchall()]

            logger.debug(f"Found {len(teams)} teams for group '{group_name}': {teams}")
            return teams, group_options, group_name
        except sqlite3.Error as e:
            logger.error(f"Error retrieving team members for group '{group_name}': {str(e)}")
            return [], group_options, ""
        finally:
            conn.close()

    # Callback to create a new team group
    @app.callback(
        [Output('group-management-status', 'children'),
        Output('new-group-name', 'value'),
        Output('teams-for-group', 'value'),
        Output('team-group-dropdown', 'options'),
        Output('team-group-dropdown', 'value')],
        [Input('create-group-button', 'n_clicks'),
        Input('update-group-button', 'n_clicks'),
        Input('delete-group-button', 'n_clicks')],
        [State('new-group-name', 'value'),
        State('teams-for-group', 'value'),
        State('edit-group-dropdown', 'value'),
        State('edit-teams-for-group', 'value'),
        State('edit-group-name', 'value'),
        State('team-group-dropdown', 'value')]
    )
    def manage_team_groups(create_clicks, update_clicks, delete_clicks,
                        new_name, new_teams, edit_name, edit_teams, edit_new_name, current_selection):
        """Handle team group management operations."""
        # Declare team_groups as global to access the module-level variable
        global team_groups

        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        logger.debug(f"Team group management triggered by: {triggered_id}")
        logger.debug(f"Current state - Create clicks: {create_clicks}, Update clicks: {update_clicks}, Delete clicks: {delete_clicks}")
        logger.debug(f"Edit name: {edit_name}, New name: {edit_new_name}, Edit teams count: {len(edit_teams) if edit_teams else 0}")
        logger.debug(f"Current group selection: {current_selection}")
        logger.debug(f"BEFORE OPERATION: Global team_groups contains {len(team_groups)} groups: {list(team_groups.keys())}")

        # Default return values
        status = ""
        new_name_value = ""
        new_teams_value = []
        selected_group = current_selection  # Keep current selection by default

        # We're using the global team_groups variable declared at the init_callbacks level
        # so we don't need to redeclare it here

        if triggered_id == 'create-group-button' and new_name and new_teams:
            # Create a new team group
            if create_team_group(new_name, new_teams):
                status = f"Team group '{new_name}' created successfully!"
                # Refresh team groups after successful creation
                team_groups = get_team_groups()
                logger.debug(f"AFTER CREATE: Global team_groups refreshed, now contains {len(team_groups)} groups: {list(team_groups.keys())}")
                selected_group = new_name  # Auto-select newly created group
            else:
                status = f"Failed to create team group '{new_name}'. It may already exist."
                new_name_value = new_name
                new_teams_value = new_teams

        elif triggered_id == 'update-group-button' and edit_name and edit_teams:
            # Update an existing team group
            # Use the new name if it's different from the original
            renamed = edit_new_name and edit_new_name != edit_name
            if update_team_group(edit_name, edit_teams, edit_new_name if renamed else None):
                if renamed:
                    status = f"Team group '{edit_name}' renamed to '{edit_new_name}' and updated successfully!"
                    # If current selection is the updated group, update it with the new name
                    if current_selection == edit_name:
                        selected_group = edit_new_name
                else:
                    status = f"Team group '{edit_name}' updated successfully!"

                # Refresh team groups after successful update
                team_groups = get_team_groups()
                logger.debug(f"AFTER UPDATE: Global team_groups refreshed, now contains {len(team_groups)} groups: {list(team_groups.keys())}")
            else:
                status = f"Failed to update team group '{edit_name}'."

        elif triggered_id == 'delete-group-button':
            # Validate the input for deletion
            if not edit_name:
                logger.debug("Delete operation failed: No team group selected")
                status = "Delete failed: No team group selected"
            else:
                logger.debug(f"Attempting to delete team group: {edit_name}")
                # Delete a team group
                if delete_team_group(edit_name):
                    status = f"Team group '{edit_name}' deleted successfully!"

                    # Force removal from the team_groups dictionary before refreshing
                    if edit_name in team_groups:
                        del team_groups[edit_name]

                    # Refresh team groups after deletion
                    team_groups = get_team_groups()
                    logger.debug(f"AFTER DELETE: Global team_groups refreshed, now contains {len(team_groups)} groups: {list(team_groups.keys())}")

                    # Clear the current selection if it was the deleted group
                    if current_selection == edit_name:
                        # Select another group if available, otherwise set to None
                        if team_groups:
                            selected_group = next(iter(team_groups.keys()))
                            logger.debug(f"Selected new group: {selected_group}")
                        else:
                            selected_group = None
                            logger.debug("No groups available after deletion")
                else:
                    status = f"Failed to delete team group '{edit_name}'."

        # Update dropdown options for team group dropdown
        logger.debug(f"Updating team group dropdown with team groups: {list(team_groups.keys())}")

        # Instead of relying only on the global variable, also query the database directly
        # to ensure complete consistency across all dropdowns
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM team_groups ORDER BY name")
            db_group_names = [row[0] for row in cursor.fetchall()]
            logger.debug(f"Direct database query shows {len(db_group_names)} groups: {db_group_names}")
            team_group_options = [{'label': group_name, 'value': group_name} for group_name in db_group_names]
        except sqlite3.Error as e:
            logger.error(f"Error querying team groups for dropdown: {str(e)}")
            # Fall back to using the global variable if database query fails
            team_group_options = [{'label': group_name, 'value': group_name} for group_name in team_groups.keys()]
        finally:
            conn.close()

        # Make sure the selected group still exists
        if selected_group and selected_group not in db_group_names:
            if db_group_names:
                selected_group = db_group_names[0]
                logger.debug(f"Selected group not found, defaulting to: {selected_group}")
            else:
                selected_group = None
                logger.debug("No groups available, setting selection to None")

        logger.debug(f"Final selected group: {selected_group}")
        return status, new_name_value, new_teams_value, team_group_options, selected_group

    # Callback to update URL when team group selection changes
    @app.callback(
        Output('url', 'search'),
        [Input('team-group-dropdown', 'value'),
         Input('team-selection-type', 'value')],
        [State('url', 'search')],
        prevent_initial_call=True
    )
    def update_url_team_group(selected_team_group, selection_type, current_search):
        """Update URL with team group selection"""
        logger.debug(f"Debug: Updating URL with team group={selected_team_group}, selection_type={selection_type}")

        # Only update for team group selection type
        if selection_type != 'group' or not selected_team_group:
            return current_search or ''

        # Parse current query string if it exists
        query_params = parse_qs(current_search[1:]) if current_search and current_search.startswith('?') else {}

        # Update or add team_group parameter
        query_params['team_group'] = [selected_team_group]

        # Return updated query string
        updated_search = '?' + urlencode(query_params, doseq=True)
        logger.debug(f"Debug: Updated URL search to {updated_search}")
        return updated_search

    # Callback to set team dropdown selection based on URL
    @app.callback(
        [Output('team-group-dropdown', 'value', allow_duplicate=True),
         Output('team-selection-type', 'value', allow_duplicate=True)],
        [Input('url', 'search')],
        [State('team-group-dropdown', 'options')],
        prevent_initial_call='initial_duplicate'
    )
    def set_team_from_url(search, team_group_options):
        """Set team selection from URL parameters"""
        logger.debug(f"Debug: Setting team from URL search: {search}")

        # Check if team_group parameter exists in URL
        if search and search.startswith('?'):
            # Parse query string
            query_params = parse_qs(search[1:])

            # Check if team_group parameter exists
            if 'team_group' in query_params:
                team_group = query_params['team_group'][0]

                # Verify it's a valid option
                available_groups = [opt['value'] for opt in team_group_options]
                if team_group in available_groups:
                    logger.debug(f"Debug: Setting team group to {team_group} from URL")
                    return team_group, 'group'

        # If URL parameter not present or not valid, set default (first alphabetical)
        if team_group_options:
            default_group = team_group_options[0]['value']
            logger.debug(f"Debug: Setting default team group to {default_group}")
            return default_group, 'group'

        # If no options available, don't update
        return dash.no_update, dash.no_update

    # Callback to update team group options for the opponent filter
    @app.callback(
        Output('opponent-team-groups', 'options'),
        [Input('group-management-status', 'children'),
         Input('team-group-dropdown', 'value'),
         Input('team-selection-type', 'value')]  # Add inputs for current selection and selection type
    )
    def update_opponent_team_groups(status_change, current_team_group, selection_type):
        """Update the team groups dropdown in the opponent filter section"""
        # Query the database directly for the most up-to-date list
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM team_groups ORDER BY name")
            all_group_names = [row[0] for row in cursor.fetchall()]

            # Filter out the currently selected team group when in Team Group mode
            if selection_type == 'group' and current_team_group:
                group_names = [name for name in all_group_names if name != current_team_group]
                logger.debug(f"Updating opponent team groups dropdown with {len(group_names)} groups (excluded {current_team_group})")
            else:
                group_names = all_group_names
                logger.debug(f"Updating opponent team groups dropdown with all {len(group_names)} groups")

            return [{'label': name, 'value': name} for name in group_names]
        except sqlite3.Error as e:
            logger.error(f"Error querying team groups for opponent dropdown: {str(e)}")
            # Fall back to the global variable, but still filter out current selection
            if selection_type == 'group' and current_team_group:
                group_names = [name for name in team_groups.keys() if name != current_team_group]
            else:
                group_names = list(team_groups.keys())
            return [{'label': group_name, 'value': group_name} for group_name in group_names]
        finally:
            conn.close()

    # Callback to reset opponent team groups selection when team selection changes
    @app.callback(
        Output('opponent-team-groups', 'value'),
        [Input('team-group-dropdown', 'value'),
         Input('team-selection-type', 'value')],
        [State('opponent-team-groups', 'value')]
    )
    def reset_opponent_team_groups(current_team_group, selection_type, current_selection):
        """Reset the opponent team groups selection when team selection changes"""
        # Get the callback context to check what triggered this callback
        ctx = callback_context
        if not ctx.triggered:
            # If not triggered by any input, just return the current selection
            return current_selection

        # Get the ID of the input that triggered this callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id in ['team-group-dropdown', 'team-selection-type']:
            # If the selection type is 'group' and current_team_group is in the current selection,
            # remove it and return the filtered selection
            if selection_type == 'group' and current_team_group and current_selection:
                if isinstance(current_selection, list) and current_team_group in current_selection:
                    new_selection = [group for group in current_selection if group != current_team_group]
                    logger.debug(f"Removed {current_team_group} from opponent team groups selection")
                    return new_selection

        # Otherwise, just return the current selection unchanged
        return current_selection

    # Mobile menu toggle callback
    @app.callback(
        Output("mobile-menu", "style"),
        Input("mobile-menu-button", "n_clicks"),
        State("mobile-menu", "style"),
        prevent_initial_call=True
    )
    def toggle_mobile_menu(n_clicks, current_style):
        if current_style is None:
            current_style = {}
        if current_style.get("display") == "none":
            return {"display": "block"}
        return {"display": "none"}

    # Tooltip positioning callback for AI icon
    @app.callback(
        [Output("ai-tooltip", "show"),
         Output("ai-tooltip", "bbox")],
        [Input("ai-summary-icon", "n_hover")],
        prevent_initial_call=True
    )
    def show_tooltip(hover_data):
        if hover_data:
            return True, {"bottom": 0, "height": 20, "left": 0, "right": 20, "top": 20, "width": 20, "x": 10, "y": 10}
        return False, {}

    # Immediately trigger spinning animation when icon is clicked
    @app.callback(
        Output('ai-summary-icon', 'children', allow_duplicate=True),
        Input('ai-summary-icon', 'n_clicks'),
        prevent_initial_call=True
    )
    def start_spinning_icon(n_clicks):
        """Replace the robot icon with a spinner when clicked"""
        if not n_clicks:
            return no_update

        # Replace with a spinner icon
        return html.I(className="fas fa-spinner fa-spin", style={
            "color": "#20A7C9",
            "font-size": "1.25rem",
            "padding": "6px",
            "background-color": "rgba(32, 167, 201, 0.1)",
            "border-radius": "50%",
            "box-shadow": "0 0 5px rgba(32, 167, 201, 0.2)"
        })

    # AI summary generation callback
    @app.callback(
        [Output('ai-summary-container', 'children'),
         Output('ai-summary-container', 'style'),
         Output('ai-summary-icon', 'children')],
        [Input('ai-summary-icon', 'n_clicks')],
        [State('team-dropdown', 'value'),
         State('team-selection-type', 'value'),
         State('team-group-dropdown', 'value'),
         State('date-range', 'start_date'),
         State('date-range', 'end_date'),
         State('opponent-filter-type', 'value'),
         State('games-played', 'children'),
         State('win-rate', 'children'),
         State('loss-rate-display', 'children'),
         State('goals-scored', 'children'),
         State('goals-conceded-display', 'children'),
         State('goal-difference', 'children'),
         State('match-results-table', 'data')],
        prevent_initial_call=True
    )
    def update_ai_summary(n_clicks, team, selection_type, team_group, start_date, end_date, opponent_filter,
                          games_played, win_rate, loss_rate, goals_scored,
                          goals_conceded, goal_diff, match_data):
        """Generate and display AI summary of dashboard data when icon is clicked."""
        if not n_clicks:
            return no_update, no_update, no_update

        # Create normal icon - to be returned after generation is complete
        normal_icon = html.I(className="fas fa-robot ai-icon")

        # Use the team group value if team selection type is 'group'
        selected_team = team_group if selection_type == 'group' else team

        if not selected_team:
            return html.Div("Please select a team to analyze."), {'display': 'block'}, normal_icon

        # Convert match data to DataFrame
        match_df = pd.DataFrame(match_data) if match_data else pd.DataFrame()

        # Create metrics dictionary from the values in the cards
        metrics = {
            "games_played": games_played,
            "win_rate_value": win_rate,
            "loss_rate_value": loss_rate,
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded,
            "goal_diff": goal_diff
        }

        try:
            # Format the date range
            date_range = [
                start_date or "All time",
                end_date or datetime.now().strftime("%Y-%m-%d")
            ]

            # Generate the summary using Claude
            logger.debug(f"Calling Claude API for summary generation for team: {selected_team}")
            logger.debug(f"ANTHROPIC_API_KEY set: {bool(os.getenv('ANTHROPIC_API_KEY'))}")

            summary_markdown = generate_summary(
                selected_team=selected_team,
                date_range=date_range,
                opponent_filter=opponent_filter or "All opponents",
                metrics=metrics,
                match_data=match_df,
                stream=False
            )

            # If we get an error message back
            if isinstance(summary_markdown, str) and summary_markdown.startswith("**Error:**"):
                logger.error(f"Error message received: {summary_markdown}")
                return html.Div([
                    html.P("Error generating AI analysis:"),
                    html.P(summary_markdown)
                ], style={"color": "red"}), {'display': 'block'}, normal_icon

            # Return the markdown content with normal icon ONLY AFTER generation is complete
            return dcc.Markdown(summary_markdown, dangerously_allow_html=True), {'display': 'block'}, normal_icon

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error generating AI summary: {str(e)}")
            logger.error(error_trace)

            return html.Div([
                html.P("Error generating AI analysis:"),
                html.P(str(e))
            ], style={"color": "red"}), {'display': 'block'}, normal_icon

    # New callback to filter the match results table based on the result filter dropdown
    @app.callback(
        Output('match-results-table', 'data', allow_duplicate=True),
        [Input('result-filter-dropdown', 'value')],
        [State('full-match-results-data', 'data')],
        prevent_initial_call=True
    )
    def filter_match_results_table(result_filter, full_data):
        """Filter the match results table based on selected win/loss/draw filters."""
        # If no result filter or full data is empty, return the full data
        if not result_filter or not full_data or len(result_filter) == 0:
            return full_data

        # Apply result filter
        filtered_data = [row for row in full_data if row['result'] in result_filter]
        logger.debug(f"Applied result filter: {result_filter}, {len(filtered_data)} matches remain out of {len(full_data)}")

        return filtered_data
