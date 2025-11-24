# NFL Stats AI Frontend

A modern, natural language interface for querying NFL statistics, built with Next.js, Tailwind CSS, and Framer Motion.

## Features

- 🏈 **Natural Language Search**: Ask questions like "Mahomes vs Allen 2024" or "Tom Brady playoffs".
- 🎨 **Premium UI**: Dark mode aesthetic with glassmorphism and smooth animations.
- 📊 **Rich Results**: Displays stats in a clean, terminal-like interface with syntax highlighting.
- ⚡ **Real-time**: Connects to a Python FastAPI backend for live data processing.

## Getting Started

### Prerequisites

1.  **Backend**: Ensure the FastAPI backend is running.
    ```bash
    # In the project root
    python api_server.py
    ```

2.  **Frontend**: Install dependencies and run the dev server.
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

3.  Open [http://localhost:3000](http://localhost:3000) in your browser.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS v4
- **Animations**: Framer Motion
- **Fonts**: Inter & JetBrains Mono
- **Backend**: FastAPI + Rich (for formatting)

## Project Structure

- `app/`: Main application pages and layout.
- `components/`: Reusable UI components (`Header`, `SearchInput`, `ResultCard`, etc.).
- `globals.css`: Global styles and theme variables.
