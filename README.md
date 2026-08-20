![Netflix2Anki](https://raw.githubusercontent.com/jgafron/Netflix2Anki/main/images/Netflix2Anki.png)
# AI Language Mining Assistant

> An AI-powered desktop application that turns screenshots into editable Anki flashcards using OCR, computer vision, OpenAI, and Anki integration.

## Overview

Learning a language often means finding a useful sentence, translating it, and manually building a flashcard out of it, a repetitive workflow that breaks your focus every time. This app collapses that whole process into one tool by combining OCR, computer vision, AI-powered translation, and Anki automation.

Users can capture text straight from a screenshot, an uploaded image, or the clipboard. The app extracts and cleans up the text with OpenCV and Tesseract OCR, sends it to OpenAI for translation and a word-by-word breakdown, then builds a complete Anki flashcard, optional recorded audio included, in one click.

## Features

- OCR from screenshots, clipboard, or uploaded images
- OpenCV image preprocessing for better OCR accuracy
- AI-powered translation and word-by-word breakdowns
- One-click flashcard creation through AnkiConnect
- Individual vocabulary card generation
- Optional system audio recording for pronunciation
- Supports 200+ OCR languages and writing systems
- Built-in multilingual virtual keyboard for manual OCR corrections
- Persistent user settings and customizable AI prompts

## Workflow

Screenshot / Clipboard / Image
│
▼
OpenCV Processing
│
▼
Tesseract OCR
│
▼
OpenAI Translation
│
▼
Review & Edit Results
│
▼
Optional Audio
│
▼
One-Click Anki Cards


## Getting Started

### Prerequisites

Before running the application, install:

- Python 3.10+
- Tesseract OCR
- Anki Desktop
- The free **AnkiConnect** add-on
- An OpenAI API key

### OpenAI Setup

The app requires your own OpenAI API key, which you can get from the OpenAI Platform.

Once you have one, either:

- Launch the app, open **Settings**, and paste your API key into the **API Key** field, or
- Edit `settings.ini` manually and enter it there

The repository intentionally doesn't include an API key.

### Anki Setup

This app talks to Anki through the free **AnkiConnect** add-on.

1. Install Anki Desktop.
2. Install the AnkiConnect add-on.
3. Launch Anki before using the application.

Without AnkiConnect running, flashcards can't be created automatically.

### Audio Recording

Audio recording is currently configured for my local Windows playback device. Depending on your system, you may need to update the recording device in the source code to match your default audio output before recording system audio.

### OCR Languages

The app supports over 200 OCR languages and writing systems through Tesseract. Just pick your language in the Settings window before extracting text.

A built-in multilingual virtual keyboard is also available for manually correcting OCR results when needed.

## Architecture

**Desktop Application**
Tkinter, multi-window interface, built-in snipping tool, virtual keyboard, persistent settings

**OCR Pipeline**
OpenCV preprocessing, Tesseract OCR, language-aware OCR selection

**AI Processing**
OpenAI Chat Completions, configurable prompts, translation, word-by-word linguistic analysis

**Flashcard Integration**
AnkiConnect API, deck selection, audio attachment, live preview

## Technology Stack

**Language**
Python

**Desktop UI**
Tkinter

**Computer Vision**
OpenCV, Pillow

**OCR**
Tesseract OCR

**AI**
OpenAI API

**Audio**
soundcard, soundfile, NumPy

**Automation**
AnkiConnect, keyboard

## Technical Highlights

- Built a complete desktop workflow from screen capture to AI-generated flashcards
- Improved OCR accuracy with an OpenCV preprocessing pipeline
- Integrated OpenAI for structured translation and linguistic analysis
- Automated flashcard generation through AnkiConnect
- Supported over 200 OCR languages and writing systems
- Included optional system audio recording for pronunciation cards
- Implemented global hotkeys and an integrated snipping tool
- Built a configurable multi-window desktop application with persistent settings

## Running Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the application:

```bash
python main.py
```

## Future Improvements

- Local LLM support
- Batch OCR processing
- Automatic subtitle detection
- Speech-to-text integration
- Cross-platform builds
- Configurable audio device selection

## License

This repository is provided for educational and portfolio purposes.
