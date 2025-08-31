import pygame
import sys
import numpy as np

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Chess")

WIDTH, HEIGHT           =  400, 400
screen                  =  pygame.display.set_mode((WIDTH, HEIGHT))
smol_font               =  pygame.font.Font("font/Pecita.otf", 25)
big_font                =  pygame.font.Font("font/Pecita.otf", 50)
timer                   =  pygame.time.Clock()
FPS                     =  30

tile_size               =  50
# Using numpy array for board - much faster lookups!
board                   =  np.zeros((8, 8), dtype=object)  # Will store piece names or None
pieces                  =  {'K':'♚', 'Q':'♛', 'R':'♜', 'B':'♝', 'N':'♞', 'P':'♟'}

# Initial positions
initial_black_position  =  {'P1':(0,1), 'P2':(1,1), 'P3':(2,1), 'P4':(3,1), 'P5':(4,1), 'P6':(5,1), 'P7':(6,1), 'P8':(7,1),
                           'K_':(4,0), 'Q_':(3,0), 'R1':(0,0), 'R2':(7,0), 'B1':(2,0), 'B2':(5,0), 'N1':(1,0), 'N2':(6,0)}
initial_white_position  =  {'K_':(4,7), 'Q_':(3,7), 'R1':(0,7), 'R2':(7,7), 'B1':(2,7), 'B2':(5,7), 'N1':(1,7), 'N2':(6,7),
                           'P1':(0,6), 'P2':(1,6), 'P3':(2,6), 'P4':(3,6), 'P5':(4,6), 'P6':(5,6), 'P7':(6,6), 'P8':(7,6)}
black_position          =  initial_black_position.copy()
white_position          =  initial_white_position.copy()
turn_step               =  0
valid_moves             =  []
selected_piece          =  None
game_over               =  False
winner                  =  None
captured_piece          =  None
capture_timer           =  0
game_state              =  "playing"  # "playing", "checkmate", "stalemate"
pgn_moves               =  []
move_number             =  1

def update_board_array():

    board.fill(None)
    
    for name, pos in white_position.items():
        x, y = pos
        board[x, y] = ('w', name)
    
    for name, pos in black_position.items():
        x, y = pos
        board[x, y] = ('b', name)

def play_move_sound():
    try:
        sample_rate     = 22050
        duration        = 0.15
        t               = np.linspace(0, duration, int(sample_rate * duration))
        frequency       = 120
        decay           = np.exp(-t * 15) 
        wave            = np.sin(2 * np.pi * frequency * t) * decay * 0.3
        wave           += np.sin(2 * np.pi * frequency * 2 * t) * decay * 0.1
        wave           += np.sin(2 * np.pi * frequency * 3 * t) * decay * 0.05
        audio_data      = (wave * 32767).astype(np.int16).tobytes()

        pygame.mixer.Sound(buffer=audio_data).play()
    except:
        pass

def play_capture_sound():
    try:
        sample_rate    = 22050
        duration       = 0.2
        t              = np.linspace(0, duration, int(sample_rate * duration))
        frequency      = 2000
        attack         = 1 - np.exp(-t * 50)
        decay          = np.exp(-t * 8)
        envelope       = attack * decay
        wave           = np.sin(2 * np.pi * frequency * t) * envelope * 0.2
        noise          = np.random.normal(0, 0.1, len(t)) * envelope * 0.3
        wave           += np.sin(2 * np.pi * frequency * 4 * t) * envelope * 0.1
        final_wave     = wave + noise
        audio_data     = (final_wave * 32767).astype(np.int16).tobytes()

        pygame.mixer.Sound(buffer=audio_data).play()
    except:
        pass

def reset_game():
    global black_position, white_position, turn_step, valid_moves, selected_piece
    global game_over, winner, captured_piece, capture_timer, game_state, pgn_moves, move_number
    
    black_position    = initial_black_position.copy()
    white_position    = initial_white_position.copy()
    turn_step         = 0
    valid_moves       = []
    selected_piece    = None
    game_over         = False
    winner            = None
    captured_piece    = None
    capture_timer     = 0
    game_state        = "playing"
    pgn_moves         = []
    move_number       = 1
    update_board_array()  # Initialize board array
    print("\n=== GAME RESET ===")
    print("PGN: [New Game]")

def draw_board():
    colors      =  [(142, 140, 150), (95, 90, 100)]
    pen_colours =  [(165, 162, 170), (75, 70, 80)]
    pattern     =  '▒'
    
    for x in range(8):
        for y in range(8):
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            pygame.draw.rect(screen, colors[(x + y) % 2], rect)
            
            text_surface =  big_font.render(pattern, True,pen_colours[(x + y) % 2])
            text_rect    =  text_surface.get_rect(center=rect.center)
            screen.blit(text_surface, text_rect)

