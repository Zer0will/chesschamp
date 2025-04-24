import pygame
import sys
import chess
import chess.engine # Added for engine communication
import os # Added for path joining
import time # Import time for potential simple delays, though pygame.time is better for non-blocking
import argparse # Import for command line argument parsing

# Parse command line arguments
def parse_arguments():
    """Parse command line arguments for difficulty level and player color."""
    parser = argparse.ArgumentParser(description='Chess Game vs AI')
    parser.add_argument('--skill', type=int, default=0, choices=range(5),
                      help='Skill level (0-4): 0=Beginner, 1=Easy, 2=Intermediate, 3=Hard, 4=Impossible')
    parser.add_argument('--color', type=int, default=0, choices=[0, 1],
                      help='Player color: 0=White, 1=Black')
    return parser.parse_args()

# !!! IMPORTANT: SET THE PATH TO YOUR STOCKFISH EXECUTABLE !!!
# Download Stockfish from https://stockfishchess.org/download/
# Example for Windows: "C:/Users/YourUser/Downloads/stockfish/stockfish.exe"
# Example for Linux/macOS: "/usr/games/stockfish" or "/path/to/stockfish"

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set paths relative to the script location
STOCKFISH_PATH = os.path.join(SCRIPT_DIR, "stockfish", "stockfish-windows-x86-64-avx2.exe")
# Fallback to the absolute path if the relative one doesn't exist
if not os.path.exists(STOCKFISH_PATH):
    STOCKFISH_PATH = "C:/Users/talic/Downloads/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"

# --- Constants ---
# Game States
MENU = 0
PLAYING = 1
# Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700 # Keep height for buttons
SCREEN_TITLE = "Chess Game"
# Board
BOARD_SIZE = 8
SQUARE_SIZE = 60
BOARD_WIDTH = BOARD_HEIGHT = BOARD_SIZE * SQUARE_SIZE
BOARD_X = (SCREEN_WIDTH - BOARD_WIDTH) // 2
BOARD_Y = (SCREEN_HEIGHT - BOARD_HEIGHT - 80) // 2 + 40
# Colors
WHITE_COL = (255, 255, 255)
BLACK_COL = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (100, 255, 100, 150)
TEXT_COLOR = (30, 30, 30)
INFO_TEXT_COLOR = (200, 0, 0)
BUTTON_BG_COLOR = (220, 220, 220)
BUTTON_HOVER_COLOR = (200, 200, 200)
BUTTON_TEXT_COLOR = (0, 0, 0)
BUTTON_SELECTED_COLOR = (170, 220, 170) # Greenish tint for selected buttons
GAME_OVER_BG_COLOR = (50, 50, 50, 200)
GAME_OVER_TEXT_COLOR = (255, 255, 255)
# Assets Path
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
PIECE_DIR = os.path.join(ASSETS_DIR, "pieces")
# Game Settings (Defaults - will be set by menu)
AI_THINK_TIME = 0.5
AI_MOVE_DELAY = 500

# --- Pygame and Font Initialization ---
pygame.init()
pygame.font.init()

# Font Loading
try:
    STATUS_FONT = pygame.font.SysFont("Arial", 24)
    INFO_FONT = pygame.font.SysFont("Arial", 28, bold=True)
    BUTTON_FONT = pygame.font.SysFont("Arial", 20)
    GAME_OVER_FONT = pygame.font.SysFont("Arial", 36, bold=True)
    MENU_TITLE_FONT = pygame.font.SysFont("Arial", 40, bold=True)
    MENU_OPTION_FONT = pygame.font.SysFont("Arial", 28)
except Exception as e:
    print(f"Warning: Could not load default system font (Arial). Using Pygame default. Error: {e}")
    # Fallback fonts
    STATUS_FONT = pygame.font.Font(None, 30)
    INFO_FONT = pygame.font.Font(None, 36)
    BUTTON_FONT = pygame.font.Font(None, 28)
    GAME_OVER_FONT = pygame.font.Font(None, 48)
    MENU_TITLE_FONT = pygame.font.Font(None, 50)
    MENU_OPTION_FONT = pygame.font.Font(None, 36)

