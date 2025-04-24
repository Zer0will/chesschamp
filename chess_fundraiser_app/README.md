# Chess Fundraiser App

A web application for a chess game fundraiser that allows users to "purchase" access to play against an AI chess opponent.

## Overview

This application consists of two main components:

1. **Web Frontend (Flask)**: Handles the donation/payment process and game configuration
2. **Chess Game (Pygame)**: The actual chess game that users play after their donation

## Features

- Simple landing page with fundraiser information
- Simulated donation/payment flow (can be integrated with Stripe)
- Game settings configuration (AI difficulty, player color)
- Launches the pygame chess game with the selected settings
- Responsive UI with a clean, modern design

## Setup and Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure the Stockfish chess engine is properly set up:
   - Download Stockfish from https://stockfishchess.org/download/
   - Update the `STOCKFISH_PATH` in main.py to point to your Stockfish executable

3. Start the web server:

```bash
python chess_fundraiser_app/app.py
```

4. Open your browser and navigate to:

```
http://localhost:5000
```

## Project Structure

- `chess_fundraiser_app/` - Flask web application
  - `app.py` - Main Flask application
  - `templates/` - HTML templates
    - `index.html` - Fundraiser landing page
    - `settings.html` - Game configuration page
  - `static/` - Static assets
    - `css/` - Stylesheets
    - `js/` - JavaScript files
    - `images/` - Images and graphics
- `main.py` - Pygame chess game
- `assets/` - Game assets (chess pieces, etc.)
- `stockfish/` - Stockfish chess engine

## How It Works

1. User visits the fundraiser landing page
2. User clicks the "Unlock Chess Bots" button and completes the (simulated) payment
3. After payment, user is taken to the settings page to select difficulty and color
4. User clicks "Start Playing" to launch the chess game with the chosen settings
5. The Pygame chess application starts with the configured parameters

## Payment Integration

This application includes a simulated payment process. To implement real payments:

1. Sign up for a Stripe account
2. Update the checkout route in app.py to create a Stripe Checkout Session
3. Configure the success URL in Stripe to point to your success route

## License

This project is licensed under the MIT License - see the LICENSE file for details. 