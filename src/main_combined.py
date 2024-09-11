from openai import OpenAI
from pyannote.audio import Pipeline
import requests
import os
import sys
import argparse
import subprocess
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pydub import AudioSegment
from config import *
from colorama import init, Fore, Back, Style
from playsound import playsound
from pygame import mixer
from cleanup import cleanup_temp_files
import threading

# Initialize colorama
init(autoreset=True)

def print_colored(text, color=Fore.GREEN, style=Style.BRIGHT):
    print(f"{style}{color}{text}")
    playsound('coin.mp3')

def display_intro():
    intro = f"""
    {Fore.CYAN}███████╗ {Fore.MAGENTA}██████╗ {Fore.YELLOW}███╗   ██╗{Fore.GREEN}███████╗{Fore.BLUE}███████╗{Fore.RED}██╗ ██████╗ {Fore.WHITE}██╗  ██╗{Fore.CYAN}████████╗
    {Fore.CYAN}╚══███╔╝{Fore.MAGENTA}██╔═══██╗{Fore.YELLOW}████╗  ██║{Fore.GREEN}██╔════╝{Fore.BLUE}██╔════╝{Fore.RED}██║██╔════╝ {Fore.WHITE}██║  ██║{Fore.CYAN}╚══██╔══╝
    {Fore.CYAN}  ███╔╝ {Fore.MAGENTA}██║   ██║{Fore.YELLOW}██╔██╗ ██║{Fore.GREEN}█████╗  {Fore.BLUE}███████╗{Fore.RED}██║██║  ███╗{Fore.WHITE}███████║{Fore.CYAN}   ██║   
    {Fore.CYAN} ███╔╝  {Fore.MAGENTA}██║   ██║{Fore.YELLOW}██║╚██╗██║{Fore.GREEN}██╔══╝  {Fore.BLUE}╚════██║{Fore.RED}██║██║   ██║{Fore.WHITE}██╔══██║{Fore.CYAN}   ██║   
    {Fore.CYAN}███████╗{Fore.MAGENTA}╚██████╔╝{Fore.YELLOW}██║ ╚████║{Fore.GREEN}███████╗{Fore.BLUE}███████║{Fore.RED}██║╚██████╔╝{Fore.WHITE}██║  ██║{Fore.CYAN}   ██║   
    {Fore.CYAN}╚══════╝{Fore.MAGENTA} ╚═════╝ {Fore.YELLOW}╚═╝  ╚═══╝{Fore.GREEN}╚══════╝{Fore.BLUE}╚══════╝{Fore.RED}╚═╝ ╚═════╝ {Fore.WHITE}╚═╝  ╚═╝{Fore.CYAN}   ╚═╝   
                             
{Fore.YELLOW}ZoneSight - Combined Narrative and Data Output{Style.RESET_ALL}
    """
    print(intro)

def play_background_music():
    mixer.init()
    mixer.music.load('aquatic_ambience.mp3')
    mixer.music.play(-1)  # -1 means loop indefinitely

def stop_background_music():
    mixer.music.stop()

def convert_to_wav(input_file):
    if input_file.lower().endswith('.wav'):
        return input_file
    
    output_file = os.path.splitext(input_file)[0] + '.wav'
    try:
        subprocess.run(['ffmpeg', '-i', input_file, output_file], check=True)
        print_colored(f"Converted {input_file} to {output_file}", Fore.GREEN)
        return output_file
    except subprocess.CalledProcessError as e:
        print_colored(f"Error converting file to WAV: {e}", Fore.RED)
        return None

