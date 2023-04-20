import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None
from scipy.stats import percentileofscore
import warnings
warnings.filterwarnings("ignore")
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import dash
from jupyter_dash import JupyterDash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

agility_scores = pd.read_csv('https://raw.githubusercontent.com/nkal22/combine_score/main/agility_scores.csv', header = 1).rename(columns={'LANE AGILITY TIME \n(SECONDS)':'Lane Agility', 'SHUTTLE RUN \n(SECONDS)':'Shuttle Run', 'THREE QUARTER SPRINT \n(SECONDS)':'Three Quarter Sprint', 'STANDING VERTICAL LEAP \n(INCHES)':'Standing Vert', 'MAX VERTICAL LEAP \n(INCHES)':'Max Vert'}).drop('MAX BENCH PRESS \n(REPETITIONS)', axis = 1)
size_grades = pd.read_csv('https://raw.githubusercontent.com/nkal22/combine_score/main/Size_grades.csv', header = 1).rename(columns={'HAND LENGTH (INCHES)':'Hand Length', 'HAND WIDTH (INCHES)':'Hand Width', 'HEIGHT W/O SHOES':'Height W/O Shoes', 'STANDING REACH':'Standing Reach', 'WEIGHT (LBS)':'Weight', 'WINGSPAN': 'Wingspan'}).drop(['BODY FAT %','HEIGHT W/ SHOES'], axis = 1)

size_grades['Year'] = agility_scores['Year']

total_df = agility_scores.merge(size_grades, on=['PLAYER', 'POS', 'Year'])

total_df['Height W/O Shoes'] = total_df['Height W/O Shoes'].astype(str)
total_df['Standing Reach'] = total_df['Standing Reach'].astype(str)

total_df = total_df.loc[total_df['Height W/O Shoes'] != 'nan'].reset_index(drop = True).replace({'nan': "0' 0''", '-': 0})
                        
for i in range(len(total_df)):
    
    total_df['Height W/O Shoes'][i] = total_df['Height W/O Shoes'][i][:-2]
    total_df['Standing Reach'][i] = total_df['Standing Reach'][i][:-2]
    total_df['Wingspan'][i] = total_df['Wingspan'][i][:-2]
    height, inches = total_df['Height W/O Shoes'][i].rsplit("'")
    height = float(height)
    inches = float(inches)
    inches = inches / 12
    height = height + inches
    height2, inches2 = total_df['Standing Reach'][i].rsplit("'")
    height2 = float(height2)
    inches2 = float(inches2)
    inches2 = inches2 / 12
    height2 = height2 + inches2
    height3, inches3 = total_df['Wingspan'][i].rsplit("'")
    height3 = float(height3)
    inches3 = float(inches3)
    inches3 = inches3 / 12
    height3 = height3 + inches3
    total_df['Wingspan'][i] = round(height3, 2)
    total_df['Height W/O Shoes'][i] = round(height, 2)
    total_df['Standing Reach'][i] = round(height2, 2)
    
    
    
    


cols = total_df.columns[2:]


for i in cols:
    total_df[i] = total_df[i].astype(float)
    
total_df[['primary_pos', 'secondary_pos']] = total_df['POS'].str.split('-', n=1, expand=True)

total_df = total_df.drop('POS', axis = 1)

total_df = total_df[total_df['primary_pos'].notnull()]

positions = total_df['primary_pos'].unique()
percentiles_df = pd.DataFrame(columns=['Player', 'Year', 'Column', 'Value', 'Percentile', 'Position'])
scores_df = pd.DataFrame(columns=['Player', 'Year', 'Physical Score', 'Vert Score', 'Agility Score', 'Position'])


