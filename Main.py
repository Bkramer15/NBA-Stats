from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.endpoints import playerawards  #this endpoint gives data based on awards that player searched for has on
from nba_api.stats.static import players
import dash
from dash import dcc, html,State
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout for the web application
app.layout = html.Div([
    html.H1("NBA Player Stats Dashboard"),
    html.P("Find stats about your favorite NBA player!"),

    # Input field for Player ID
    dcc.Input(
        id="player",
        type="number",
        placeholder="Enter a player ID",
    ),

    # Dropdown to select the stat to visualize
    dcc.Dropdown(
        id="stat_dropdown",
        options=[
            {'label': 'Points (PTS)', 'value': 'PTS'},
            {'label': 'Assists (AST)', 'value': 'AST'},
            {'label': 'Rebounds (REB)', 'value': 'REB'},
            {'label': 'Blocks (BLK)', 'value': 'BLK'},
            {'label': 'Steals (STL)', 'value': 'STL'},
            {'label': 'Field Goal Percentage (FG_PCT)', 'value': 'FG_PCT'},
            {'label': 'Free Throw Percentage (FT_PCT)', 'value': 'FT_PCT'},
            {'label': '3-Point Percentage (3P_PCT)', 'value': '3P_PCT'},
            {'label': 'All Stats', 'value': 'all'}
        ],
        placeholder="Select a stat"
    ),

    # Radio items for selecting the type of graph
    dcc.RadioItems(
        id="graph_type_radio",
        options=[
            {'label': 'Line Graph', 'value': 'line'},
            {'label': 'Bar Graph', 'value': 'bar'},
            {'label': 'Scatter Plot', 'value': 'scatter'}
        ],
        value='line',  # Default selection for graph type
    ),

    # Button to trigger the search and visualization
    html.Button('Search', id='search_button', n_clicks=0),

    # Graph component to display the stats
    dcc.Graph(id="player_stats_graph"),

    # Div to display player info
    html.Div(id="player_info")
])


# Class to handle fetching player information and stats
class PlayerStats:
    def __init__(self, player_id):
        self.player_id = player_id

    def player_career_stats(self):
        """Fetch the player's career stats from the API."""
        player_career = playercareerstats.PlayerCareerStats(player_id=self.player_id)
        career_stats_df = player_career.get_data_frames()[0]  # Returns a dataframe
        return career_stats_df

    def common_player_info(self):
        """Fetch common player info from the API."""
        player_data = commonplayerinfo.CommonPlayerInfo(player_id=self.player_id)
        player_data_df = player_data.get_data_frames()[0]
        if not player_data_df.empty:
            relevant_columns = ['SCHOOL', 'TEAM_NAME', 'HEIGHT', 'WEIGHT']
            filtered_data = player_data_df[relevant_columns]
            return filtered_data.iloc[0]  # Return the first row of data
        else:
            return "Player not found"

    def player_info(self):
        """Fetch and return basic player information."""
        nba_players = players.get_players()
        player = next((player for player in nba_players if player['id'] == self.player_id), None)
        if player:
            return player
        else:
            return "Player not found"

    #thismethod

# Callback to handle user interaction and dynamic updates
@app.callback(
    #handling of what data will be displayed
    [Output("player_stats_graph", "figure"), 
     Output("player_info", "children")],

     #handling and tracki
    [Input("search_button", "n_clicks")],
    [State("player", "value"),
     State("stat_dropdown", "value"),
     State("graph_type_radio", "value")]
)
def update_graph_and_info(n_clicks, player_id, stat, graph_type):
    if player_id is None or player_id <= 0:
        return {}, "Please enter a valid Player ID."

    # Fetch player stats
    player = PlayerStats(player_id)
    try:
        career_stats_df = player.player_career_stats()

        # Check for 'all' stats option
        if stat == "all":
            fig = None  # Initialize an empty figure
            for column in career_stats_df.columns:
                if column not in ["SEASON_ID", "PLAYER_ID"]:  # Skip non-stat columns
                    if graph_type == "line":
                        trace = px.line(career_stats_df, x="SEASON_ID", y=column, title=f"{column} over the Career")
                    elif graph_type == "scatter":
                        trace = px.scatter(career_stats_df, x="SEASON_ID", y=column, title=f"{column} over the Career")
                    elif graph_type == "bar":
                        trace = px.bar(career_stats_df, x="SEASON_ID", y=column, title=f"{column} over the Career")
                    
                    if fig is None:
                        fig = trace
                    else:
                        fig.add_trace(trace.data[0])

            return fig, f"Player {player.player_info()['full_name']} - Stats Over Career"

        elif stat in career_stats_df.columns:
            if graph_type == "line":
                fig = px.line(career_stats_df, x="SEASON_ID", y=stat, title=f"{stat} over Career")
            elif graph_type == "scatter":
                fig = px.scatter(career_stats_df, x="SEASON_ID", y=stat, title=f"{stat} over Career")
            elif graph_type == "bar":
                fig = px.bar(career_stats_df, x="SEASON_ID", y=stat, title=f"{stat} over Career")
            
            return fig, f"Player {player.player_info()['full_name']} - {stat} over Career"
        else:
            return {}, "Invalid stat selection!"

    except Exception as e:
        return {}, f"Error fetching data for Player ID {player_id}: {str(e)}"


# Running the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)