# --- Button Class ---
class Button:
    def __init__(self, rect, text, font, text_color, bg_color, hover_color=None, selected_color=None, action=None, value=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_color = hover_color or bg_color
        self.selected_color = selected_color or bg_color # Color when selected
        self.action = action
        self.value = value # Optional value associated with the button (e.g., skill level)
        self.is_hovered = False
        self.is_active = True
        self.is_selected = False # New state for menu buttons

    def draw(self, surface):
        current_bg = self.bg_color
        if self.is_selected:
            current_bg = self.selected_color
        elif self.is_hovered and self.is_active:
            current_bg = self.hover_color

        # Draw inactive buttons differently (optional)
        if not self.is_active:
             # Example: draw slightly transparent
             temp_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
             temp_surf.fill((*current_bg, 150)) # Use alpha for transparency
             surface.blit(temp_surf, self.rect.topleft)
             pygame.draw.rect(surface, (100,100,100), self.rect, 1, border_radius=5) # Grey border
        else:
             pygame.draw.rect(surface, current_bg, self.rect, border_radius=5)


        text_surf = self.font.render(self.text, True, self.text_color if self.is_active else (150, 150, 150)) # Grey out text if inactive
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def handle_click(self, mouse_pos):
        if self.is_active and self.rect.collidepoint(mouse_pos):
            print(f"Button '{self.text}' clicked!") # Keep debug print
            if self.action:
                print(f"---> Calling action: {self.action.__name__}")
                if self.value is not None:
                     self.action(self.value) # Pass value if action needs it
                else:
                     self.action()
            return True # Click was handled (action may or may not have run)
        return False

# --- Global Game State Variables ---
# These will be set by the menu before starting the game loop
chosen_skill_level = 0 # Default
player_color = chess.WHITE # Default
engine = None
board = chess.Board()
selected_square = None
current_turn = chess.WHITE
ai_move_trigger_time = None
status_text = ""
info_text = ""
game_over = False
game_result_message = None
game_state = MENU # Start in the menu state

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)

# --- Asset Loading ---
def load_piece_images(size):
    """Loads and scales piece images from the assets directory."""
    pieces = {}
    piece_symbols = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
    
    # Check if piece directory exists
    if not os.path.exists(PIECE_DIR):
        print(f"ERROR: Piece directory not found: {PIECE_DIR}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {SCRIPT_DIR}")
        # Try to list available directories to help debugging
        try:
            parent_dir = os.path.dirname(PIECE_DIR)
            if os.path.exists(parent_dir):
                print(f"Contents of parent directory ({parent_dir}):")
                for item in os.listdir(parent_dir):
                    print(f"  - {item}")
        except Exception as e:
            print(f"Error listing parent directory: {e}")
    
    for symbol in piece_symbols:
        try:
            # Full path to piece image
            path = os.path.join(PIECE_DIR, f"{symbol}.png")
            
            # Check if the file exists before trying to load it
            if not os.path.exists(path):
                print(f"ERROR: Piece image not found: {path}")
                pieces[symbol] = None
                continue
                
            # Load and scale the image
            image = pygame.image.load(path).convert_alpha() # Load with transparency
            image = pygame.transform.smoothscale(image, (size, size))
            pieces[symbol] = image
            print(f"Successfully loaded image: {path}")
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading image {path}: {e}. Ensure it exists and is valid.")
            pieces[symbol] = None
        except Exception as e:
            print(f"Unexpected error loading {symbol} piece: {e}")
            pieces[symbol] = None
    
    # Check if all pieces were loaded
    missing_pieces = [symbol for symbol, img in pieces.items() if img is None]
    if missing_pieces:
        print(f"\n--- WARNING: Could not load {len(missing_pieces)} piece images ---")
        print(f"Missing pieces: {', '.join(missing_pieces)}")
        print(f"Piece directory: {PIECE_DIR}")
    else:
        print("All piece images loaded successfully!")
        
    return pieces

PIECE_IMAGES = load_piece_images(SQUARE_SIZE)


# --- Game Logic Functions ---
def determine_game_outcome():
    """Determines the game result string if the game has ended naturally."""
    if board.is_game_over():
        outcome = board.outcome()
        if outcome:
            winner_color = "White" if outcome.winner == chess.WHITE else "Black" if outcome.winner == chess.BLACK else None
            termination = str(outcome.termination).split('.')[1].replace('_', ' ').title()
            if winner_color:
                # Use more standard phrasing
                reason = "Checkmate" if termination == "Checkmate" else f"on time?" # Placeholder, outcome doesn't give resignation
                return f"{termination}! {winner_color} Wins" 
            else: # Draw
                return f"{termination}! Draw"
        else:
             # Should not happen if is_game_over is true, but cover it
             return "Game Over: Unknown Reason"
    return None # Game not over

