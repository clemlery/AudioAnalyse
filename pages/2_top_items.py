import streamlit as st

from streaming_history_analyser.visualize import plot_bar_chart, top_artists, top_releases, top_tracks
    
# Streamlit App
st.title("Spotify Streaming Analytics Dashboard")

# Top Artists
st.subheader("Top 10 Artists by Streaming Time")
st.markdown("""
This bar chart displays the **top 10 artists** based on total streaming time (in minutes).
It highlights which artists received the most listening time and overall attention.
""")
st.pyplot(plot_bar_chart(top_artists(), "Top Artists"))

# Top Tracks
st.subheader("Top 10 Tracks by Streaming Time")
st.markdown("""
This chart shows the **10 most streamed tracks**.
It provides insight into your favorite songs or the most frequently played ones in your library.
""")
st.pyplot(plot_bar_chart(top_tracks(), "Top Tracks"))

# Top Releases
st.subheader("Top 10 Releases by Streaming Time")
st.markdown("""
This chart highlights the **top 10 releases** (albums or singles) with the highest total streaming time.
It helps to understand which full-length projects or EPs had the most impact.
""")
st.pyplot(plot_bar_chart(top_releases(), "Top Releases"))

