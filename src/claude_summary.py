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
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable not set.")
        return None

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
1. Start with a brief overview of the team's performance (win rate, goals, etc.)
2. Mention any notable trends or patterns in the match results
3. Provide insights about how they perform against different types of opponents
4. Include 2-3 specific data-backed observations that might not be immediately obvious
5. End with a brief, high-level conclusion

Format your response in Markdown, with appropriate headings, bullet points, and emphasis where relevant.
Keep your analysis factual and data-driven, limited to 200-300 words.
"""
    return prompt

def generate_summary(
    selected_team: str,
    date_range: List[str],
    opponent_filter: str,
    metrics: Dict[str, Any],
    match_data: pd.DataFrame,
    chart_data: Dict[str, Any] = None
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

    Returns:
        Markdown formatted summary string
    """
    client = get_claude_client()
    if not client:
        return "**Error:** Unable to generate summary. Anthropic API key not configured."

    try:
        prompt = format_dashboard_data_for_claude(
            selected_team, date_range, opponent_filter, metrics, match_data, chart_data
        )

        # Call the Claude API
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0.2,
            system="You are a soccer analytics assistant that provides insightful, concise summaries of team performance data. You respond only with the requested analysis in markdown format without any introductory text or explanations about your role.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the summary from the response
        summary = message.content[0].text

        # Convert to HTML for display
        return summary

    except Exception as e:
        logger.error(f"Error generating summary with Claude: {str(e)}")
        return f"**Error generating summary:** {str(e)}"