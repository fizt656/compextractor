from openai import OpenAI
from pyannote.audio import Pipeline
import requests
import os
import sys
import argparse
from config import *

def display_intro():
    intro = """
 _______ ____  _____
|__   __|  _ \|__  /
   | |  | |_) | / / 
   | |  |  __/ / /_ 
   |_|  |_|   /____|
   
Text Parsing Zone?    """
    print(intro)

def transcribe_audio(audio_file):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(audio_file, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio, 
                response_format="text"
            )
        return transcription
    except Exception as e:
        print(f"Error in transcription: {e}")
        return None

def load_diarization_pipeline():
    try:
        print("Attempting to load the diarization pipeline...")
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                            use_auth_token=HUGGING_FACE_TOKEN)
        print("Diarization pipeline loaded successfully.")
        return pipeline
    except Exception as e:
        print(f"Error loading diarization pipeline: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure you have an active internet connection.")
        print("2. Verify that you've accepted the user conditions at https://hf.co/pyannote/speaker-diarization")
        print("3. Check that your Hugging Face token is correct in the .env file.")
        print("4. Try running 'huggingface-cli login' in your terminal and enter your token when prompted.")
        print("5. If the issue persists, try clearing your Hugging Face cache:")
        print("   - On macOS/Linux: rm -rf ~/.cache/huggingface")
        print("   - On Windows: rmdir /s /q %USERPROFILE%\\.cache\\huggingface")
        sys.exit(1)

def transcribe_and_diarize(audio_file, perform_diarization=False):
    try:
        transcription = transcribe_audio(audio_file)
        if transcription is None:
            return None

        if not perform_diarization:
            return transcription

        diarization_pipeline = load_diarization_pipeline()

        print("Performing speaker diarization...")
        diarization = diarization_pipeline(audio_file)

        print("Combining transcription with speaker labels...")
        diarized_transcript = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment_start = turn.start
            segment_end = turn.end
            segment_text = transcription[segment_start:segment_end]
            diarized_transcript.append(f"Speaker {speaker}: {segment_text}")

        return "\n".join(diarized_transcript)
    except Exception as e:
        print(f"Error in transcription and diarization: {e}")
        return None

def read_competency_definitions(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading competency definitions: {e}")
        return None

def extract_competency_insights(transcript, competency_definitions):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": SITE_URL,
            "X-Title": SITE_NAME,
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Analyze the following transcript and extract insights about student competency development based on the provided competency definitions. Generate an HTML report that includes an analysis for EACH of the competencies in the competency definitions text. Focus on identifying evidence of competency development, areas for improvement, and specific examples from the transcript that demonstrate competency-related behaviors or knowledge.  

        Competency Definitions:
        {competency_definitions}

        Transcript:
        {transcript}

        Please provide a structured HTML report of competency development, including:
        1. An Overview section listing ALL of the competencies and describing the report briefly.
        2. A section for competency insights, with subsections for each competency arranged in two columns with 6 rows per column
        3. Evidence of competency development for each defined competency
        4. Areas for improvement or further development
        5. Specific examples from the transcript that demonstrate competency-related behaviors or knowledge
        6. Overall assessment of the student's competency development

        Use appropriate HTML tags to structure your report. Include inline CSS for basic styling. Ensure the HTML is well-formatted and easy to read. The HTML structure should be as follows:

        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Competency Insights Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                .competency-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                }}
                .competency-item {{
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>TPZ Competency Insights Report</h1>
            
            <section id="overview">
                <h2>Overview</h2>
                <!-- Include the Overview section here -->
            </section>
            
            <section id="competency-insights">
                <h2>Competency Insights</h2>
                <div class="competency-grid">
                    <!-- Include competency analysis here, with each competency in a div with class "competency-item" -->
                </div>
            </section>
        </body>
        </html>

        There are multiple speakers in this conversation. Pick them apart based on how they talk and label the speakers accordingly (if they don't give their name, give them a descriptive name).
        
        Ensure that your response is a complete, valid HTML document with the competencies arranged in two columns, 6 rows per column.
        """
        
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()

        return response_json['choices'][0]['message']['content']
    except requests.RequestException as e:
        print(f"Error in API request: {e}")
        return None
    except Exception as e:
        print(f"Error in competency insight extraction: {e}")
        return None

def main(perform_diarization):
    display_intro()
    
    audio_file = input("Enter the name of the audio file: ")
    competency_file = input("Enter the name of the competencies file: ")

    if not os.path.exists(audio_file):
        print(f"Error: The audio file {audio_file} does not exist.")
        return

    if not os.path.exists(competency_file):
        print(f"Error: The competency definition file {competency_file} does not exist.")
        return

    print("Transcribing audio..." + (" and performing diarization" if perform_diarization else ""))
    transcript = transcribe_and_diarize(audio_file, perform_diarization)
    if transcript is None:
        return

    print("Reading competency definitions...")
    competency_definitions = read_competency_definitions(competency_file)
    if competency_definitions is None:
        return

    print("Extracting competency insights and generating HTML report...")
    html_report = extract_competency_insights(transcript, competency_definitions)
    if html_report is None:
        return

    print("\nWriting output to report.html...")
    try:
        with open('report.html', 'w', encoding='utf-8') as report_file:
            report_file.write(html_report)
        print("Report successfully written to report.html")
    except Exception as e:
        print(f"Error writing to report.html: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process audio file for transcription, optional diarization, and competency insight extraction.")
    parser.add_argument("--diarize", action="store_true", help="Enable diarization (speaker identification)")
    args = parser.parse_args()

    main(args.diarize)