def split_audio(file_path, max_size_mb=24):
    audio = AudioSegment.from_wav(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    duration_ms = len(audio)
    chunk_duration_ms = int((max_size_bytes / len(audio.raw_data)) * duration_ms)
    
    # Create temp directory if it doesn't exist
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    chunks = []
    for i, chunk_start in enumerate(range(0, duration_ms, chunk_duration_ms)):
        chunk_end = min(chunk_start + chunk_duration_ms, duration_ms)
        chunk = audio[chunk_start:chunk_end]
        chunk_file = os.path.join(temp_dir, f"chunk_{i}.wav")
        chunk.export(chunk_file, format="wav")
        chunks.append(chunk_file)
        
        print_colored(f"Chunk {i}: Start={chunk_start}ms, End={chunk_end}ms, Duration={chunk_end-chunk_start}ms, Size={os.path.getsize(chunk_file)} bytes", Fore.YELLOW)
    
    return chunks

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
        print_colored(f"Error in transcription: {e}", Fore.RED)
        return None

def load_diarization_pipeline():
    try:
        print_colored("Attempting to load the diarization pipeline...", Fore.CYAN)
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                            use_auth_token=HUGGING_FACE_TOKEN)
        print_colored("Diarization pipeline loaded successfully.", Fore.GREEN)
        return pipeline
    except Exception as e:
        print_colored(f"Error loading diarization pipeline: {e}", Fore.RED)
        print_colored("\nTroubleshooting steps:", Fore.YELLOW)
        print("1. Ensure you have an active internet connection.")
        print("2. Verify that you've accepted the user conditions at https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("3. Check that your Hugging Face token is correct in the .env file.")
        print("4. Try running 'huggingface-cli login' in your terminal and enter your token when prompted.")
        print("5. If the issue persists, try clearing your Hugging Face cache:")
        print("   - On macOS/Linux: rm -rf ~/.cache/huggingface")
        print("   - On Windows: rmdir /s /q %USERPROFILE%\\.cache\\huggingface")
        print("6. Ensure that you have the latest version of pyannote.audio installed:")
        print("   pip install --upgrade pyannote.audio")
        sys.exit(1)

def transcribe_and_diarize(audio_file, perform_diarization=True):
    try:
        chunks = split_audio(audio_file)
        transcriptions = []
        
        for chunk in chunks:
            print_colored(f"Transcribing chunk: {chunk}", Fore.CYAN)
            transcription = transcribe_audio(chunk)
            if transcription is None:
                return None
            transcriptions.append(transcription)
        
        full_transcription = " ".join(transcriptions)

        if not perform_diarization:
            return {"Speaker 1": full_transcription}

        diarization_pipeline = load_diarization_pipeline()

        print_colored("Performing speaker diarization...", Fore.MAGENTA)
        diarization = diarization_pipeline(audio_file)

        print_colored("Combining transcription with speaker labels...", Fore.BLUE)
        speaker_transcripts = {}
        
        total_duration = max(segment.end for segment in diarization.get_timeline())
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            
            start_ratio = start_time / total_duration
            end_ratio = end_time / total_duration
            start_char = int(start_ratio * len(full_transcription))
            end_char = int(end_ratio * len(full_transcription))
            
            segment_text = full_transcription[start_char:end_char].strip()
            if segment_text:
                if speaker not in speaker_transcripts:
                    speaker_transcripts[speaker] = []
                speaker_transcripts[speaker].append(segment_text)

        for speaker in speaker_transcripts:
            speaker_transcripts[speaker] = " ".join(speaker_transcripts[speaker])

        return speaker_transcripts
    except Exception as e:
        print_colored(f"Error in transcription and diarization: {e}", Fore.RED)
        return None

def read_competency_definitions(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print_colored(f"Error reading competency definitions: {e}", Fore.RED)
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
        1. An Overview section announcing the purpose of this report and the insights it tries to provide, THEN, listing ALL of the competencies, and describing the report briefly.
        2. A section for competency insights, with subsections for each competency
        3. Evidence of competency development for each defined competency
        4. Areas for improvement or further development
        5. Specific examples from the transcript that demonstrate competency-related behaviors or knowledge
        6. OVERALL ASSESSMENT of the student's competency development in a final section

        Use appropriate HTML tags to structure your report. Include inline CSS for basic styling. Ensure the HTML is well-formatted and easy to read.
        """
        
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        print_colored("Extracting competency insights...", Fore.CYAN)
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()

        print_colored("Competency insights extracted successfully.", Fore.GREEN)
        return response_json['choices'][0]['message']['content']
    except requests.RequestException as e:
        print_colored(f"Error in API request: {e}", Fore.RED)
        return None
    except Exception as e:
        print_colored(f"Error in competency insight extraction: {e}", Fore.RED)
        return None

def extract_competency_data(transcript, competency_definitions):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": SITE_URL,
            "X-Title": SITE_NAME,
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Analyze the following transcript and extract quantitative data about student competency development based on the provided competency definitions. Generate a JSON object that includes ratings and observations for EACH of the competencies in the competency definitions text. Focus on providing numerical ratings and specific examples from the transcript that demonstrate competency-related behaviors or knowledge.

        Competency Definitions:
        {competency_definitions}

        Transcript:
        {transcript}

        Please provide a structured JSON object with the following format:
        {{
            "competencies": [
                {{
                    "name": "Competency Name",
                    "rating": 0-10,
                    "observations": [
                        "Specific example or observation from the transcript",
                        "Another example or observation"
                    ],
                    "areas_for_improvement": [
                        "Suggestion for improvement",
                        "Another suggestion"
                    ]
                }},
                // ... repeat for all competencies
            ],
            "overall_assessment": "A brief overall assessment of the student's competency development"
        }}

        Ensure that you provide a rating between 0 and 10 for each competency, with 0 being the lowest and 10 being the highest level of competency demonstrated. Include at least two specific observations and two areas for improvement for each competency.
        """
        
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        print_colored("Extracting competency data...", Fore.CYAN)
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        
        response_json = response.json()
        
        if 'choices' not in response_json or len(response_json['choices']) == 0:
            print_colored("Error: Invalid response structure from API", Fore.RED)
            return None
        
        content = response_json['choices'][0]['message']['content']
        
        # Find the start of the JSON object
        json_start = content.find('{')
        if json_start == -1:
            print_colored("Error: No JSON object found in the response", Fore.RED)
            return None
        
        json_content = content[json_start:]
        
        try:
            parsed_data = json.loads(json_content)
        except json.JSONDecodeError as e:
            print_colored(f"Error parsing JSON: {e}", Fore.RED)
            print_colored("Content that failed to parse:", Fore.YELLOW)
            print(json_content[:500] + "..." if len(json_content) > 500 else json_content)
            return None
        
        if 'competencies' not in parsed_data or 'overall_assessment' not in parsed_data:
            print_colored("Error: Parsed data does not have the expected structure", Fore.RED)
            return None
        
        print_colored("Competency data extracted successfully.", Fore.GREEN)
        return parsed_data
    except requests.RequestException as e:
        print_colored(f"Error in API request: {e}", Fore.RED)
        return None
    except Exception as e:
        print_colored(f"Error in competency data extraction: {e}", Fore.RED)
        print_colored(f"Exception details: {str(e)}", Fore.RED)
        return None

def create_radar_chart(competency_data, speaker):
    categories = [comp['name'] for comp in competency_data['competencies']]
    values = [comp['rating'] for comp in competency_data['competencies']]

    figure = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))

    figure.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title=f"Competency Radar Chart for {speaker}"
    )

    return figure