def initialize_engine(skill_level):
    """Initializes or re-initializes the chess engine with a specific skill level."""
    global engine
    if engine: # Shutdown existing engine first if any
        try:
            engine.quit()
        except Exception as e:
            print(f"Minor error quitting previous engine instance: {e}")
        engine = None

    try:
        print(f"Initializing engine with Skill Level {skill_level}...")
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        engine.configure({"Skill Level": skill_level})
        print(f"Stockfish engine initialized successfully.")
        return True
    except (FileNotFoundError, OSError, chess.engine.EngineError) as e:
        print(f"\n--- Engine Error/Configuration Error: {e} ---")
        print("Game may continue without AI or with default settings.")
        engine = None # Ensure engine is None if init failed
        return False

def reset_game(start_engine_if_needed=True):
    """Resets the game state. Optionally initializes engine based on global settings."""
    global board, selected_square, current_turn, ai_move_trigger_time, info_text, game_over, game_result_message, engine
    print("DEBUG: reset_game() called")

    # Initialize engine ONLY if start_engine_if_needed is True
    if start_engine_if_needed and not engine:
         initialize_engine(chosen_skill_level)

    print("Resetting board state...")
    board = chess.Board()
    selected_square = None
    current_turn = chess.WHITE
    ai_move_trigger_time = None
    info_text = ""
    game_over = False
    game_result_message = None
    update_ui_text()

    # Trigger initial AI move AFTER resetting state if player is Black
    if player_color == chess.BLACK and not game_over and engine:
         ai_move_trigger_time = pygame.time.get_ticks() + 100 # Small extra delay after reset
         print("New Game: Player is Black. AI (White) making first move...")

def resign_game():
    """Handles player resignation."""
    print("DEBUG: resign_game() called") # DEBUG PRINT
    global game_over, info_text, game_result_message
    if not game_over:
        print("Player resigns.")
        game_over = True
        winner = "Black" if player_color == chess.WHITE else "White"
        game_result_message = f"{winner} Wins by Resignation" # Set the main result message
        info_text = "" # Clear any secondary info text like "Check!"
        update_ui_text() # Update turn display (won't change info_text)

def get_square_from_mouse(pos):
    """Converts mouse coordinates to a chess square index, considering board orientation."""
    x, y = pos
    # Check if the click is within the board boundaries
    if not (BOARD_X <= x < BOARD_X + BOARD_WIDTH and BOARD_Y <= y < BOARD_Y + BOARD_HEIGHT):
        return None # Click was outside the board
    
    # Calculate the row and column index based on screen coordinates (0-7 from top-left)
    screen_col = (x - BOARD_X) // SQUARE_SIZE
    screen_row = (y - BOARD_Y) // SQUARE_SIZE
    
    # Convert screen coordinates to logical chess file (0-7, a-h) and rank (0-7, 1-8)
    if player_color == chess.WHITE:
        # For white, screen col directly maps to file
        file = screen_col 
        # Screen row 0 is rank 7, screen row 7 is rank 0
        rank = BOARD_SIZE - 1 - screen_row 
    else: # Player is Black, board is flipped visually
        # Screen col 0 (left) is h-file (7), screen col 7 (right) is a-file (0)
        file = BOARD_SIZE - 1 - screen_col
        # Screen row 0 (top) is rank 0 (1st rank), screen row 7 (bottom) is rank 7 (8th rank)
        rank = screen_row 
        
    # Convert logical file and rank to the single square index (0-63)
    square_index = chess.square(file, rank)
    return square_index

def update_ui_text():
    """Updates the status_text and info_text based on the game state."""
    global status_text, info_text
    
    # Always set the current turn text
    turn_color_name = "White" if board.turn == chess.WHITE else "Black"
    status_text = f"{turn_color_name}'s Turn"
    
    # Only display "Check!" if game is NOT over
    if not game_over and board.is_check():
        info_text = "Check!"
    else:
        # Clear info text if game is over or not in check
        info_text = ""