def draw_pieces():
    def draw_with_outline(symbol, color, outline_color, pos):
        text      =  big_font.render(symbol, True, color)
        outline   =  big_font.render(symbol, True, outline_color)
        text_rect =  text.get_rect(center=pos)

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            outline_rect = outline.get_rect(center=(pos[0] + dx, pos[1] + dy))
            screen.blit(outline, outline_rect)

        screen.blit(text, text_rect)

    for name, pos in black_position.items():
        piece_symbol = pieces[name[0]]
        x, y         = pos
        draw_with_outline(piece_symbol, (15, 0, 5), (255, 255, 255), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2))

    for name, pos in white_position.items():
        piece_symbol = pieces[name[0]]
        x, y         = pos
        draw_with_outline(piece_symbol, (255, 245, 250), (0, 0, 0), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2))

def draw_capture_effect():
    global capture_timer, captured_piece
    if captured_piece and capture_timer > 0:

        x, y           = captured_piece
        pos            = (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2)
        fade_intensity = int((capture_timer / 30.0) * 200)
        fade_color     = (min(200, fade_intensity+100), 50, 100)  
        skull_symbol   = chr(0x2620)  
        skull_text     = big_font.render(skull_symbol, True, fade_color)
        skull_rect     = skull_text.get_rect(center=pos)
        
        screen.blit(skull_text, skull_rect)
        capture_timer -= 1
        
        if capture_timer <= 0:
            captured_piece = None

def draw_valid_moves():
    for move in valid_moves:
        x, y  = move
        pos   = (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2)
        if turn_step in [0, 1]: 
            star_text    = smol_font.render('*', True, (255, 255, 255))
            star_outline = smol_font.render('*', True, (0, 0, 0))
        else:
            star_text    = smol_font.render('*', True, (0, 0, 0))
            star_outline = smol_font.render('*', True, (255, 255, 255))
        
        star_rect = star_text.get_rect(center=pos)
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            outline_rect = star_outline.get_rect(center=(pos[0] + dx, pos[1] + dy))
            screen.blit(star_outline, outline_rect)
        
        screen.blit(star_text, star_rect)

def get_piece_at_position(x, y):
    if 0 <= x < 8 and 0 <= y < 8:
        piece_data = board[x, y]
        if piece_data is not None:
            color_char, piece_name = piece_data
            color = 'white' if color_char == 'w' else 'black'
            return piece_name, color
    return None, None

def is_in_check(king_color):
    # Find king position using numpy
    king_pos = None
    if king_color == 'white':
        for name, pos in white_position.items():
            if name[0] == 'K':
                king_pos = pos
                break
    else:
        for name, pos in black_position.items():
            if name[0] == 'K':
                king_pos = pos
                break
    
    if king_pos is None:
        return False
    
    opponent_color = 'black' if king_color == 'white' else 'white'
    opponent_positions = black_position if opponent_color == 'black' else white_position
    
    for name, pos in opponent_positions.items():
        moves = get_valid_moves_raw(name, opponent_color, pos)
        if king_pos in moves:
            return True
    
    return False

