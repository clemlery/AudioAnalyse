import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import random

# We load a font in order to be able to display Japanese characters
jp_prop = fm.FontProperties(fname='./data/font/NotoSansJP-Regular.ttf')
fm.fontManager.addfont('./data/font/NotoSansJP-Regular.ttf')
plt.rcParams['font.family'] = 'Noto Sans JP'


# Top Streamed
def top_artists(csv_artists_path : str = './data/csv/artists_data.csv'):
    a_df = pd.read_csv(csv_artists_path)
    sorted_a_df = a_df.sort_values('Minutes_Streamed', ascending=False)
    return sorted_a_df.head(10)
    
def top_tracks(csv_tracks_path : str = './data/csv/tracks_data.csv'):
    t_df = pd.read_csv(csv_tracks_path)
    sorted_t_df = t_df.sort_values('Minutes_Streamed', ascending=False)
    return sorted_t_df.head(10)

    
def top_releases(csv_releases_path : str = './data/csv/releases_data.csv'):
    r_df = pd.read_csv(csv_releases_path)
    sorted_r_df = r_df.sort_values('Minutes_Streamed', ascending=False)
    return sorted_r_df.head(10)



def plot_bar_chart(df, title):
    colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd',
              '#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
    rdm_colors = random.sample(colors, k=len(df))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df['Name'], df['Minutes_Streamed'], color=rdm_colors)
    ax.set_title(title, fontproperties=jp_prop)
    ax.set_xlabel('Name', fontproperties=jp_prop)
    ax.set_ylabel('Minutes Streamed', fontproperties=jp_prop)
    ax.tick_params(axis='x', rotation=90)
    return fig
    

    
def scatter_calculate_scores(path: str):
    w_click = 1.0
    w_done  = 0.5
    w_skip  = 0.2

    a_df = pd.read_csv(path)
    filt = (a_df['Track_Done_Count'] > 50) & (a_df['Click_Row_Count'] > 0)
    df = a_df.loc[filt].copy()

    df['Interest_Score'] = (
        w_done  * df['Track_Done_Count']
      + w_click * df['Click_Row_Count']
      - w_skip  * df['Skipped_Count']
    )

    df['Commitment_Ratio'] = (
        (df['Track_Done_Count'] + df['Click_Row_Count'])
        / (df['Track_Done_Count'] + df['Click_Row_Count'] + df['Skipped_Count'])
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df['Interest_Score'], df['Commitment_Ratio'])
    ax.set_xlabel('Interest Score')
    ax.set_ylabel('Commitment Ratio')
    ax.set_title('Interest Score vs Commitment Ratio')
    ax.plot(
        [df['Interest_Score'].min(), df['Interest_Score'].max()],
        [df['Commitment_Ratio'].min(), df['Commitment_Ratio'].max()],
        color='red'
    )
    
    df_selected = df[['Name', 'Interest_Score', 'Commitment_Ratio']]
    
    return fig, df_selected.sort_values('Interest_Score', ascending=False).head(50), df_selected.sort_values('Commitment_Ratio', ascending=False).head(50)
    
    