"""
Module for generating AI summaries of dashboard data using Claude via Anthropic API.
"""
import os
import json
import logging
from typing import Dict, Any, List

import pandas as pd
import anthropic
from markdown import markdown

# Set up logging
logger = logging.getLogger(__name__)

def get_claude_client():
    """
    Create and return an Anthropic API client using the API key from environment variables.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"Anthropic API Key present: {bool(api_key)}")
    print(f"Environment variables: {[k for k in os.environ.keys() if not k.startswith('_')]}")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable not set.")
        return None

    print(f"Creating Anthropic client with API key starting with: {api_key[:8]}...")
    return anthropic.Anthropic(api_key=api_key)

def format_dashboard_data_for_claude(
    selected_team: str,
    date_range: List[str],
    opponent_filter: str,
    metrics: Dict[str, Any],
    match_data: pd.DataFrame,
    chart_data: Dict[str, Any] = None
) -> str:
    """
    Format dashboard data into a structured prompt for Claude to analyze.

    Args:
        selected_team: The currently selected team
        date_range: The start and end dates of the analysis period
        opponent_filter: The currently applied opponent filter
        metrics: Dashboard metrics (win rate, goals, etc.)
        match_data: DataFrame containing match results
        chart_data: Optional dictionary containing data used in charts

    Returns:
        Formatted prompt string for Claude
    """
    # Convert match data to JSON-serializable format
    if not match_data.empty:
        match_list = match_data.to_dict('records')
    else:
        match_list = []

    # Format metrics
    formatted_metrics = {
        "games_played": metrics.get("games_played", 0),
        "win_rate": metrics.get("win_rate_value", "0%"),
        "loss_rate": metrics.get("loss_rate_value", "0%"),
        "goals_scored": metrics.get("goals_scored", 0),
        "goals_conceded": metrics.get("goals_conceded", 0),
        "goal_diff": metrics.get("goal_diff", 0)
    }

    # Prepare data object
    dashboard_data = {
        "selected_team": selected_team,
        "date_range": date_range,
        "opponent_filter": opponent_filter,
        "metrics": formatted_metrics,
        "matches": match_list[:10],  # Limit to 10 matches to avoid token limits
        "match_count": len(match_list)
    }

    # Include chart data if provided
    if chart_data:
        dashboard_data["chart_data"] = chart_data

    # Create the prompt
    prompt = f"""
You are a soccer analytics assistant. Based on the following dashboard data for {selected_team},
provide a concise, insightful summary of their performance. Focus on key metrics, trends, and notable insights.

Dashboard Data:
```json
{json.dumps(dashboard_data, indent=2)}
```

Guidelines for your analysis:
1. Start with an H2 heading "{selected_team} Performance Analysis"
2. Use structural elements like H3 headings to organize your analysis ("Overview", "Match Results Trends", "Performance Against Different Opponents", "Key Insights", "Conclusion")
3. Use bullet points for key observations
4. Highlight important numbers or metrics with HTML color, using <span style="color:#20A7C9"> for positive stats and <span style="color:#E04355"> for concerning stats
5. Keep paragraphs short and focused
6. End with a conclusion paragraph that summarizes the overall performance

Format your response using Markdown with HTML color spans where appropriate. Keep your analysis factual and data-driven, limited to 200-300 words.

Example formatting (but with the actual content from this team's data):
```
## Team Name Performance Analysis

### Overview
* Team has a <span style="color:#20A7C9">high win rate</span> of X%...
* They have scored X goals while conceding Y...

### Match Results Trends
* Recent trend shows...
```
"""
    return prompt

def generate_summary(
    selected_team: str,
    date_range: List[str],
    opponent_filter: str,
    metrics: Dict[str, Any],
    match_data: pd.DataFrame,
    chart_data: Dict[str, Any] = None,
    stream: bool = False
) -> str:
    """
    Generate an AI summary of the dashboard data using Claude.

    Args:
        selected_team: The currently selected team
        date_range: The start and end dates of the analysis period
        opponent_filter: The currently applied opponent filter
        metrics: Dashboard metrics (win rate, goals, etc.)
        match_data: DataFrame containing match results
        chart_data: Optional dictionary containing data used in charts
        stream: Whether to stream the response

    Returns:
        Markdown formatted summary string or a generator if streaming
    """
    client = get_claude_client()
    if not client:
        return "**Error:** Unable to generate summary. Anthropic API key not configured."

    try:
        prompt = format_dashboard_data_for_claude(
            selected_team, date_range, opponent_filter, metrics, match_data, chart_data
        )

        # Call the Claude API
        if stream:
            # Use streaming mode - returns a generator
            with client.messages.stream(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                temperature=0.2,
                system="You are a soccer analytics assistant that provides insightful, concise summaries of team performance data. Format your response using Markdown with HTML color spans for emphasis. Use <span style=\"color:#20A7C9\"> for positive stats and <span style=\"color:#E04355\"> for concerning stats. Make sure to close all HTML tags properly.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            ) as stream:
                # Return the stream object directly for the callback to handle
                return stream
        else:
            # Normal synchronous mode
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                temperature=0.2,
                system="You are a soccer analytics assistant that provides insightful, concise summaries of team performance data. Format your response using Markdown with HTML color spans for emphasis. Use <span style=\"color:#20A7C9\"> for positive stats and <span style=\"color:#E04355\"> for concerning stats. Make sure to close all HTML tags properly.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the summary from the response
            summary = message.content[0].text

            # Process the summary to ensure proper HTML formatting
            summary = summary.replace('```', '')  # Remove code blocks if present

            return summary

    except Exception as e:
        logger.error(f"Error generating summary with Claude: {str(e)}")
        return f"**Error generating summary:** {str(e)}"