# --- Drawing Functions ---
def draw_board(surface):
    """Draws the chessboard squares, considering board orientation."""
    for screen_row in range(BOARD_SIZE):
        for screen_col in range(BOARD_SIZE):
            # Determine logical rank/file for this screen position
            if player_color == chess.WHITE:
                logical_rank = BOARD_SIZE - 1 - screen_row
                logical_file = screen_col
            else: # Player is Black
                logical_rank = screen_row 
                logical_file = BOARD_SIZE - 1 - screen_col
            
            # Determine color based on logical rank/file
            is_light = (logical_rank + logical_file) % 2 == 0
            color = LIGHT_SQUARE if is_light else DARK_SQUARE
            
            # Calculate screen position (top-left corner of square)
            screen_x = BOARD_X + screen_col * SQUARE_SIZE
            screen_y = BOARD_Y + screen_row * SQUARE_SIZE
            
            rect = pygame.Rect(screen_x, screen_y, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(surface, color, rect)
            
def draw_pieces(surface, current_board, images):
    """Draws the pieces on the board based on the chess.Board state."""
    if not images: # Don't try drawing if images didn't load
        return
        
    for square_index in range(64):
        piece = current_board.piece_at(square_index)
        if piece:
            color = 'w' if piece.color == chess.WHITE else 'b'
            piece_type = piece.symbol().upper()
            symbol = f"{color}{piece_type}"
            piece_image = images.get(symbol)

            if piece_image: 
                file = chess.square_file(square_index)
                rank = chess.square_rank(square_index)
                if player_color == chess.WHITE:
                    screen_x = BOARD_X + file * SQUARE_SIZE
                    screen_y = BOARD_Y + (BOARD_SIZE - 1 - rank) * SQUARE_SIZE
                else:
                    screen_x = BOARD_X + (BOARD_SIZE - 1 - file) * SQUARE_SIZE
                    screen_y = BOARD_Y + rank * SQUARE_SIZE
                img_rect = piece_image.get_rect(center=(screen_x + SQUARE_SIZE // 2, screen_y + SQUARE_SIZE // 2))
                surface.blit(piece_image, img_rect.topleft)
            else:
                pass 

def draw_selection(surface, sq_index):
    """Draws a highlight overlay on the selected square."""
    if sq_index is not None:
        # Convert square index back to row/col for drawing
        file = chess.square_file(sq_index)
        rank = chess.square_rank(sq_index)
        # Remember to flip rank for Pygame's coordinate system
        if player_color == chess.WHITE:
            screen_x = BOARD_X + file * SQUARE_SIZE
            screen_y = BOARD_Y + (BOARD_SIZE - 1 - rank) * SQUARE_SIZE
        else:
            screen_x = BOARD_X + (BOARD_SIZE - 1 - file) * SQUARE_SIZE
            screen_y = BOARD_Y + rank * SQUARE_SIZE
        
        # Create a semi-transparent surface for the highlight
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA) # SRCALPHA allows transparency
        highlight_surface.fill(HIGHLIGHT_COLOR)
        surface.blit(highlight_surface, (screen_x, screen_y))

def draw_ui_text(surface):
    """Draws the turn status and info text."""
    # Draw the main turn status
    status_surf = STATUS_FONT.render(status_text, True, TEXT_COLOR)
    status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, BOARD_Y - 45))
    surface.blit(status_surf, status_rect)
    if info_text:
        info_surf = INFO_FONT.render(info_text, True, INFO_TEXT_COLOR)
        info_rect = info_surf.get_rect(center=(SCREEN_WIDTH // 2, BOARD_Y - 15))
        surface.blit(info_surf, info_rect)

def draw_buttons(surface, button_list): # Pass the list of buttons to draw
    """Draws all buttons in the provided list."""
    for button in button_list:
        button.draw(surface)

def draw_game_over_overlay(surface):
    """Draws the centered game over message if the game has ended."""
    if game_over and game_result_message:
        # Make the background overlay slightly smaller than the board
        overlay_margin = 10
        overlay_rect = pygame.Rect(
            BOARD_X + overlay_margin,
            BOARD_Y + BOARD_HEIGHT // 2 - 40, # Center vertically a bit better
            BOARD_WIDTH - 2 * overlay_margin,
            80 # Fixed height for the overlay box
        )
        overlay_surface = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
        overlay_surface.fill(GAME_OVER_BG_COLOR)
        surface.blit(overlay_surface, overlay_rect.topleft)

        # Render and draw the centered text within the overlay rect
        text_surf = GAME_OVER_FONT.render(game_result_message, True, GAME_OVER_TEXT_COLOR)
        # Center the text within the overlay rectangle
        text_rect = text_surf.get_rect(center=overlay_rect.center) 
        surface.blit(text_surf, text_rect)

# --- AI Move Function ---
def make_ai_move():
    """Calculates and performs the AI's move. Now non-blocking for delay."""
    global current_turn, board, game_over, ai_move_trigger_time, game_result_message
    if engine and board.turn != player_color and not game_over:
        print(f"AI ({'White' if board.turn == chess.WHITE else 'Black'}) is thinking...")
        try:
            # Use the constant for think time
            result = engine.play(board, chess.engine.Limit(time=AI_THINK_TIME))
            if result.move:
                print(f"AI moves: {result.move.uci()}")
                board.push(result.move)
                current_turn = player_color # Switch back to player's turn
                game_over = board.is_game_over() # Check game over state *after* move
                if game_over:
                    game_result_message = determine_game_outcome()
                update_ui_text() # Update both status and info text
            else:
                # Engine might not find a move if it's already mate/stalemate
                print("AI could not find a move.")
                game_over = board.is_game_over()
                if game_over:
                    game_result_message = determine_game_outcome()
                update_ui_text()
                if not game_over: # Should ideally not happen unless engine error
                   print("Warning: AI failed to move, but game is not over.")
                   current_turn = player_color # Give control back?
        except chess.engine.EngineError as e:
            print(f"Engine error during AI move: {e}")
            # Consider switching turn back or stopping the game on engine error
            current_turn = player_color 
            update_ui_text()
        except Exception as e:
            print(f"Unexpected error during AI move: {e}")
            current_turn = player_color
            update_ui_text()
        finally:
             ai_move_trigger_time = None # Ensure timer is reset even if AI fails

# --- Menu Function ---
def run_menu():
    """Displays the pre-game menu and handles selections."""
    global game_state, chosen_skill_level, player_color

    menu_selected_difficulty = None
    menu_selected_color = None
    menu_clock = pygame.time.Clock()
    menu_running = True

    # --- Menu Actions ---
    def set_difficulty(level):
        nonlocal menu_selected_difficulty
        menu_selected_difficulty = level
        print(f"Menu: Difficulty set to {level}")
        # Update button selection state
        for btn in difficulty_buttons:
            btn.is_selected = (btn.value == level)

    def set_color(color):
        nonlocal menu_selected_color
        menu_selected_color = color
        print(f"Menu: Color set to {'White' if color == chess.WHITE else 'Black'}")
        # Update button selection state
        for btn in color_buttons:
            btn.is_selected = (btn.value == color)

    def start_game_action():
        nonlocal menu_running
        global chosen_skill_level, player_color, game_state
        if menu_selected_difficulty is not None and menu_selected_color is not None:
            chosen_skill_level = menu_selected_difficulty
            player_color = menu_selected_color
            print("-" * 20)
            print(f"Starting Game: Skill={chosen_skill_level}, Player Color={'White' if player_color == chess.WHITE else 'Black'}")
            print("-" * 20)
            game_state = PLAYING # Change game state
            menu_running = False # Exit menu loop
        else:
             print("Menu: Please select difficulty and color first.")


    # --- Create Menu Buttons ---
    # Difficulty Labels and Levels (0-4)
    difficulty_labels = ["Beginner", "Easy", "Intermediate", "Hard", "Impossible"]
    difficulty_levels = list(range(len(difficulty_labels))) # Corresponds to 0, 1, 2, 3, 4
    
    difficulty_buttons = []
    btn_width_diff = 140 # Increased width for longer text
    btn_height = 40
    num_buttons = len(difficulty_labels)
    button_spacing_diff = 15
    total_width_diff = (num_buttons * btn_width_diff + (num_buttons - 1) * button_spacing_diff)
    start_x_diff = (SCREEN_WIDTH - total_width_diff) // 2 
    y_pos_diff = 200
    
    for i, label in enumerate(difficulty_labels):
        level = difficulty_levels[i]
        btn = Button(
            rect=(start_x_diff + i * (btn_width_diff + button_spacing_diff), y_pos_diff, btn_width_diff, btn_height),
            text=label, # Use the descriptive label
            font=BUTTON_FONT,
            text_color=BUTTON_TEXT_COLOR,
            bg_color=BUTTON_BG_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            selected_color=BUTTON_SELECTED_COLOR,
            action=set_difficulty,
            value=level # Store the actual skill level (0-4) as the value
        )
        difficulty_buttons.append(btn)

    # Color Buttons
    color_buttons = []
    btn_width_col = 150
    total_width_col = (2 * btn_width_col + 30)
    start_x_col = (SCREEN_WIDTH - total_width_col) // 2
    y_pos_col = 350

    white_btn = Button(
         rect=(start_x_col, y_pos_col, btn_width_col, btn_height),
         text="Play as White", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
         bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR, selected_color=BUTTON_SELECTED_COLOR,
         action=set_color, value=chess.WHITE
    )
    black_btn = Button(
         rect=(start_x_col + btn_width_col + 30, y_pos_col, btn_width_col, btn_height),
         text="Play as Black", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
         bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR, selected_color=BUTTON_SELECTED_COLOR,
         action=set_color, value=chess.BLACK
    )
    color_buttons.extend([white_btn, black_btn])

    # Start Button
    start_btn = Button(
        rect=(SCREEN_WIDTH // 2 - 100, 500, 200, 50),
        text="Start Game", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
        bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
        action=start_game_action
    )
    start_btn.is_active = False # Start disabled

    all_menu_buttons = difficulty_buttons + color_buttons + [start_btn]

    # --- Menu Loop ---
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()
        menu_clock.tick(60)

        # Check hover states
        for button in all_menu_buttons:
            button.check_hover(mouse_pos)

        # Enable Start button only if both options selected
        start_btn.is_active = (menu_selected_difficulty is not None and menu_selected_color is not None)

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit() # Quit pygame fully if closing from menu
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click_pos = event.pos
                    for button in all_menu_buttons:
                        # Make copies of button lists to avoid modifying during iteration if needed
                        if button.handle_click(click_pos):
                            # Potentially update selection states here too if action doesn't
                            break # Assume only one button click per event

        # Drawing
        screen.fill(WHITE_COL)

        # Draw Titles
        title_surf = MENU_TITLE_FONT.render("Chess Game Setup", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)

        diff_label_surf = MENU_OPTION_FONT.render("Select AI Difficulty:", True, TEXT_COLOR) # Updated Label
        diff_label_rect = diff_label_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos_diff - 40))
        screen.blit(diff_label_surf, diff_label_rect)

        col_label_surf = MENU_OPTION_FONT.render("Select Your Color:", True, TEXT_COLOR)
        col_label_rect = col_label_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos_col - 40))
        screen.blit(col_label_surf, col_label_rect)

        # Draw Buttons
        draw_buttons(screen, all_menu_buttons)

        pygame.display.flip()

