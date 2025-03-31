# NC Soccer Analytics Dashboard

![Dashboard Screenshot](./docs/images/dashboard.png)

A Plotly Dash application for exploring soccer match data and visualizing team performance.

## Features

- Filter by date range and team
- View key statistics including games played, win rate, goals scored, and goal difference
- Visualize performance over time
- Explore match results with a sortable table
- Analyze goal statistics

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Project Structure

```
ncsh-dashboard/
├── analysis/           # Application code
├── data/              # Data directory (mounted as volume)
│   └── data.parquet   # Main data file
├── Dockerfile
└── docker-compose.yml
```

### Running the Application

1. Clone this repository
2. Place your `data.parquet` file in the `data/` directory
3. Run `docker-compose up --build`
4. Access the dashboard at http://localhost:8090

### Environment Variables

You can customize the application using these environment variables:

- `BASIC_AUTH_USERNAME`: Username for dashboard access (default: ncsoccer)
- `BASIC_AUTH_PASSWORD`: Password for dashboard access (default: password)
- `PARQUET_FILE`: Path to the Parquet data file (default: /app/analysis/data/data.parquet)

The development server will be available at http://localhost:8050.

## Data

The application uses soccer match data from a Parquet file located in the `data/` directory. The data includes:

- Match dates
- Home and away teams
- Scores
- League information

## License

This project is licensed under the same terms as the parent project.