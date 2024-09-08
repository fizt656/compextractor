![Competency Extractor](banner.jpg)

# Competency Extractor

This is a prototype tool for extracting student competency insights from audio recordings of student presentations or discussions. It now supports multi-speaker analysis through diarization and includes a new data output mode with radar graph visualizations, as well as a combined mode that provides both narrative and visual outputs.

## Prerequisites

- Python 3.7 or higher
- ffmpeg (for audio file conversion)

## Installation

1. Install ffmpeg:
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system PATH.
   - On macOS: Use Homebrew: `brew install ffmpeg`
   - On Linux: Use your package manager, e.g., `sudo apt-get install ffmpeg`

2. Clone this repository:
   ```bash
   git clone https://github.com/fizt656/compextractor.git
   cd compextractor
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

5. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

6. Copy the `.env.example` file to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file with your actual API keys.

7. Set up the Hugging Face token:
   - Go to [Hugging Face](https://huggingface.co/) and create an account if you don't have one.
   - Generate an access token in your account settings.
   - Add the token to your `.env` file:
     ```
     HUGGING_FACE_TOKEN=your_token_here
     ```
   - Run `huggingface-cli login` in your terminal and enter your token when prompted.

8. Accept the user conditions for the pyannote/speaker-diarization model:
   - Visit https://huggingface.co/pyannote/speaker-diarization
   - Click on "Access repository" and accept the terms.

9. Set up pyannote:
   - After accepting the use policies on Hugging Face, run the `copy_model_files.py` script in the project directory. This script will copy the necessary files to the correct folders.
   - Ensure you're logged in with the same Hugging Face token that's in your `.env` file.

## Usage

1. Prepare your audio file (supported formats include MP3, MP4, WAV) and competencies file (a text file with competency definitions).

2. Run the script in one of the following modes:
   - For narrative output:
     ```bash
     python src/main.py [--diarize]
     ```
   - For data output with radar graphs:
     ```bash
     python src/main_data.py [--diarize] [--visualize]
     ```
   - For combined narrative and data output:
     ```bash
     python src/main_combined.py
     ```
   Use the `--diarize` flag for multi-speaker analysis and the `--visualize` flag to generate radar charts (where applicable).

3. When prompted, enter the names of your audio file, competencies file, and sound file to play when done.

4. The script will automatically convert non-WAV audio files to WAV format for processing.

5. For large audio files, the script will automatically split them into smaller chunks to avoid API limitations.

6. If diarization is enabled, the script will identify different speakers in the audio.

7. The script will process the audio and generate output based on the mode:
   - Narrative mode: Generates a `report.html` file with the transcript and competency insights.
   - Data mode: Generates a `competency_data.json` file with structured data and, if visualize is enabled, radar chart HTML files for each speaker.
   - Combined mode: Generates a `combined_report.html` file with both narrative insights and radar charts for each speaker.

8. Open the generated HTML files in a web browser to view the formatted report, radar charts, or combined output.

## Combined Narrative and Data Output

In addition to providing separate outputs if needed, the Competency Extractor now includes a combined output mode that provides both narrative insights and data visualizations in a single report:

1. **Structured Data Output**: The script generates a `competency_data.json` file containing detailed competency assessments for each speaker, including:
   - Competency ratings (0-10 scale)
   - Specific observations from the transcript
   - Areas for improvement
   - Overall assessment

2. **Radar Graph Visualizations**: When the `--visualize` flag is used, the script generates interactive radar charts for each speaker, saved as HTML files:
   - Each chart displays competency ratings across all assessed dimensions.
   - Charts are labeled with the corresponding speaker tag (e.g., SPEAKER_00, SPEAKER_01).
   - The radar charts provide an intuitive visual representation of competency strengths and areas for development.

3. **Integrated Analysis**: The script generates a `combined_report.html` file containing:
   - Narrative competency insights for each speaker
   - Radar chart visualizations of competency ratings
   - Overall assessment of competencies 

4. **Multi-Speaker Support**: The combined mode fully supports multi-speaker analysis:
   - Automatically performs diarization to identify different speakers
   - Generates separate narrative insights and radar charts for each identified speaker
   - Allows for easy comparison of competencies across different speakers in the same recording

5. **Consistent Speaker Labeling**: Ensures that speaker labels are consistent between the narrative and visual parts of the report

To use the new combined output mode:
```bash
python src/main_combined.py
```

This will generate:
- `combined_report.html`: A single HTML file containing narrative insights and radar charts for all speakers

## Example Files

This repository includes example files for testing:

- `test.mp3`: A short sample audio file of a student reflecting on their experience in general.
- `test.txt`: A sample competencies file
- `test_report.html`: An example of the HTML report generated from the test audio file
- `longer_test.mp3`: A longer sample audio file for more comprehensive testing.
- `longer_test_report.html`: An example of a longer HTML report generated from the longer test audio file.
- `multi-speaker-discussion.mp3`: A sample file for testing diarization (speaker identification) and large file handling.

To run the script with these example files:

1. Make sure you're in the project directory and your virtual environment is activated.
2. Run the script in your desired mode:
   ```bash
   python src/main.py [--diarize]
   ```
   Or in data mode:
   ```bash
   python src/main_data.py [--diarize] [--visualize]
   ```
   Or in combined mode:
   ```bash
   python src/main_combined.py
   ```
3. When prompted, enter:
   - For the audio file: `test.mp3`, `longer_test.mp3`, or `multi-speaker-discussion.mp3` (or any other sound file you prefer)
   - For the competencies file: `test.txt` (or any other text file with competencies and their definitions) 
   - For the sound file: `sound.mp3` (or any other sound file you prefer)

This will process the example audio file using the example competencies and generate the appropriate output files.

## Handling Large Audio Files

The script automatically handles large audio files by splitting them into smaller chunks before processing. This allows for processing of files that would otherwise exceed the API's content size limit. The process is transparent to the user and doesn't require any additional steps.

## Multi-Speaker Support and Diarization

The Competency Extractor supports multi-speaker analysis through diarization. When you run the script with diarization enabled (default for main_combined.py), it will:

1. Identify different speakers in the audio recording.
2. Transcribe the audio with speaker labels.
3. Analyze competencies for each identified speaker separately.
4. Generate output that includes speaker-specific insights and an overall analysis.

## Notes and Recommendations

- Change the system prompt in main.py, main_data.py, or main_combined.py to suit different needs.  

- Try different ways of querying the competencies text file with respect to the transcript.

- You can change LLMs by editing config.py. As of 08/2024, Claude 3.5 Sonnet is recommended:

  ```
  anthropic/claude-3.5-sonnet
  ``` 

  or Cohere's Command R+: 
  ```
  cohere/command-r-plus-08-2024
  ```

OpenRouter provides access to all frontier models, closed and open-source, as well as smaller more specialized models.

Let's break it, and then make it better!

## Future Improvements Parking Lot

- Add support for batch processing of multiple audio files.
- Develop a user-friendly GUI for easier interaction with the tool.
- Improve diarization accuracy and integration with the transcript.
- Optimize the handling of large audio files for better performance.
- Enhance visualization options for competency data.
- Implement comparative analysis features for multi-speaker recordings.
- Explore ways to customize the combined report format and layout.

Other ideas? Feel free to contribute or suggest improvements!