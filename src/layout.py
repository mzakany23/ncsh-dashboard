from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from src.util import get_date_range_options

def get_loading_spinner():
    return dbc.Spinner(
        id="loading-spinner",
        fullscreen=True,
        color="#20A7C9",
        type="grow",
        children=[
        html.Div([
            html.H3("Loading NC Soccer Analytics Dashboard...",
                   style={"color": "#20A7C9", "text-align": "center", "margin-top": "20px"}),
            html.P("Please wait while we prepare your data.",
                  style={"color": "#484848", "text-align": "center"})
        ])
    ]
)

def init_layout(app, teams, team_groups=None, conn=None, min_date=None, max_date=None):
    if team_groups is None:
        team_groups = {}
    if min_date is None:
        min_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if max_date is None:
        max_date = datetime.now().strftime('%Y-%m-%d')
    loading_spinner = get_loading_spinner()
    app.layout = dbc.Container([
        # URL location component for tracking state
        dcc.Location(id='url', refresh=False),

        # Loading spinner container that will be shown/hidden via callbacks
        html.Div(
            id="loading-spinner-container",
            children=[loading_spinner],
            style={"display": "block"}  # Initially visible
        ),

        # Top Navigation Bar
        html.Div([
            # Main header row
            dbc.Row([
                # Title and star
                dbc.Col([
                    html.Div([
                        # Title
                        html.H3("NC Soccer Analytics Dashboard",
                               className="mb-0",
                               style={"font-size": "20px", "font-weight": "600"}),
                        # Star (hidden on mobile)
                        html.I(className="fas fa-star text-warning ms-2 d-none d-md-inline",
                              style={"font-size": "20px"}),
                        # Hamburger menu button (visible only on mobile)
                        html.Button(
                            html.I(className="fas fa-bars"),
                            id="mobile-menu-button",
                            className="d-md-none ms-2 btn btn-link text-dark",
                            style={"border": "none", "padding": "0"}
                        ),
                    ], className="d-flex align-items-center justify-content-between"),
                ], xs=12),
            ], className="mb-0"),

            # Mobile menu (collapsed by default)
            html.Div([
                # Version info
                html.Div([
                    html.Span("Published",
                             className="px-2 py-1 me-2",
                             style={"background-color": "#F5F5F5",
                                   "color": "#484848",
                                   "border-radius": "4px",
                                   "font-size": "12px",
                                   "font-weight": "500"}),
                    html.Span("v1.2.0",
                             style={"color": "#666666",
                                   "font-size": "12px",
                                   "font-weight": "500"}),
                ], className="mb-2"),
                # Logout button
                html.A(
                    dbc.Button(
                        [html.I(className="fas fa-sign-out-alt me-2"), "Logout"],
                        color="link",
                        className="text-secondary fw-normal p-0",
                        style={"fontSize": "14px"}
                    ),
                    href="/logout/",
                    className="text-decoration-none"
                )
            ], id="mobile-menu", className="d-md-none", style={"display": "none"}),

            # Desktop version info and logout (hidden on mobile)
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("Published",
                                     className="px-2 py-1 me-2",
                                     style={"background-color": "#F5F5F5",
                                           "color": "#484848",
                                           "border-radius": "4px",
                                           "font-size": "12px",
                                           "font-weight": "500"}),
                            html.Span("v1.2.0",
                                     style={"color": "#666666",
                                           "font-size": "12px",
                                           "font-weight": "500"}),
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.A(
                                dbc.Button(
                                    [html.I(className="fas fa-sign-out-alt me-2"), "Logout"],
                                    color="link",
                                    className="text-secondary fw-normal p-0",
                                    style={"fontSize": "14px"}
                                ),
                                href="/logout/",
                                className="text-decoration-none"
                            )
                        ], className="d-flex justify-content-end")
                    ], width=6)
                ])
            ], className="d-none d-md-block mt-2")
        ], className="py-3 px-3 mb-4", style={'background-color': 'white', 'border-bottom': '1px solid #E0E0E0'}),

        # Main content in two columns
        dbc.Row([
            # Left sidebar with filters
            dbc.Col([
                html.Div([
                    html.H4("Filters", className="mb-4", style={'color': '#20A7C9', 'font-size': 'calc(1.1rem + 0.3vw)'}),

                    html.Label("Team Selection Type:", className="fw-bold mb-2"),
                    dcc.RadioItems(
                        id='team-selection-type',
                        options=[
                            {'label': 'Individual Team', 'value': 'individual'},
                            {'label': 'Team Group', 'value': 'group'}
                        ],
                        value='group',
                        className="mb-2"
                    ),

                    html.Label("Team:", className="fw-bold mb-2"),
                    dcc.Dropdown(
                        id='team-dropdown',
                        options=[{'label': team, 'value': team} for team in teams if team != 'Key West (Combined)'],
                        value=teams[1] if len(teams) > 1 else teams[0],  # Default to first non-Key West team
                        searchable=True,
                        className="mb-4"
                    ),

                    html.Div(
                        [
                            html.Label("Select Team Group:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='team-group-dropdown',
                                options=[{'label': group_name, 'value': group_name} for group_name in team_groups.keys()],
                                value=None,  # Initially None, will be set by callback
                                searchable=True,
                                className="mb-2",
                                placeholder="Select a team group"
                            )
                        ],
                        id="team-group-selection-div",
                        style={'display': 'none'}
                    ),

                    html.Label("Opponent Filter:", className="fw-bold mb-2"),
                    dcc.RadioItems(
                        id='opponent-filter-type',
                        options=[
                            {'label': 'All Opponents', 'value': 'all'},
                            {'label': 'Specific Opponent(s)', 'value': 'specific'},
                            {'label': 'Team Group(s)', 'value': 'team_groups'},
                            {'label': 'Worthy Adversaries', 'value': 'worthy'}
                        ],
                        value='all',
                        className="mb-2"
                    ),

                    html.Div(
                        [
                            html.Label("Select Opponent(s):", className="fw-bold mb-2", id="opponent-selection-label"),
                            dcc.Dropdown(
                                id='opponent-selection',
                                options=[], # Will be updated dynamically
                                value=[],
                                multi=True,
                                searchable=True,
                                className="mb-2 multi-select-dropdown",
                                placeholder="Select one or more opponents",
                                style={
                                    'min-height': '38px',
                                    'height': 'auto',
                                    'margin-bottom': '10px',
                                    'width': '100%'
                                }
                            ),
                            # New dropdown specifically for team groups
                            html.Div([
                                html.Label("Select Team Group(s):", className="fw-bold mb-2"),
                                dcc.Dropdown(
                                    id='opponent-team-groups',
                                    options=[{'label': group_name, 'value': group_name} for group_name in team_groups.keys()],
                                    value=[],
                                    multi=True,
                                    searchable=True,
                                    className="mb-2",
                                    placeholder="Select one or more team groups"
                                ),
                            ], id="team-groups-opponent-div", style={'display': 'none'}),
                            html.Div(
                                [
                                    html.Label("Competitiveness Threshold:", className="fw-bold mb-2"),
                                    dcc.Slider(
                                        id='competitiveness-threshold',
                                        min=0,
                                        max=100,
                                        step=5,
                                        value=30,
                                        marks={
                                            0: {'label': '0%', 'style': {'color': '#44B78B'}},
                                            30: {'label': '30%', 'style': {'color': '#20A7C9'}},
                                            70: {'label': '70%', 'style': {'color': '#FF7F44'}},
                                            100: {'label': '100%', 'style': {'color': '#E04355'}}
                                        },
                                        className="mb-1"
                                    ),
                                    html.P("Teams you've lost to or had close matches with (higher = more challenging opponents)",
                                        className="small text-muted mb-3")
                                ],
                                id="worthy-adversaries-controls",
                                style={'display': 'none'}
                            )
                        ],
                        id="opponent-selection-div",
                        style={'display': 'none'}
                    ),

                    html.Label("Quick Date Selection:", className="fw-bold mb-2"),
                    dcc.Dropdown(
                        id='date-preset-dropdown',
                        options=get_date_range_options(conn),
                        value='this_year',
                        clearable=False,
                        className="mb-4"
                    ),

                    html.Label("Custom Date Range:", className="fw-bold mb-2"),
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=min_date,
                        max_date_allowed=max_date,
                        start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d'),
                        display_format='YYYY-MM-DD',
                        className="mb-4"
                    ),

                    html.Hr(className="my-4"),

                    # Team Groups Management Section
                    html.Div([
                        html.H5("Team Groups Management", className="mb-3", style={'color': '#20A7C9'}),

                        html.Label("Create New Team Group:", className="fw-bold mb-2"),
                        dbc.Input(
                            id="new-group-name",
                            type="text",
                            placeholder="Enter group name",
                            className="mb-2"
                        ),
                        html.Div([
                            html.Label("Select teams to include:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='teams-for-group',
                                options=[{'label': team, 'value': team} for team in teams],
                                value=[],
                                multi=True,
                                className="mb-2",
                                placeholder="Select teams to include in this group",
                                style={'position': 'relative', 'zIndex': 1030}
                            ),
                        ], style={'position': 'relative', 'zIndex': 1030}),
                        dbc.Button(
                            "Create Group",
                            id="create-group-button",
                            color="primary",
                            className="mb-3"
                        ),

                        html.Div([
                            html.Label("Edit Existing Group:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='edit-group-dropdown',
                                options=[{'label': group_name, 'value': group_name} for group_name in team_groups.keys()],
                                placeholder="Select group to edit",
                                className="mb-2",
                                style={'position': 'relative', 'zIndex': 1020}, # Increased z-index to appear above other elements
                            ),
                            html.Label("Group Name:", className="fw-bold mb-2"),
                            dbc.Input(
                                id="edit-group-name",
                                type="text",
                                placeholder="Enter new group name",
                                className="mb-2"
                            ),
                            html.Label("Select teams to edit:", className="fw-bold mb-2"),
                            html.Div([
                                dcc.Dropdown(
                                    id='edit-teams-for-group',
                                    options=[{'label': team, 'value': team} for team in teams],
                                    value=[],
                                    multi=True,
                                    className="mb-2",
                                    placeholder="Select teams to include in this group",
                                    style={'position': 'relative', 'zIndex': 1010}
                                ),
                            ], style={'position': 'relative', 'zIndex': 1010}),
                            dbc.ButtonGroup([
                                dbc.Button(
                                    "Update Group",
                                    id="update-group-button",
                                    color="primary",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Delete Group",
                                    id="delete-group-button",
                                    color="danger"
                                ),
                            ], className="mb-3 d-flex"),
                        ], id="edit-group-div", style={'position': 'relative', 'zIndex': 1000}),

                        html.Div(id="group-management-status", className="small text-muted my-2")
                    ], className="mb-4"),

                    html.Div([
                        html.P([
                            html.I(className="fas fa-info-circle me-2"),
                            "Select filters above to analyze team performance data."
                        ], className="small text-muted mb-0")
                    ])
                ], className="filter-panel p-3 p-md-4"),  # Add responsive padding
            ], xs=12, md=4, lg=3, className="filter-sidebar mb-4"),

            # Main content area
            dbc.Col([
                # Summary statistics cards in a single row at the top of the story
                html.Div([
                    html.H4("Performance Summary", className="section-header"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-robot ai-icon")
                        ], id="ai-summary-icon",
                           className="btn-icon",
                           title="Generate AI analysis"),
                        dcc.Tooltip(
                            id="ai-tooltip",
                            children=["Click to generate AI insights"],
                            style={
                                "backgroundColor": "rgba(32, 167, 201, 0.9)",
                                "color": "white",
                                "borderRadius": "4px",
                                "padding": "8px 12px",
                                "fontSize": "14px",
                                "fontWeight": "500",
                                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)"
                            }
                        )
                    ], className="ai-icon-container")
                ], className="section-header-container d-flex align-items-center"),

                # Container for AI summary
                html.Div(id='ai-summary-container', className='ai-summary-content mb-3', style={'display': 'none'}),

                dcc.Loading(
                    id="loading-performance-metrics",
                    type="circle",
                    color="#20A7C9",
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Games Played"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="games-played", children="0", className="summary-value")),
                                        html.Div("Total matches", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1"),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Win Rate"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="win-rate", children="0.0%", className="summary-value")),
                                        html.Div("Percentage of wins", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1"),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Loss Rate"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="loss-rate-display", children="0.0%", className="summary-value")),
                                        html.Div("Percentage of losses", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1"),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Goals Scored"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="goals-scored", children="0", className="summary-value")),
                                        html.Div("Total goals for", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1"),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Goals Conceded"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="goals-conceded-display", children="0", className="summary-value")),
                                        html.Div("Total goals against", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1"),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Goal Difference"),
                                    dbc.CardBody([
                                        html.Div(html.H3(id="goal-difference", children="0", className="summary-value")),
                                        html.Div("Goals scored - conceded", className="text-muted small")
                                    ])
                                ], className="summary-card h-100")
                            ], xs=12, sm=6, md=4, lg=2, className="mb-2 px-1")
                        ], className="mb-4 mx-0")
                    ]
                ),

                # Performance trend chart
                html.H4("Performance Over Time", className="section-header"),
                dcc.Loading(
                    id="loading-performance-chart",
                    type="default",
                    color="#20A7C9",
                    children=[
                        dbc.Card([
                            dbc.CardBody([
                                html.P("This chart shows the cumulative wins, draws, and losses over the selected time period."),
                                dcc.Graph(id="performance-trend")
                            ])
                        ], className="mb-4")
                    ]
                ),

                # Goal statistics - with bar chart and pie chart side by side
                html.H4("Goal Analysis", className="section-header"),
                dcc.Loading(
                    id="loading-goal-charts",
                    type="default",
                    color="#20A7C9",
                    children=[
                        dbc.Card([
                            dbc.CardBody([
                                html.P("Breakdown of goals scored, conceded, and the resulting goal difference."),
                                dbc.Row([
                                    dbc.Col([
                                        dcc.Graph(id="goal-stats-chart")
                                    ], xs=12, md=6, className="mb-3 mb-md-0"),
                                    dbc.Col([
                                        dcc.Graph(id="goal-stats-pie")
                                    ], xs=12, md=6)
                                ])
                            ])
                        ], className="mb-4")
                    ]
                ),

                # Opponent Analysis Section (conditionally displayed)
                html.Div(
                    [
                        html.H4("Opponent Analysis", className="section-header"),
                        dcc.Loading(
                            id="loading-opponent-analysis",
                            type="default",
                            color="#20A7C9",
                            children=[
                                dbc.Card([
                                    dbc.CardHeader("Opponent Performance Comparison"),
                                    dbc.CardBody([
                                        html.P(id="opponent-analysis-text", children="Detailed comparison against selected opponents."),
                                        dcc.Graph(id="opponent-comparison-chart")
                                    ])
                                ], className="mb-4"),

                                dbc.Row([
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader("Win/Loss Distribution"),
                                            dbc.CardBody([
                                                dcc.Graph(id="opponent-win-rate-chart")
                                            ])
                                        ])
                                    ], xs=12, md=6, className="mb-3 mb-md-0"),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader("Goal Performance"),
                                            dbc.CardBody([
                                                dcc.Graph(id="opponent-goal-diff-chart")
                                            ])
                                        ])
                                    ], xs=12, md=6),
                                ], className="mb-3")
                            ]
                        )
                    ],
                    id="opponent-analysis-section",
                    className="mb-4",
                    style={'display': 'block'}  # Make visible by default
                ),

                # Detailed match results
                html.H4("Match Details", className="section-header"),
                dcc.Loading(
                    id="loading-match-results",
                    type="default",
                    color="#20A7C9",
                    children=[
                        dbc.Card([
                            dbc.CardBody([
                                html.P("Complete record of individual matches during the selected period."),
                                dash_table.DataTable(
                                    id='match-results-table',
                                    columns=[
                                        {"name": "Date", "id": "date", "type": "datetime"},
                                        {"name": "Home Team", "id": "home_team"},
                                        {"name": "Away Team", "id": "away_team"},
                                        {"name": "Score", "id": "score"},
                                        {"name": "Result", "id": "result"}
                                    ],
                                    page_size=10,
                                    sort_action='native',
                                    sort_mode='single',
                                    sort_by=[{'column_id': 'date', 'direction': 'desc'}],
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px',
                                        'fontFamily': 'Inter, Helvetica Neue, Helvetica, Arial, sans-serif',
                                        'color': '#323232'
                                    },
                                    style_header={
                                        'backgroundColor': '#F5F5F5',
                                        'color': '#484848',
                                        'fontWeight': 'bold',
                                        'textAlign': 'left',
                                        'border': 'none',
                                        'borderBottom': '1px solid #E0E0E0'
                                    },
                                    style_data={
                                        'border': 'none',
                                        'borderBottom': '1px solid #DEE2E6'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'filter_query': '{result} contains "Win"'},
                                            'backgroundColor': 'rgba(68, 183, 139, 0.1)',
                                            'borderLeft': '3px solid #44B78B'
                                        },
                                        {
                                            'if': {'filter_query': '{result} contains "Draw"'},
                                            'backgroundColor': 'rgba(252, 199, 0, 0.1)',
                                            'borderLeft': '3px solid #FCC700'
                                        },
                                        {
                                            'if': {'filter_query': '{result} contains "Loss"'},
                                            'backgroundColor': 'rgba(224, 67, 85, 0.1)',
                                            'borderLeft': '3px solid #E04355'
                                        },
                                        {
                                            'if': {'column_id': 'result', 'filter_query': '{result} contains "Win"'},
                                            'color': '#44B78B',
                                            'fontWeight': 'bold'
                                        },
                                        {
                                            'if': {'column_id': 'result', 'filter_query': '{result} contains "Draw"'},
                                            'color': '#FCC700',
                                            'fontWeight': 'bold'
                                        },
                                        {
                                            'if': {'column_id': 'result', 'filter_query': '{result} contains "Loss"'},
                                            'color': '#E04355',
                                            'fontWeight': 'bold'
                                        }
                                    ]
                                )
                            ])
                        ], className="mb-4")
                    ]
                ),

                # Footer
                dbc.Row([
                    dbc.Col([
                        html.Hr(),
                        html.Div([
                            html.Span("NC Soccer Hudson Analytics Dashboard", className="text-muted me-2"),
                        ], className="text-center py-3")
                    ], width=12)
                ], className="mt-4")
            ], xs=12, md=8, lg=9)
        ], className="mt-3"),

        # Hidden div for storing initial load state
        html.Div(id='initial-load', style={'display': 'none'})
    ], fluid=True, className="px-3 px-md-4")