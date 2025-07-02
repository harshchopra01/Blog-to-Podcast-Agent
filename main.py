# importing important libraries of our Agent.
import os  # for getting api key's for openai and firecrawl and putting into the environment, such that agent can easily use from os env
from agno.agent import Agent  # importing agent from agno framework
from agno.models.openai import OpenAIChat  # for decision making and what to do next
from agno.tools.eleven_labs import ElevenLabsTools  # for giving voice to agent
from agno.tools.firecrawl import FirecrawlTools  # to fetch real time data through urls
from agno.agent import RunResponse  # for getting response from agent
from agno.utils.audio import write_audio_to_file  # for download the audio for future references
from agno.utils.log import logger  # for authentication
import streamlit as st  # for deploy app and use UI components
from uuid import uuid4  # generating random number

# creating UI through streamlit
st.set_page_config(page_title="Blog to Podcast Agent")
st.title("Agent")

# for api key which we are currently using
st.sidebar.header("API Keys")

# Initializing API Key's
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
elevenlabs_api_key = st.sidebar.text_input("ElevenLabs API Key", type="password")
firecrawl_api_key = st.sidebar.text_input("Firecrawl API Key", type="password")

# checking all keys are provided or not
keys_provided = all([openai_api_key, elevenlabs_api_key, firecrawl_api_key])

# taking url from user
url = st.text_input("Enter URL to translate:", "")

# creating a button for generating audio from url text only if all keys are provided
generate_button = st.button("GENERATE AUDIO", disabled=not keys_provided)

# managing if user doesn't enter all required keys
if not keys_provided:
    st.warning("PLEASE ENTER ALL THE REQUIRED KEYS!")

# checking conditions for generate button
if generate_button:
    if url.strip() == "":
        st.warning("PLEASE ENTER A URL")
    else:
        # give handle to os if all were correct
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key
        os.environ["ELEVENLABS_API_KEY"] = elevenlabs_api_key
        # changing data into voice holding with a processing spinner
        with st.spinner("PROCESSING DATA:"):
            try:
                # Creating our Agent Identity
                blog_to_podcast_agent = Agent(
                    name="Blog to Podcast",
                    agent_id="blog_to_podcast_agent",
                    model=OpenAIChat(id="gpt-4o"),
                    tools=[
                        ElevenLabsTools(
                            voice_id="JBFqnCBsd6RMkjVDRZzb",
                            model_id="eleven_multilingual_v2",
                            target_directory="audio_generations"
                        ),
                        FirecrawlTools(),
                    ],
                    description="You are an AI Agent that can generate audio using ElevenLabs API",
                    instructions=[
                        "When the user provides a blog post URL:",
                        "1. Use FirecrawlTools to scrape the blog content",
                        "2. Create a concise summary of the blog content that is more than 1000 characters long",
                        "3. The summary should capture the main points while being engaging and conversational",
                        "4. Use the ElevenLabsTools to convert the summary to audio",
                        "5. Ensure the summary is within the 2000 character limit to avoid ElevenLabs API limits"
                    ],
                    markdown=True,
                    debug_mode=True
                )

                # for running our agent
                podcast: RunResponse = blog_to_podcast_agent.run(
                    f"Convert the blog content to a podcast: {url}"
                )

                # Saving the generated audio
                save_dir = "audio_generations"
                os.makedirs(save_dir, exist_ok=True)

                # checking audio is faulty or not if faulty then re-run the agent else save the audio
                if podcast.audio and len(podcast.audio) > 0:
                    filename = f"{save_dir}/podcast_{uuid4()}.wav"
                    write_audio_to_file(
                        audio=podcast.audio[0].base64_audio,
                        filename=filename
                    )
                    # if all were smooth Podcast has been generated successfully
                    st.success("PODCAST GENERATED SUCCESSFULLY!")
                    audio_bytes = open(filename, "rb").read()

                    st.audio(audio_bytes, format="audio/wav")

                    st.download_button(
                        label="DOWNLOAD",
                        data=audio_bytes,
                        file_name="Generated_podcast.wav",
                        mime="audio/wav"
                    )

                else:
                    st.error("No audio generated, please try again")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                logger.error(f"Streamlit app error: {e}")