def generate_combined_report(narrative_reports, competency_data):
    combined_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Combined Competency Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
            h1, h2 { color: #2c3e50; }
            .speaker-section { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
            .radar-chart { width: 100%; height: 500px; }
        </style>
    </head>
    <body>
        <h1>Combined Competency Report</h1>
    """

    for speaker, narrative in narrative_reports.items():
        combined_html += f"""
        <div class="speaker-section">
            <h2>{speaker}</h2>
            <div>{narrative}</div>
            <div id="radar-chart-{speaker}" class="radar-chart"></div>
            <script>
                var data = {json.dumps(competency_data[speaker])};
                Plotly.newPlot('radar-chart-{speaker}', [{{
                    type: 'scatterpolar',
                    r: data.competencies.map(comp => comp.rating),
                    theta: data.competencies.map(comp => comp.name),
                    fill: 'toself'
                }}], {{
                    polar: {{ radialaxis: {{ visible: true, range: [0, 10] }} }},
                    showlegend: false,
                    title: 'Competency Radar Chart for {speaker}'
                }});
            </script>
        </div>
        """

    combined_html += """
    </body>
    </html>
    """

    return combined_html

def main():
    display_intro()
    
    # Start playing background music
    background_music_thread = threading.Thread(target=play_background_music)
    background_music_thread.start()

    
    audio_file = input(f"{Fore.YELLOW}Enter the name of the audio file: {Style.RESET_ALL}")
    competency_file = input(f"{Fore.YELLOW}Enter the name of the competencies file: {Style.RESET_ALL}")

    if not os.path.exists(audio_file):
        print_colored(f"Error: The audio file {audio_file} does not exist.", Fore.RED)
        return
    if not os.path.exists(competency_file):
        print_colored(f"Error: The competency definition file {competency_file} does not exist.", Fore.RED)
        return
    if not os.path.exists('sound.mp3'):
        print_colored(f"Error: The sound file sound.mp3 does not exist.", Fore.RED)
        return
    if not os.path.exists('coin.mp3'):
        print_colored(f"Error: The sound file coin.mp3 does not exist.", Fore.RED)
        return
    if not os.path.exists('aquatic_ambience.mp3'):
        print_colored(f"Error: The sound file aquatic_ambience.mp3 does not exist.", Fore.RED)
        return

    wav_file = convert_to_wav(audio_file)
    if wav_file is None:
        return

    print_colored(f"{'[INIT]':=^40}", Fore.CYAN)
    print_colored("Transcribing audio and performing diarization...", Fore.CYAN)
    print_colored(f"{'[PROCESSING]':=^40}", Fore.CYAN)
    
    
    speaker_transcripts = transcribe_and_diarize(wav_file, True)
    if speaker_transcripts is None:
        stop_background_music()
        return

    print_colored("Reading competency definitions...", Fore.CYAN)
    competency_definitions = read_competency_definitions(competency_file)
    if competency_definitions is None:
        stop_background_music()
        return

    narrative_reports = {}
    competency_data = {}
    for speaker, transcript in speaker_transcripts.items():
        print_colored(f"Extracting competency insights for {speaker}...", Fore.CYAN)
        narrative_reports[speaker] = extract_competency_insights(transcript, competency_definitions)
        
        print_colored(f"Extracting competency data for {speaker}...", Fore.CYAN)
        competency_data[speaker] = extract_competency_data(transcript, competency_definitions)

    print_colored("Generating combined report...", Fore.CYAN)
    combined_report = generate_combined_report(narrative_reports, competency_data)

    print_colored("\nWriting output to combined_report.html...", Fore.CYAN)
    try:
        with open('combined_report.html', 'w', encoding='utf-8') as report_file:
            report_file.write(combined_report)
        print_colored("Combined report successfully written to combined_report.html", Fore.GREEN)

        print_colored(f"{'[COMPLETE]':=^40}", Fore.GREEN)
        
        # Stop background music and play completion sound
        stop_background_music()
        playsound('sound.mp3')
        print_colored("Played completion sound", Fore.GREEN)

        # Clean up temporary files
        cleanup_temp_files()
        print_colored("Temporary files cleaned up", Fore.GREEN)
    except Exception as e:
        print_colored(f"Error writing output: {e}", Fore.RED)
        stop_background_music()

if __name__ == "__main__":
    main()