# --- Main Function ---
def main():
    """Main function to run the chess game."""
    global game_state, chosen_skill_level, player_color, engine, board, selected_square, current_turn
    global ai_move_trigger_time, status_text, info_text, game_over, game_result_message
    
    # Log startup information
    print("\n--- Chess Game Starting ---")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Assets directory: {ASSETS_DIR}")
    print(f"Piece directory: {PIECE_DIR}")
    print(f"Stockfish path: {STOCKFISH_PATH}")
    print(f"Stockfish exists: {os.path.exists(STOCKFISH_PATH)}")
    print(f"Command line args: {sys.argv}")
    
    # Parse command line arguments
    try:
        args = parse_arguments()
        print(f"Parsed arguments: skill={args.skill}, color={args.color}")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        args = argparse.Namespace(skill=0, color=0)  # Default values
        print("Using default arguments")
    
    # Check if skill and color arguments were provided
    # Skip the menu if command line arguments are provided
    if '--skill' in sys.argv and '--color' in sys.argv:
        # Get the values from the parsed arguments
        chosen_skill_level = args.skill
        player_color = chess.BLACK if args.color == 1 else chess.WHITE
        game_state = PLAYING  # Skip the menu and go directly to playing
        
        print(f"Starting game with command line args: Skill={chosen_skill_level}, Color={'Black' if player_color == chess.BLACK else 'White'}")
        
        # Initialize the game with the provided settings
        engine_initialized = initialize_engine(chosen_skill_level)
        if not engine_initialized:
            print("WARNING: Failed to initialize chess engine. Game will continue without AI.")
        
        # Create game screen buttons
        button_y = BOARD_Y + BOARD_HEIGHT + 20
        button_width = 120
        button_height = 40
        button_spacing = 30
        total_button_width = (button_width * 2) + button_spacing
        start_x = (SCREEN_WIDTH - total_button_width) // 2
        new_game_button = Button(
            rect=(start_x, button_y, button_width, button_height),
            text="New Game", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
            bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
            action=reset_game # Reset keeps current settings
        )
        resign_button = Button(
            rect=(start_x + button_width + button_spacing, button_y, button_width, button_height),
            text="Resign", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
            bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
            action=resign_game
        )
        game_buttons = [new_game_button, resign_button]
        
        # Reset board state for the first game
        reset_game(start_engine_if_needed=False)  # Engine already started
        
        # Run the game loop
        running = True
        clock = pygame.time.Clock()
        
        while running:
            dt = clock.tick(60)
            
            # Get mouse position for this frame
            current_frame_mouse_pos = pygame.mouse.get_pos()
            
            # Update game button hover states
            for button in game_buttons:
                button.check_hover(current_frame_mouse_pos)
            
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        click_pos = event.pos
                        button_clicked = False
                        # Check Game Buttons
                        for button in game_buttons:
                            if button.action == resign_game:
                                button.is_active = not game_over
                            else:
                                button.is_active = True
                            
                            if button.handle_click(click_pos):
                                button_clicked = True
                                break
                        
                        # Check Board Interaction
                        if not button_clicked and current_turn == player_color and not game_over:
                            clicked_square = get_square_from_mouse(click_pos)
                            if clicked_square is not None:
                                piece = board.piece_at(clicked_square)
                                if selected_square is None:
                                    if piece is not None and piece.color == player_color:
                                        selected_square = clicked_square
                                    else: 
                                        selected_square = None
                                else: # Attempt move
                                    move = chess.Move(selected_square, clicked_square)
                                    moving_piece = board.piece_at(selected_square)
                                    if moving_piece and moving_piece.piece_type == chess.PAWN:
                                        target_rank = chess.square_rank(clicked_square)
                                        is_promotion_rank = (player_color == chess.WHITE and target_rank == 7) or \
                                                            (player_color == chess.BLACK and target_rank == 0)
                                        if is_promotion_rank:
                                            move.promotion = chess.QUEEN
                                    if move in board.legal_moves:
                                        board.push(move)
                                        print(f"Player ({'White' if player_color == chess.WHITE else 'Black'}) moves: {move.uci()}")
                                        selected_square = None
                                        current_turn = not player_color
                                        game_over = board.is_game_over()
                                        if game_over: 
                                            game_result_message = determine_game_outcome()
                                        update_ui_text()
                                        if not game_over and engine:
                                            ai_move_trigger_time = pygame.time.get_ticks()
                                            print(f"AI turn starts. Delaying {AI_MOVE_DELAY}ms...")
                                    elif clicked_square == selected_square: 
                                        selected_square = None
                                    elif piece is not None and piece.color == player_color: 
                                        selected_square = clicked_square
                                    else: 
                                        print(f"Illegal move attempt: {move.uci()}")
                            else: # Clicked outside board
                                selected_square = None
                
            # AI Move Timing
            if not game_over and current_turn != player_color and engine and ai_move_trigger_time is not None:
                current_time = pygame.time.get_ticks()
                if current_time - ai_move_trigger_time >= AI_MOVE_DELAY:
                    make_ai_move()
            
            # Drawing
            screen.fill(WHITE_COL)
            draw_board(screen)
            if selected_square is not None: 
                draw_selection(screen, selected_square)
            draw_pieces(screen, board, PIECE_IMAGES)
            draw_ui_text(screen)
            draw_buttons(screen, game_buttons) # Draw game buttons
            draw_game_over_overlay(screen)
            
            pygame.display.flip()
    
    else:
        # The original game loop with menu
        running = True
        clock = pygame.time.Clock()
        game_buttons = []  # Will be initialized after menu
        
        while running:
            dt = clock.tick(60)
            
            if game_state == MENU:
                run_menu()  # This function handles its own loop and changes game_state
                
                # --- Post-Menu Initialization (only runs once after menu exits) ---
                if game_state == PLAYING:
                    # Initialize engine with chosen level
                    initialize_engine(chosen_skill_level)
                    
                    # Create game screen buttons (only needs to happen once)
                    button_y = BOARD_Y + BOARD_HEIGHT + 20
                    button_width = 120
                    button_height = 40
                    button_spacing = 30
                    total_button_width = (button_width * 2) + button_spacing
                    start_x = (SCREEN_WIDTH - total_button_width) // 2
                    new_game_button = Button(
                        rect=(start_x, button_y, button_width, button_height),
                        text="New Game", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
                        bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
                        action=reset_game # Reset keeps current settings
                    )
                    resign_button = Button(
                        rect=(start_x + button_width + button_spacing, button_y, button_width, button_height),
                        text="Resign", font=BUTTON_FONT, text_color=BUTTON_TEXT_COLOR,
                        bg_color=BUTTON_BG_COLOR, hover_color=BUTTON_HOVER_COLOR,
                        action=resign_game
                    )
                    game_buttons = [new_game_button, resign_button]
                    
                    # Reset board state for the very first game
                    reset_game(start_engine_if_needed=False) # Engine already started
            
            elif game_state == PLAYING:
                # --- Game Loop Logic ---
                current_frame_mouse_pos = pygame.mouse.get_pos()
                
                # Update game button hover states
                for button in game_buttons:
                    button.check_hover(current_frame_mouse_pos)
                
                # Event Handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            click_pos = event.pos
                            button_clicked = False
                            # Check Game Buttons
                            for button in game_buttons:
                                if button.action == resign_game:
                                    button.is_active = not game_over
                                else:
                                    button.is_active = True
                                
                                if button.handle_click(click_pos):
                                    button_clicked = True
                                    break
                            
                            # Check Board Interaction
                            if not button_clicked and current_turn == player_color and not game_over:
                                clicked_square = get_square_from_mouse(click_pos)
                                if clicked_square is not None:
                                    piece = board.piece_at(clicked_square)
                                    if selected_square is None:
                                        if piece is not None and piece.color == player_color:
                                            selected_square = clicked_square
                                        else: selected_square = None
                                    else: # Attempt move
                                        move = chess.Move(selected_square, clicked_square)
                                        moving_piece = board.piece_at(selected_square)
                                        if moving_piece and moving_piece.piece_type == chess.PAWN:
                                            target_rank = chess.square_rank(clicked_square)
                                            is_promotion_rank = (player_color == chess.WHITE and target_rank == 7) or \
                                                                (player_color == chess.BLACK and target_rank == 0)
                                            if is_promotion_rank:
                                                move.promotion = chess.QUEEN
                                        if move in board.legal_moves:
                                            board.push(move)
                                            print(f"Player ({'White' if player_color == chess.WHITE else 'Black'}) moves: {move.uci()}")
                                            selected_square = None
                                            current_turn = not player_color
                                            game_over = board.is_game_over()
                                            if game_over: game_result_message = determine_game_outcome()
                                            update_ui_text()
                                            if not game_over and engine:
                                                ai_move_trigger_time = pygame.time.get_ticks()
                                                print(f"AI turn starts. Delaying {AI_MOVE_DELAY}ms...")
                                        elif clicked_square == selected_square: selected_square = None
                                        elif piece is not None and piece.color == player_color: selected_square = clicked_square
                                        else: print(f"Illegal move attempt: {move.uci()}")
                                else: # Clicked outside board
                                    selected_square = None
                
                # AI Move Timing
                if not game_over and current_turn != player_color and engine and ai_move_trigger_time is not None:
                    current_time = pygame.time.get_ticks()
                    if current_time - ai_move_trigger_time >= AI_MOVE_DELAY:
                        make_ai_move()
                
                # Drawing
                screen.fill(WHITE_COL)
                draw_board(screen)
                if selected_square is not None: draw_selection(screen, selected_square)
                draw_pieces(screen, board, PIECE_IMAGES)
                draw_ui_text(screen)
                draw_buttons(screen, game_buttons) # Draw game buttons
                draw_game_over_overlay(screen)
                
                pygame.display.flip()
    
    # --- Quit ---
    if engine:
        print("Shutting down chess engine...")
        engine.quit()
        print("Engine shut down.")
    pygame.font.quit()
    pygame.quit()
    sys.exit()

# Call the main function
if __name__ == '__main__':
    main() 