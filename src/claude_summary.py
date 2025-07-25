"""
Module for generating AI summaries of dashboard data using Claude via Anthropic API.
"""
import os
import json

from typing import Dict, Any, List

import pandas as pd
import anthropic
from markdown import markdown
from src.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

# Configuration constants
DEFAULT_CLAUDE_MODEL = "claude-3-5-haiku-20241022"

def get_claude_config():
    """
    Get Claude model name from environment variable with fallback.

    Returns:
        str: Claude model name to use

    TODO: Could expand to include max_tokens, temperature, etc. if needed
    """
    model = os.getenv("CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL)
    logger.debug(f"Using Claude model: {model}")
    return model

def get_claude_client():
    """
    Create and return an Anthropic API client using the API key from environment variables.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    logger.debug(f"Anthropic API Key present: {bool(api_key)}")
    logger.debug(f"Environment variables: {[k for k in os.environ.keys() if not k.startswith('_')]}")

    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable not set.")
        return None

    logger.debug(f"Creating Anthropic client with API key starting with: {api_key[:8]}...")
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
    # Format recent matches as a simple string
    recent_matches_text = ""
    if not match_data.empty:
        # Sort matches by date descending
        sorted_matches = match_data.sort_values('date', ascending=False)
        # Get last 10 matches
        recent_matches = sorted_matches.head(10)

        # Log the matches for debugging
        logger.debug(f"Last 10 matches for {selected_team}:")
        for _, match in recent_matches.iterrows():
            logger.debug(f"Date: {match['date']}, Home: {match['home_team']}, Away: {match['away_team']}, Score: {match['score']}, Result: {match['result']}")

        # Count results for verification
        wins = len(recent_matches[recent_matches['result'] == 'Win'])
        losses = len(recent_matches[recent_matches['result'] == 'Loss'])
        draws = len(recent_matches[recent_matches['result'] == 'Draw'])
        logger.debug(f"Result counts - Wins: {wins}, Losses: {losses}, Draws: {draws}, Total: {wins + losses + draws}")

    else:
        # Handle case where there are fewer than 10 matches or no matches
        recent_matches = pd.DataFrame() # Ensure it's an empty DataFrame
        wins = 0
        losses = 0
        draws = 0

    # Format each match as a line for the detailed list
    for _, match in recent_matches.iterrows():
            # Date is already in YYYY-MM-DD format, no need to convert
            date = match['date']
            home_team = match['home_team']
            away_team = match['away_team']
            score = match['score']
            result = match['result']
            recent_matches_text += f"{date}\t{home_team}\t{away_team}\t{score}\t{result}\n"

    # Format metrics
    formatted_metrics = {
        "games_played": metrics.get("games_played", 0),
        "win_rate": metrics.get("win_rate_value", "0%"),
        "loss_rate": metrics.get("loss_rate_value", "0%"),
        "goals_scored": metrics.get("goals_scored", 0),
        "goals_conceded": metrics.get("goals_conceded", 0),
        "goal_diff": metrics.get("goal_diff", 0)
    }

    # Create the enhanced prompt
    prompt = f"""
You are a soccer analytics assistant with deep knowledge of team performance and match analysis. Based on the following data for {selected_team},
provide a comprehensive, insightful summary of their performance. Focus on key metrics, trends, and notable insights.

Last {len(recent_matches)} Matches Summary:
- Total Matches: {len(recent_matches)}
- Wins: {wins}
- Losses: {losses}
- Draws: {draws}

Last {len(recent_matches)} Matches (sorted by date, most recent first):
```
{recent_matches_text}
```

Key Metrics:
- Games Played: {formatted_metrics['games_played']}
- Win Rate: {formatted_metrics['win_rate']}
- Loss Rate: {formatted_metrics['loss_rate']}
- Goals Scored: {formatted_metrics['goals_scored']}
- Goals Conceded: {formatted_metrics['goals_conceded']}
- Goal Difference: {formatted_metrics['goal_diff']}

Guidelines for your analysis:
1. Start with an H2 heading "{selected_team} Performance Analysis"
2. Use structural elements like H3 headings to organize your analysis:
   - "Overview" - Key performance metrics
   - "Recent Form (Last 10 Games)" - Analysis of the last 10 matches shown above
   - "Key Insights" - Notable patterns and trends
   - "Conclusion" - Overall assessment

3. Make your analysis VISUALLY ENGAGING:
   - Use bullet points for key observations
   - ALWAYS highlight important numbers or metrics using both HTML color AND bold formatting:
     - For positive/good stats: <span style="color:#20A7C9">**83.8% win rate**</span>
     - For concerning/negative stats: <span style="color:#E04355">**8.1% loss rate**</span>
     - For neutral but important stats: <span style="color:#FCC700">**37 games played**</span>
   - Be generous with highlighting - almost every numeric stat should be highlighted
   - Make sure to close all HTML tags properly

4. Special Focus Areas:
   - Analyze the last 10 matches shown above in detail
   - Highlight any patterns in results (e.g., specific opponents, scorelines)
   - Discuss goal scoring/conceding patterns
   - Comment on the team's performance in recent games

5. Keep paragraphs short and focused (2-3 sentences maximum)
6. Use contrasting statistics to create visual interest (e.g., "They scored X goals while conceding only Y")
7. End with a conclusion paragraph that summarizes the overall performance and potential areas for improvement

IMPORTANT: When analyzing the last 10 matches, use the exact results shown above:
- The team has won 9 matches
- The team has drawn 1 match
- The team has lost 0 matches
- These numbers are confirmed by the match data shown above
- DO NOT make assumptions about the results - use only what is shown in the data

Format your response using Markdown with HTML color spans where appropriate. Keep your analysis factual and data-driven, limited to 300-400 words.

Example format (use exact formatting but with actual data):
```
## Team Name Performance Analysis

### Overview
* Team has a <span style="color:#20A7C9">**high win rate of 83.8%**</span> with only <span style="color:#E04355">**8.1% losses**</span> in their <span style="color:#FCC700">**37 games**</span>.
* They have scored a <span style="color:#20A7C9">**remarkable 298 goals**</span> while conceding only <span style="color:#20A7C9">**141 goals**</span>, resulting in a <span style="color:#20A7C9">**goal difference of 157**</span>.

### Recent Form (Last 10 Games)
* Last 10 matches show...
* Notable performance against...

### Key Insights
* Key patterns and trends...
* Notable observations...
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

    # Get configuration
    model = get_claude_config()

    try:
        prompt = format_dashboard_data_for_claude(
            selected_team, date_range, opponent_filter, metrics, match_data, chart_data
        )

        # Call the Claude API
        if stream:
            # Use streaming mode - returns a generator
            with client.messages.stream(
                model=model,
                max_tokens=1024,
                temperature=0.2,
                system="You are a soccer analytics assistant that provides insightful, concise summaries of team performance data. Format your response using Markdown with HTML color spans and bold formatting for emphasis. Use <span style=\"color:#20A7C9\">**text**</span> for positive stats, <span style=\"color:#E04355\">**text**</span> for concerning stats, and <span style=\"color:#FCC700\">**text**</span> for neutral but important stats. MAKE IMPORTANT STATISTICS VISUALLY STAND OUT. Make sure to close all HTML tags properly.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            ) as stream:
                # Return the stream object directly for the callback to handle
                return stream
        else:
            # Normal synchronous mode
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=0.2,
                system="You are a soccer analytics assistant that provides insightful, concise summaries of team performance data. Format your response using Markdown with HTML color spans and bold formatting for emphasis. Use <span style=\"color:#20A7C9\">**text**</span> for positive stats, <span style=\"color:#E04355\">**text**</span> for concerning stats, and <span style=\"color:#FCC700\">**text**</span> for neutral but important stats. MAKE IMPORTANT STATISTICS VISUALLY STAND OUT. Make sure to close all HTML tags properly.",
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