for i in positions:
    
    position_frame = total_df.loc[(total_df['primary_pos'] == i) | (total_df['secondary_pos'] == i)]

    position_frame = position_frame.drop(['primary_pos', 'secondary_pos'], axis = 1).reset_index(drop=True).replace(0, np.nan)
    
    percentiles_df_pos = pd.DataFrame(columns=['Player', 'Year', 'Column', 'Value', 'Percentile', 'Position'])
    
    
    scores_df_pos = pd.DataFrame(columns=['Player', 'Year', 'Physical Score', 'Vert Score', 'Agility Score'])
    
    for col in position_frame.columns[1:]: # Exclude the 'Customer ID' column
        col_data = position_frame[col].dropna()
        for m, val in enumerate(position_frame[col]):
            if pd.isna(val):
                pctl = np.nan
            pctl = percentileofscore(col_data, val)
            pctl = round(pctl, 1)
            player_id = position_frame.loc[m, 'PLAYER']
            year_id = position_frame.loc[m, 'Year']
            percentiles_df_pos = percentiles_df_pos.append({'Player': player_id, 'Year': year_id, 'Column': col, 'Value': val, 'Percentile': pctl, 'Position': i}, ignore_index=True)
        
    for k in range(len(percentiles_df_pos)):
        if (percentiles_df_pos.iloc[k]['Column'] == 'Lane Agility') or (percentiles_df_pos.iloc[k]['Column'] == 'Shuttle Run') or (percentiles_df_pos.iloc[k]['Column'] == 'Three Quarter Sprint'):
            percentiles_df_pos.at[k, 'Percentile'] = round(100 - percentiles_df_pos.iloc[k]['Percentile'], 1)
        else:
            continue

            
    player_names = percentiles_df_pos['Player'].unique()
    
    for f in player_names:
        test_player = percentiles_df_pos.loc[percentiles_df_pos['Player'] == f].reset_index(drop=True)

        player_id = test_player['Player'][0]
        year_id = test_player['Year'][0]
        agility_score = round((test_player['Percentile'].iloc[0:3].sum())/3, 1)
        vert_score = round((test_player['Percentile'].iloc[3:5].sum())/2, 1)
        phys_score = round((test_player['Percentile'].iloc[8:12].sum())/4, 1)

        scores_df_pos = scores_df_pos.append({'Player': player_id, 'Year': year_id, 'Physical Score': phys_score, 'Vert Score': vert_score, 'Agility Score': agility_score}, ignore_index=True)

    scores_df_pos['Raw Score'] = 0
    scores_df_pos['Position'] = i

    for j in range(len(scores_df_pos)):
        if (scores_df_pos['Physical Score'][j] == 0) or (scores_df_pos['Vert Score'][j] == 0) or (scores_df_pos['Agility Score'][j] == 0):
            scores_df_pos['Raw Score'][j] = np.nan
        else:
            scores_df_pos['Raw Score'][j] = round((scores_df_pos['Physical Score'][j] + scores_df_pos['Vert Score'][j] + scores_df_pos['Agility Score'][j])/3, 1)
    
    new_col_data = scores_df_pos['Raw Score'].dropna()
    pctl_list = []
    for val in scores_df_pos['Raw Score']:
        if pd.isna(val):
            pctl = np.nan
        pctl = percentileofscore(new_col_data, val)
        pctl = round(pctl, 1)
        pctl_list.append(pctl)
    scores_df_pos['Combine Score'] = pctl_list
    scores_df = pd.concat([scores_df, scores_df_pos])
    percentiles_df = pd.concat([percentiles_df, percentiles_df_pos])

years = percentiles_df['Year'].unique()

percentiles_df = percentiles_df.sort_values(['Year', 'Player'], ascending = [True, True]).reset_index(drop=True)
        
for col in scores_df.columns[1:5]:
    scores_df[col] = scores_df[col].astype(float)
    
for column in percentiles_df.columns[3:5]:
    percentiles_df[column] = percentiles_df[column].astype(float)
    
percentiles_df = percentiles_df.rename(columns={"Column": "Drill/Attribute"})

branham_tab = percentiles_df.loc[percentiles_df['Player'] == 'Malaki Branham']
branham_scores = scores_df.loc[scores_df['Player'] == 'Malaki Branham']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'padding': '18px',
    'fontWeight': 'bold',
    'fontSize': '32px',
    'color': 'black',
    'backgroundColor': 'white',
    'align': 'center'
}

tab_selected_style = {
    'borderTop': '5px solid #d6d6d6',
    'borderBottom': '5px solid #d6d6d6',
    'backgroundColor': 'black',
    'color': 'white',
    'padding': '18px',
    'fontSize': '32px',
    'align': 'center'
}

image_style = {
    'display': 'block',
    'margin-left': 'auto',
    'margin-right': 'auto',
    'width': '50%',
    'height': '50%',
}