def get_valid_moves_raw(piece_name, piece_color, piece_pos):
    moves = []
    piece_type = piece_name[0]
    x, y = piece_pos
    
    if piece_type == 'P': 
        if piece_color == 'white':
            if y > 0 and board[x, y-1] is None:
                moves.append((x, y-1))
                if y == 6 and board[x, y-2] is None:
                    moves.append((x, y-2))
            for dx in [-1, 1]:
                if 0 <= x+dx < 8 and y > 0:
                    piece_data = board[x+dx, y-1]
                    if piece_data is not None and piece_data[0] == 'b':
                        moves.append((x+dx, y-1))
        else: 
            if y < 7 and board[x, y+1] is None:
                moves.append((x, y+1))
                if y == 1 and board[x, y+2] is None:
                    moves.append((x, y+2))
            # Diagonal captures
            for dx in [-1, 1]:
                if 0 <= x+dx < 8 and y < 7:
                    piece_data = board[x+dx, y+1]
                    if piece_data is not None and piece_data[0] == 'w':
                        moves.append((x+dx, y+1))
    
    elif piece_type == 'R':
        directions = np.array([(0, 1), (0, -1), (1, 0), (-1, 0)])
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    piece_data = board[new_x, new_y]
                    if piece_data is None:
                        moves.append((new_x, new_y))
                    else:
                        target_color = 'white' if piece_data[0] == 'w' else 'black'
                        if target_color != piece_color:
                            moves.append((new_x, new_y))
                        break
                else:
                    break
    
    elif piece_type == 'B': 
        directions = np.array([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    piece_data = board[new_x, new_y]
                    if piece_data is None:
                        moves.append((new_x, new_y))
                    else:
                        target_color = 'white' if piece_data[0] == 'w' else 'black'
                        if target_color != piece_color:
                            moves.append((new_x, new_y))
                        break
                else:
                    break
    
    elif piece_type == 'N': 
        knight_moves = np.array([(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)])
        for dx, dy in knight_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                piece_data = board[new_x, new_y]
                if piece_data is None:
                    moves.append((new_x, new_y))
                else:
                    target_color = 'white' if piece_data[0] == 'w' else 'black'
                    if target_color != piece_color:
                        moves.append((new_x, new_y))
    
    elif piece_type == 'Q': 
        directions = np.array([(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)])
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    piece_data = board[new_x, new_y]
                    if piece_data is None:
                        moves.append((new_x, new_y))
                    else:
                        target_color = 'white' if piece_data[0] == 'w' else 'black'
                        if target_color != piece_color:
                            moves.append((new_x, new_y))
                        break
                else:
                    break
    
    elif piece_type == 'K': 
        king_moves = np.array([(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)])
        for dx, dy in king_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                piece_data = board[new_x, new_y]
                if piece_data is None:
                    moves.append((new_x, new_y))
                else:
                    target_color = 'white' if piece_data[0] == 'w' else 'black'
                    if target_color != piece_color:
                        moves.append((new_x, new_y))
    
    return moves

def would_be_in_check_after_move(piece_name, piece_color, to_pos):
    # Store original state
    original_white = white_position.copy()
    original_black = black_position.copy()
    original_board = board.copy()
    
    captured_piece_name = None
    if piece_color == 'white':
        white_position[piece_name] = to_pos
        for name, pos in list(black_position.items()):
            if pos == to_pos:
                del black_position[name]
                break
    else:
        black_position[piece_name] = to_pos
        for name, pos in list(white_position.items()):
            if pos == to_pos:
                del white_position[name]
                break

    update_board_array()
    in_check = is_in_check(piece_color)
    
    white_position.clear()
    white_position.update(original_white)
    black_position.clear()
    black_position.update(original_black)
    board[:] = original_board
    
    return in_check

def get_valid_moves(piece_name, piece_color, piece_pos):
    raw_moves = get_valid_moves_raw(piece_name, piece_color, piece_pos)
    valid_moves = []
    
    for move in raw_moves:
        if not would_be_in_check_after_move(piece_name, piece_color, move):
            valid_moves.append(move)
    
    return valid_moves

def get_all_valid_moves_for_color(color):
    all_moves = []
    positions = white_position if color == 'white' else black_position
    
    for name, pos in positions.items():
        moves = get_valid_moves(name, color, pos)
        for move in moves:
            all_moves.append((name, pos, move))
    
    return all_moves

def check_game_state():
    current_color = 'white' if turn_step in [0, 1] else 'black'
    
    all_moves = get_all_valid_moves_for_color(current_color)
    in_check = is_in_check(current_color)
    
    if len(all_moves) == 0:
        if in_check:
            return "checkmate"
        else:
            return "stalemate"
    
    return "playing"

def pos_to_chess_notation(x, y):
    files = 'abcdefgh'
    ranks = '87654321'
    return files[x] + ranks[y]

def piece_to_notation(piece_name):
    piece_type = piece_name[0]
    if piece_type == 'P':
        return ''
    return piece_type

def create_pgn_move(piece_name, from_pos, to_pos, is_capture, is_check, is_checkmate):
    piece_notation = piece_to_notation(piece_name)
    from_notation = pos_to_chess_notation(*from_pos)
    to_notation = pos_to_chess_notation(*to_pos)
    
    if piece_name[0] == 'P':  # Pawn move
        if is_capture:
            move = from_notation[0] + 'x' + to_notation
        else:
            move = to_notation
    else:  # Other pieces
        if is_capture:
            move = piece_notation + 'x' + to_notation
        else:
            move = piece_notation + to_notation
    
    if is_checkmate:
        move += '#'
    elif is_check:
        move += '+'
    
    return move

def update_pgn(piece_name, from_pos, to_pos, is_capture):
    global pgn_moves, move_number
    
    opponent_color = 'black' if turn_step in [0, 1] else 'white'
    is_check       = is_in_check(opponent_color)
    opponent_moves = get_all_valid_moves_for_color(opponent_color)
    is_checkmate   = is_check and len(opponent_moves) == 0
    move_notation  = create_pgn_move(piece_name, from_pos, to_pos, is_capture, is_check, is_checkmate)
    
    if turn_step in [0, 1]:  # White's move
        pgn_moves.append(f"{move_number}.{move_notation}")
    else:  
        if pgn_moves:
            pgn_moves[-1] += f" {move_notation}"
        move_number += 1
    
    # Print current PGN
    pgn_string = " ".join(pgn_moves)
    print(f"PGN: {pgn_string}")

def check_for_win():
    white_king_exists = any(name[0] == 'K' for name in white_position.keys())
    black_king_exists = any(name[0] == 'K' for name in black_position.keys())
    
    if not white_king_exists:
        return 'black'
    elif not black_king_exists:
        return 'white'
    return None

def update_game_status():
    global game_over, winner, game_state
    
    winner = check_for_win()
    if winner:
        game_over = True
        game_state = "checkmate"
        return
    
    # Check for checkmate or stalemate
    game_state = check_game_state()
    if game_state == "checkmate":
        game_over = True
        winner = 'black' if turn_step in [0, 1] else 'white'
    elif game_state == "stalemate":
        game_over = True
        winner = "draw"

def get_status_text():
    if game_over:
        if game_state == "stalemate":
            return "Stalemate - Draw!"
        elif winner == 'white':
            return "Checkmate - White Wins!"
        elif winner == 'black':
            return "Checkmate - Black Wins!"
        else:
            return "Game Over"
    else:
        current_color = 'white' if turn_step in [0, 1] else 'black'
        in_check = is_in_check(current_color)
        check_text = " (Check!)" if in_check else ""
        
        if turn_step == 0:
            return f"White's Turn{check_text}"
        elif turn_step == 1:
            return f"White's Turn (Piece Selected){check_text}"
        elif turn_step == 2:
            return f"Black's Turn{check_text}"
        else:
            return f"Black's Turn (Piece Selected){check_text}"

def handle_click(pos):
    global turn_step, valid_moves, selected_piece, black_position, white_position, captured_piece, capture_timer
    
    if game_over:
        return
    
    x, y = pos[0] // tile_size, pos[1] // tile_size
    
    if turn_step == 0:
        for name, piece_pos in white_position.items():
            if piece_pos == (x, y):
                selected_piece = name
                valid_moves = get_valid_moves(name, 'white', piece_pos)
                turn_step = 1
                return
    
    elif turn_step == 1: 
        if (x, y) in valid_moves:
            from_pos = white_position[selected_piece]
            piece_data = board[x, y]
            is_capture = piece_data is not None
            
            if is_capture and piece_data[0] == 'b':
                captured_piece = (x, y)
                capture_timer = 30
                del black_position[piece_data[1]]
                play_capture_sound()
            else:
                play_move_sound()
            
            white_position[selected_piece] = (x, y)
            update_board_array()  # Update numpy array after move
            update_pgn(selected_piece, from_pos, (x, y), is_capture)
            
            valid_moves = []
            selected_piece = None
            turn_step = 2
            update_game_status()
        else:
            for name, piece_pos in white_position.items():
                if piece_pos == (x, y):
                    selected_piece = name
                    valid_moves = get_valid_moves(name, 'white', piece_pos)
                    return
            valid_moves = []
            selected_piece = None
            turn_step = 0
    
    elif turn_step == 2:
        for name, piece_pos in black_position.items():
            if piece_pos == (x, y):
                selected_piece = name
                valid_moves = get_valid_moves(name, 'black', piece_pos)
                turn_step = 3
                return
    
    elif turn_step == 3:
        if (x, y) in valid_moves:
            from_pos = black_position[selected_piece]
            piece_data = board[x, y]
            is_capture = piece_data is not None
            
            if is_capture and piece_data[0] == 'w':
                captured_piece = (x, y)
                capture_timer = 30
                del white_position[piece_data[1]]
                play_capture_sound()
            else:
                play_move_sound()
            
            black_position[selected_piece] = (x, y)
            update_board_array()  # Update numpy array after move
            update_pgn(selected_piece, from_pos, (x, y), is_capture)
            
            valid_moves = []
            selected_piece = None
            turn_step = 0
            update_game_status()
        else:
            for name, piece_pos in black_position.items():
                if piece_pos == (x, y):
                    selected_piece = name
                    valid_moves = get_valid_moves(name, 'black', piece_pos)
                    return
            valid_moves = []
            selected_piece = None
            turn_step = 2

update_board_array()

print("=== CHESS GAME STARTED ===")
print("Controls:")
print("- Click to select and move pieces")
print("- Press R to restart the game")
print("- Press ESC to quit")
print("PGN: [New Game]")

run = True
while run:
    timer.tick(FPS)
    screen.fill((0, 0, 0))
    
    pygame.display.set_caption(f"Chess - {get_status_text()}")

    draw_board()
    draw_pieces()
    draw_valid_moves()
    draw_capture_effect()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                handle_click(event.pos)
    
    pygame.display.update()

pygame.quit()
sys.exit()