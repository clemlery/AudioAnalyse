import streamlit as st

from streaming_history_analyser.visualize import scatter_calculate_scores

st.subheader("Interest Score vs Commitment Ratio")
st.markdown("""
This scatter plot compares two dimensions:
- **Interest Score**: A custom score based on clicks, completed tracks, and skips.
- **Commitment Ratio**: The proportion of positive engagement (completed + clicked) over total interactions (including skips).

This visualization helps to identify which artists are both interesting and engaging for listeners.
    """)


########################################### Scatter plot Artists ###########################################
plot, df_interest_score, df_commitment_ratio = scatter_calculate_scores('./data/csv/artists_data.csv')
    
# plot scatter 
st.subheader("Scatter plot Artists")
st.pyplot(plot)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Interest Score")
st.write(df_interest_score)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Commitment Ratio")
st.write(df_commitment_ratio)
    
########################################### Scatter plot Tracks ###########################################
plot, df_interest_score, df_commitment_ratio = scatter_calculate_scores('./data/csv/tracks_data.csv')

# plot scatter 
st.subheader("Scatter plot Tracks")
st.pyplot(plot)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Interest Score")
st.write(df_interest_score)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Commitment Ratio")
st.write(df_commitment_ratio)
    
########################################### Scatter plot Releases ###########################################
plot, df_interest_score, df_commitment_ratio = scatter_calculate_scores('./data/csv/releases_data.csv')

# plot scatter 
st.subheader("Scatter plot Releases")
st.pyplot(plot)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Interest Score")
st.write(df_interest_score)
    
# Dataframe used sorted by interest score
st.subheader("Dataframe used sorted by Commitment Ratio")
st.write(df_commitment_ratio)