app.layout = html.Div([
    html.H1(['Introducing: Combine Score', html.Br(), 'By: Nick Kalinowski (kalidrafts)'], style={'backgroundColor':'darkred',"text-align": "center","color": "white","font-size": "40px","padding": "40px 0 40px 10px"}),
    html.Div([
        html.Img(src= 'https://cdn.nba.com/teams/legacy/www.nba.com/wizards/sites/wizards/files/dsc09950.jpg', alt='image', style=image_style),
        html.P("For many prospects and teams, the NBA Draft Combine represents the pinnacle of the predraft experience. The annual event brings together 76 of the highest regarded prospects to Chicago, where they participate in drills, submit physical measurements, scrimmage against other players, and interview with team representatives. While many of the projected top picks in the draft have opted out of most of the combine events in recent years, the combine has gained newfound significance following the NBA's recent introduction of a new rule forcing players to partake in the combine or risk being declared ineligible. As such, it will soon become easier to compare the measurables and test results of the players of today to their counterparts in the recent past, which piqued the idea of a metric similar to the NFL Draft's Relative Athletic Score, developed by Kent Lee Platte, to quantify the physical traits, athleticism and agility of NBA prospects."),
        html.P("Much like RAS, Combine Score works by first grabbing the results of physical testing, athleticism measurements (more specifically, vertical jump), and agility drills, and collects the percentile score of each result relative to their listed position. If a player is listed at multiple positions (e.g. PG and SG), the percentiles are calculated seperately for each individual position. An example of these results can be shown below, for Ohio State's Malaki Branham in last year's combine."),
        dbc.Container([
           dbc.Row([
                    dbc.Col([
                            dcc.Graph(id='branham_tab', figure = ff.create_table(branham_tab))
                        ], width=8) 
                    ],justify="center",align="center"),
        ]),
        html.P("The results are then aggregated together into three categories: Physical Score, Vert Score, and Agility Score. Physical Score consists of the average of the percentile results for Height Without Shoes, Weight, Wingspan, and Standing Reach, while Vert Score includes Max Vert and Standing Vert, and Agility Score averages the values for Lane Agility, Shuttle Run, and Three Quarter Court Sprint. Together, these three values are again averaged together to create the final Raw Score; however, unlike the NFL, basketball players do not tend to score well in all three categories (the highest Raw Score ever being Tony Mitchell's 86.8 in 2013). As a result, I scaled the Raw Score results from 0-100, by position, to create the final Combine Score. Note that Hand Length and Width are not considered for Physical Score, but are still interesting to look at. The results for Branham are shown below:"),
        dbc.Container([
           dbc.Row([
                    dbc.Col([
                            dcc.Graph(id='branham_score', figure = ff.create_table(branham_scores))
                        ], width=8) 
                    ],justify="center",align="center"),
        ]),
        html.P("In the near future, I hope to explore how Combine Score connects to NBA performance, both by position and draft range. Likewise, with the new rule coming into place in 2024, the Combine results database will only increase in size, and include top prospects, so eventually there may be no need to re-scale the Raw Scores. But for now, I believe that Combine Score, much like RAS, provides a numerical insight into a player's physical and athletic profile, and should be a metric that can be used in conjunction with in-person evaluations to assist in NBA draft scouting."),
        html.P("Below, you will be able to view any historical player's results and Combine Score, broken down by drill and subcategory. In addition, I also provide multiple helpful graphics, including a bar chart which compares the selected player's subscores to the average player at their position, and spider charts to further illustrate a prospect's strengths and weaknesses. As new data comes in, I will continually update this site every year, and provide new visualizations and datatables."),
        dbc.Container([
                 dbc.Row([
                        dbc.Col([
                            html.Label('Select Combine Year',style={'padding-top':'2.5%','fontWeight': 'bold','align':'center'}),
                            dcc.Dropdown(id='year',options=years, value=years[0])
                        ], width=4,),
                        dbc.Col([
                            html.Label('Select Player',style={'padding-top':'2.5%','fontWeight': 'bold','align':'center'}),
                            dcc.Dropdown(id='player',options=[])
                        ], width=4),
                    dbc.Col([
                            html.Label('Select Position',style={'padding-top':'2.5%','fontWeight': 'bold','align':'center'}),
                            dcc.Dropdown(id='position',options=[])
                        ], width=4)
                    ],justify="center"),
        ]),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                        dcc.Graph(id='percentiletab')
                    ], width=8),
                dbc.Col([
                        dcc.Graph(id='scoretab')
                    ],width=8)
                ],justify="center",align="center"),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='avgscore')
                ], width = 10),
            ], justify="center",align="center"),
            dbc.Row([
                dbc.Col([
                        dcc.Graph(id='physspider')
                    ], width=5),
                dbc.Col([
                        dcc.Graph(id='drillspider')
                    ],width=5)
                ],justify="center",align="center"), 
        ]),
        html.Br(),
        html.P("I hope you enjoyed my project, and I will be sure to provide more updates soon! In the meantime, you can reach out to me on twitter @kalidrafts if you have any questions about Combine Score or would like to offer any suggestions for model improvements/visualizations. I would also like to shoutout all the awesome professors at the UVA School of Data Science who taught me the skills I needed to put this together. See you all again soon!"),
               
              
    ])
])

