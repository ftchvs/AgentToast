"""Utility functions for handling agent outputs (saving files, playing audio)."""

import os
from datetime import datetime
import logging
import subprocess
import sys

# Import necessary libraries for PDF generation
import markdown
from weasyprint import HTML, CSS
from weasyprint.logger import LOGGER as WEASYPRINT_LOGGER

logger = logging.getLogger(__name__)

# Optional: Reduce WeasyPrint logging noise
WEASYPRINT_LOGGER.setLevel(logging.ERROR)

def _generate_filename(base_name: str, category: str, extension: str) -> str:
    """Generates a timestamped filename."""
    timestamp = int(datetime.now().timestamp())
    safe_category = category.replace(" ", "_").replace("/", "_") # Make category safe for filename
    return f"{base_name}_{safe_category}_{timestamp}.{extension}"

def save_pdf_report(markdown_content: str, output_dir: str, category: str) -> str:
    """
    Saves the given markdown content as a PDF file in the specified directory.

    Args:
        markdown_content: The markdown string to save.
        output_dir: The directory to save the file in.
        category: The news category (used for filename).

    Returns:
        The full path to the saved PDF file.
        
    Raises:
        Exception: If PDF generation fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = _generate_filename("news_report", category, "pdf")
    file_path = os.path.join(output_dir, filename)

    try:
        logger.info(f"Converting Markdown to HTML for PDF generation...")
        # Add extensions for better markdown compatibility (optional)
        # e.g., tables, fenced_code
        html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # Basic CSS for better formatting (optional)
        # You can expand this or load from an external file
        css = CSS(string='''
            @page { size: A4; margin: 2cm; }
            body { font-family: sans-serif; line-height: 1.5; }
            h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; line-height: 1.2; }
            h1 { font-size: 2em; }
            h2 { font-size: 1.6em; }
            h3 { font-size: 1.3em; }
            p { margin-bottom: 1em; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; overflow: auto; }
            code { font-family: monospace; }
        ''')

        logger.info(f"Generating PDF report at: {file_path}")
        HTML(string=html_content).write_pdf(file_path, stylesheets=[css])
        logger.info(f"Successfully generated PDF report.")
        return file_path
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise # Re-raise the exception so the caller knows it failed

# --- Placeholder Functions ---

def save_analysis_report(analysis_content: str, output_dir: str, category: str) -> str:
    """Placeholder for saving analysis report."""
    logger.warning("save_analysis_report is not fully implemented.")
    # Basic implementation: save as text file
    os.makedirs(output_dir, exist_ok=True)
    filename = _generate_filename("analysis_report", category, "txt")
    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, "w") as f:
            f.write(analysis_content)
        return file_path
    except Exception as e:
        logger.error(f"Failed to save basic analysis report: {e}")
        raise

def save_full_report(result_object: Any, output_dir: str, category: str) -> str:
    """Placeholder for saving a comprehensive report."""
    logger.warning("save_full_report is not fully implemented.")
     # Basic implementation: save relevant parts as JSON or text
    os.makedirs(output_dir, exist_ok=True)
    filename = _generate_filename("full_report_summary", category, "txt")
    file_path = os.path.join(output_dir, filename)
    try:
        report_str = f"Full Report Summary for Category: {category}\n\n"
        # Add more details from the result_object if it's a known type (e.g., CoordinatorOutput)
        if hasattr(result_object, 'news_summary'): report_str += f"Summary:\n{result_object.news_summary}\n\n"
        if hasattr(result_object, 'analysis'): report_str += f"Analysis:\n{result_object.analysis}\n\n"
        if hasattr(result_object, 'fact_check'): report_str += f"Fact Check:\n{result_object.fact_check}\n\n"
        if hasattr(result_object, 'trends'): report_str += f"Trends:\n{result_object.trends}\n\n"
        if hasattr(result_object, 'financial_data'): report_str += f"Financial Data:\n{json.dumps(result_object.financial_data, indent=2)}\n\n"
        if hasattr(result_object, 'agent_results'):
            report_str += "Agent Results:\n"
            for res in result_object.agent_results:
                 status = "Success" if res.success else f"Failed: {res.error}"
                 report_str += f"  - {res.agent_name}: {status}\n"
        
        with open(file_path, "w") as f:
            f.write(report_str)
        return file_path
    except Exception as e:
        logger.error(f"Failed to save basic full report: {e}")
        raise


def get_playback_command(audio_file_path: str) -> List[str]:
    """Determines the appropriate command to play an audio file based on the OS."""
    system = sys.platform
    if system == "darwin":  # macOS
        return ["afplay", audio_file_path]
    elif system == "linux":
        # Check for common Linux players
        if subprocess.call(["which", "mpg123"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return ["mpg123", "-q", audio_file_path] # -q for quiet
        elif subprocess.call(["which", "play"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            # play is part of SoX
             return ["play", audio_file_path]
        else:
            raise OSError("Could not find a suitable audio player (mpg123 or play). Please install one.")
    elif system == "win32": # Windows
         # Default Windows media player usually handles .mp3
         # Using 'start' command to open with default application
        return ["cmd", "/c", "start", "", audio_file_path]
    else:
        raise OSError(f"Unsupported operating system for audio playback: {system}")

def play_audio_file(audio_file_path: str):
    """Plays the specified audio file using the default system player."""
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
    try:
        command = get_playback_command(audio_file_path)
        logger.info(f"Executing playback command: {' '.join(command)}")
        # Use Popen for non-blocking playback if needed, run for simplicity here
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        # Optional: Wait for completion or handle errors
        # stdout, stderr = process.communicate()
        # if process.returncode != 0:
        #     logger.error(f"Audio playback failed: {stderr.decode()}")
        
    except OSError as e:
         logger.error(f"Could not play audio: {e}")
         raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during audio playback: {e}")
        raise 