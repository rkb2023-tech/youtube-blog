import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import tempfile

# Streamlit page config
st.set_page_config(page_title="YouTube to Blog Summarizer", layout="wide")

# Sidebar for API Key and model selection
st.sidebar.title("🔐 OpenAI API Key")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
model_choice = st.sidebar.selectbox("Choose OpenAI Model", ["gpt-4o-mini", "gpt-4o"])

# Main interface
st.title("🎥 YouTube to Blog Summarizer ✍️")
youtube_url = st.text_input("🔗 Enter YouTube Video URL", "")

# Utility to extract video ID
def get_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ['www.youtube.com', 'youtube.com']:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith('/embed/'):
            return query.path.split('/')[2]
        elif query.path.startswith('/v/'):
            return query.path.split('/')[2]
    return None

# Fetch the transcript
def download_transcript(video_url):
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return "\n".join([entry['text'] for entry in transcript])

# Scrape video title from YouTube
def fetch_video_title(video_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(video_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.title.string.replace(" - YouTube", "").strip()

# Summarize transcript with GPT
def summarize_transcript(transcript_text, video_title, api_key, model):
    prompt = f"""
Write a blog article based on the YouTube video titled: **{video_title}**

The blog should include:
- The title as the main heading
- Summary of technical discussions related to ai
- Limit the characters within 2950 .

Here is the transcript:
{transcript_text}
"""

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a blog writer summarizing video transcripts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4096
    )

    return response.choices[0].message.content

# Main logic
if st.button("📝 Generate Blog Summary"):
    if not openai_api_key:
        st.warning("Please enter your OpenAI API Key in the sidebar.")
    elif not youtube_url:
        st.warning("Please enter a valid YouTube video URL.")
    else:
        try:
            with st.spinner("📥 Fetching transcript..."):
                transcript_text = download_transcript(youtube_url)
            with st.spinner("📺 Fetching video title..."):
                video_title = fetch_video_title(youtube_url)
            with st.spinner("🧠 Generating blog summary..."):
                summary = summarize_transcript(transcript_text, video_title, openai_api_key, model_choice)

            st.success("✅ Blog summary generated!")
            st.markdown(f"### 📰 Blog Based on: **{video_title}**")
            st.markdown(summary)

            # Create a temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
                f.write(summary)
                temp_file_name = f.name

            with open(temp_file_name, "rb") as file:
                st.download_button(
                    label="📥 Download Blog for LinkedIn Post",
                    data=file,
                    file_name=f"{video_title}.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"🚨 Error: {e}")
