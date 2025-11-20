#!/usr/bin/env python3
"""
French Subtitle Overlay App for Mac

This app connects to WhisperLiveKit and displays simplified French subtitles
in a transparent overlay window that can be positioned alongside video calls.

Usage:
    python french_subtitle_app.py [--server-url ws://localhost:8000/asr]
"""

import asyncio
import tkinter as tk
from tkinter import ttk, font as tkfont
import json
import websockets
import argparse
import sys
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SubtitleOverlay:
    """Transparent overlay window for displaying subtitles."""

    def __init__(self, master):
        self.master = master
        self.master.title("French Subtitles")

        # Make window always on top and transparent
        self.master.attributes('-topmost', True)
        self.master.attributes('-alpha', 0.9)  # Semi-transparent

        # Set window size and position (bottom center of screen)
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = 800
        window_height = 200
        x_pos = (screen_width - window_width) // 2
        y_pos = screen_height - window_height - 100
        self.master.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        # Configure styling
        self.master.configure(bg='black')

        # Create main frame
        main_frame = tk.Frame(self.master, bg='black', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Connecting to server...",
            fg='yellow',
            bg='black',
            font=('Helvetica', 10)
        )
        self.status_label.pack(anchor='nw')

        # Original text label (smaller, for reference)
        self.original_label = tk.Label(
            main_frame,
            text="",
            fg='gray',
            bg='black',
            font=('Helvetica', 12),
            wraplength=760,
            justify=tk.LEFT
        )
        self.original_label.pack(fill=tk.X, pady=(10, 5))

        # Simplified subtitle label (larger, main display)
        subtitle_font = tkfont.Font(family='Helvetica', size=18, weight='bold')
        self.subtitle_label = tk.Label(
            main_frame,
            text="",
            fg='white',
            bg='black',
            font=subtitle_font,
            wraplength=760,
            justify=tk.LEFT
        )
        self.subtitle_label.pack(fill=tk.BOTH, expand=True)

        # Control frame
        control_frame = tk.Frame(main_frame, bg='black')
        control_frame.pack(fill=tk.X, pady=(10, 0))

        # Show original checkbox
        self.show_original = tk.BooleanVar(value=True)
        self.original_checkbox = tk.Checkbutton(
            control_frame,
            text="Show original",
            variable=self.show_original,
            fg='white',
            bg='black',
            selectcolor='black',
            activebackground='black',
            activeforeground='white',
            command=self.toggle_original
        )
        self.original_checkbox.pack(side=tk.LEFT)

        # Quit button
        quit_button = tk.Button(
            control_frame,
            text="Quit",
            command=self.quit_app,
            bg='darkred',
            fg='white',
            padx=10
        )
        quit_button.pack(side=tk.RIGHT)

        # Add keyboard shortcut to quit (Cmd+Q)
        self.master.bind('<Command-q>', lambda e: self.quit_app())
        self.master.bind('<Control-c>', lambda e: self.quit_app())

        # WebSocket connection
        self.ws_url = None
        self.ws_task = None
        self.running = True

    def update_status(self, status: str, color: str = 'yellow'):
        """Update the status label."""
        self.status_label.config(text=status, fg=color)

    def update_subtitles(self, original: str, simplified: str):
        """Update the subtitle display."""
        if simplified:
            self.subtitle_label.config(text=simplified)
        elif original:
            # Fallback to original if no simplified text available
            self.subtitle_label.config(text=original)

        if self.show_original.get() and original:
            self.original_label.config(text=f"Original: {original}")
        else:
            self.original_label.config(text="")

    def toggle_original(self):
        """Toggle display of original text."""
        # Will be updated on next subtitle update
        pass

    def quit_app(self):
        """Quit the application."""
        logger.info("Quitting application")
        self.running = False
        self.master.quit()

    async def connect_websocket(self, ws_url: str):
        """Connect to WhisperLiveKit WebSocket server."""
        self.ws_url = ws_url
        self.update_status(f"Connecting to {ws_url}...", 'yellow')

        retry_count = 0
        max_retries = 5

        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(ws_url) as websocket:
                    self.update_status("Connected - Listening for audio...", 'green')
                    retry_count = 0  # Reset on successful connection

                    # Send initial config (using PCM input mode)
                    config = {
                        "pcm_input": True,
                        "sample_rate": 16000,
                        "channels": 1
                    }
                    await websocket.send(json.dumps(config))

                    # Receive messages
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            data = json.loads(message)

                            # Extract subtitle text
                            original_text = ""
                            simplified_text = ""

                            # Get buffer text (most recent, uncommitted)
                            buffer_simplified = data.get('buffer_simplified', '')
                            buffer_transcription = data.get('buffer_transcription', '')

                            # Get last validated line (committed text)
                            lines = data.get('lines', [])
                            if lines:
                                last_line = lines[-1]
                                original_text = last_line.get('text', '')
                                simplified_text = last_line.get('simplified_text', '')

                            # Prefer buffer for real-time display
                            if buffer_simplified:
                                simplified_text = buffer_simplified
                            if buffer_transcription:
                                original_text = buffer_transcription

                            # Update display
                            if simplified_text or original_text:
                                self.master.after(0, self.update_subtitles, original_text, simplified_text)

                        except asyncio.TimeoutError:
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON received: {e}")
                            continue

            except Exception as e:
                retry_count += 1
                logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {e}")
                self.update_status(f"Connection error - retrying ({retry_count}/{max_retries})...", 'red')
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff

        if retry_count >= max_retries:
            self.update_status("Failed to connect after multiple attempts", 'red')


class AsyncTkinterApp:
    """Wrapper to run Tkinter with asyncio."""

    def __init__(self, ws_url: str):
        self.root = tk.Tk()
        self.overlay = SubtitleOverlay(self.root)
        self.ws_url = ws_url

    async def run(self):
        """Run the Tkinter app with asyncio."""
        # Start WebSocket connection
        ws_task = asyncio.create_task(self.overlay.connect_websocket(self.ws_url))

        # Run Tkinter event loop
        while self.overlay.running:
            try:
                self.root.update()
                await asyncio.sleep(0.01)  # Prevent blocking
            except tk.TclError:
                # Window closed
                break

        # Cleanup
        self.overlay.running = False
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="French Subtitle Overlay App for WhisperLiveKit"
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default="ws://localhost:8000/asr",
        help="WebSocket URL of WhisperLiveKit server (default: ws://localhost:8000/asr)"
    )
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()

    logger.info(f"Starting French Subtitle Overlay App")
    logger.info(f"Connecting to: {args.server_url}")
    logger.info("Press Cmd+Q or click Quit to exit")

    app = AsyncTkinterApp(args.server_url)
    await app.run()

    logger.info("Application closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