@app.callback(
    Output('player', 'options'),
    Output('player', 'value'),
    [Input('year','value')])
def update_player(year):
    if year == None:
        year = 2000
    year_percentiles = percentiles_df.loc[percentiles_df['Year'] == year]
    player_options = [{'label':i,'value':i} for i in year_percentiles["Player"].unique()]
    return player_options, player_options[0]['value']

@app.callback(
    Output('position', 'options'),
    Output('position', 'value'),
    [Input('player', 'value')])
def update_position(player):
    if player == None:
        player = "Ochai Agbaji"
    player_percentiles = percentiles_df.loc[percentiles_df['Player'] == player]
    position_options = [{'label':i,'value':i} for i in player_percentiles["Position"].unique()]
    return position_options, position_options[0]['value']
    

@app.callback(
    Output('percentiletab', 'figure'),
    Output('scoretab', 'figure'),
    Output('avgscore', 'figure'),
    Output('physspider', 'figure'),
    Output('drillspider', 'figure'),
    [Input('year', 'value'),
     Input('player', 'value'),
     Input('position', 'value')])
def make_figures(year, player, position):
    year_percentiles = percentiles_df.loc[(percentiles_df['Year'] == year) & (percentiles_df['Player'] == player) & (percentiles_df['Position'] == position) & (percentiles_df['Drill/Attribute'] != 'Year')].sort_values('Drill/Attribute')
    year_scores = scores_df.loc[(scores_df['Year'] == year) & (scores_df['Player'] == player) & (scores_df['Position'] == position)]
    
    if len(year_percentiles) == 0:
        percent_table = go.Figure()
        score_table = go.Figure()
        avg_score = go.Figure()
        spider_fig = go.Figure()
        spider_drills = go.Figure()
    else:
        percent_table = ff.create_table(year_percentiles)
        score_table = ff.create_table(year_scores)
        position_avg_scores = scores_df[~scores_df.isnull()].groupby('Position').mean().drop('Year', axis=1).round(2)
        
        year_scores = year_scores.drop('Year', axis=1)
        
        position_avg_scores = position_avg_scores.reset_index()

        position_avg_scores['Player'] = 'Average Player'

        position_avg_scores = position_avg_scores[year_scores.columns]
        
        avg_scores = position_avg_scores.loc[position_avg_scores['Position'].isin(year_scores['Position'])]

        total = pd.concat([year_scores, avg_scores]).reset_index(drop=True)
        
        players = total['Player']

        positions = total['Position']

        total = total.drop(['Player', 'Position'], axis=1)

        df = pd.DataFrame(total.stack()).reset_index().rename(columns={'level_0':'Player', 'level_1': 'Score', 0: 'Value'})

        df['Player'] = df['Player'].replace({0: players[0], 1: players[1]})

        avg_score = px.bar(df, x="Score", y="Value", 
                         color="Player", title=players[0] + " vs. Average " + positions[0], barmode="group")
        
        player_phys = year_percentiles.loc[(year_percentiles['Drill/Attribute'] == 'Height W/O Shoes') | (year_percentiles['Drill/Attribute'] == 'Standing Reach') | (year_percentiles['Drill/Attribute'] == 'Weight') | (year_percentiles['Drill/Attribute'] == 'Wingspan') | (year_percentiles['Drill/Attribute'] == 'Hand Length') | (year_percentiles['Drill/Attribute'] == 'Hand Width')]
        spider_fig = px.line_polar(player_phys, r='Percentile', theta='Drill/Attribute', title = players[0] + " Physical Attributes Spider Chart", line_close=True)
        spider_fig.update_traces(fill='toself')
        
        player_drills = year_percentiles.loc[(year_percentiles['Drill/Attribute'] == 'Lane Agility') | (year_percentiles['Drill/Attribute'] == 'Shuttle Run') | (year_percentiles['Drill/Attribute'] == 'Three Quarter Sprint') | (year_percentiles['Drill/Attribute'] == 'Standing Vert') | (year_percentiles['Drill/Attribute'] == 'Max Vert')]
        spider_drills = px.line_polar(player_drills, r='Percentile', theta='Drill/Attribute', title = players[0] + " Drill Results Spider Chart", line_close=True)
        spider_drills.update_traces(fill='toself')


    return percent_table, score_table, avg_score, spider_fig, spider_drills

if __name__ == '__main__':
    app.run_server(debug=False)

