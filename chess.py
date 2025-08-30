import pygame

pygame.init()
pygame.display.set_caption("Chess")

WIDTH, HEIGHT  =  400, 400
screen         =  pygame.display.set_mode((WIDTH, HEIGHT))
smol_font      =  pygame.font.Font("font/Pecita.otf", 25)
big_font       =  pygame.font.Font("font/Pecita.otf", 50)
timer          =  pygame.time.Clock()
FPS            =  30

tile_size      =  50
board          =  [[(x, y) for y in range(8)] for x in range(8)]
pieces         =  {'K':'♚', 'Q':'♛', 'R':'♜', 'B':'♝', 'N':'♞', 'P':'♟'}
black_position =  {'P1':(0,1), 'P2':(1,1), 'P3':(2,1), 'P4':(3,1), 'P5':(4,1), 'P6':(5,1), 'P7':(6,1), 'P8':(7,1),
                   'K_':(4,0), 'Q_':(3,0), 'R1':(0,0), 'R2':(7,0), 'B1':(2,0), 'B2':(5,0), 'N1':(1,0), 'N2':(6,0)}
white_position =  {'K_':(4,7), 'Q_':(3,7), 'R1':(0,7), 'R2':(7,7), 'B1':(2,7), 'B2':(5,7), 'N1':(1,7), 'N2':(6,7),
                   'P1':(0,6), 'P2':(1,6), 'P3':(2,6), 'P4':(3,6), 'P5':(4,6), 'P6':(5,6), 'P7':(6,6), 'P8':(7,6)}
turn_step      =  0  #0 = white's turn, 1 = white's piece selected, 2 = black's turn, 3 = black's piece selected
valid_moves    =  []
selected_piece =  None
game_over      =  False
winner         =  None
captured_piece =  None
capture_timer  =  0

def draw_board():
    colors      =  [(142, 140, 150), (95, 90, 100)]
    pen_colours =  [(165, 162, 170), (75, 70, 80)]
    pattern     =  '▓'
    
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
        x, y = captured_piece
        pos = (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2)

        fade_intensity = int((capture_timer / 30.0) * 200)
        fade_color = (min(200, fade_intensity+100), 50, 100)  

        skull_symbol = chr(0x2620)  
        skull_text = big_font.render(skull_symbol, True, fade_color)
        skull_rect = skull_text.get_rect(center=pos)
        

        
        screen.blit(skull_text, skull_rect)
        capture_timer -= 1
        
        if capture_timer <= 0:
            captured_piece = None

def draw_valid_moves():
    for move in valid_moves:
        x, y = move
        pos = (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2)
        if turn_step in [0, 1]: 
            star_text = smol_font.render('*', True, (255, 255, 255))  # White asterisk
            star_outline = smol_font.render('*', True, (0, 0, 0))     # Black outline
        else:  # Black's turn
            star_text = smol_font.render('*', True, (0, 0, 0))        # Black asterisk
            star_outline = smol_font.render('*', True, (255, 255, 255)) # White outline
        
        star_rect = star_text.get_rect(center=pos)
        
        # Draw outline
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            outline_rect = star_outline.get_rect(center=(pos[0] + dx, pos[1] + dy))
            screen.blit(star_outline, outline_rect)
        
        screen.blit(star_text, star_rect)

def get_piece_at_position(x, y):
    for name, pos in white_position.items():
        if pos == (x, y):
            return name, 'white'
    for name, pos in black_position.items():
        if pos == (x, y):
            return name, 'black'
    return None, None

def get_valid_moves(piece_name, piece_color, piece_pos):
    moves = []
    piece_type = piece_name[0]
    x, y = piece_pos
    
    if piece_type == 'P': 
        if piece_color == 'white':
            if y > 0 and get_piece_at_position(x, y-1)[0] is None:
                moves.append((x, y-1))

                if y == 6 and get_piece_at_position(x, y-2)[0] is None:
                    moves.append((x, y-2))
            # Capture diagonally
            if x > 0 and y > 0:
                target_piece, target_color = get_piece_at_position(x-1, y-1)
                if target_piece and target_color == 'black':
                    moves.append((x-1, y-1))
            if x < 7 and y > 0:
                target_piece, target_color = get_piece_at_position(x+1, y-1)
                if target_piece and target_color == 'black':
                    moves.append((x+1, y-1))
        else: 
            if y < 7 and get_piece_at_position(x, y+1)[0] is None:
                moves.append((x, y+1))
                # Initial double move
                if y == 1 and get_piece_at_position(x, y+2)[0] is None:
                    moves.append((x, y+2))
            if x > 0 and y < 7:
                target_piece, target_color = get_piece_at_position(x-1, y+1)
                if target_piece and target_color == 'white':
                    moves.append((x-1, y+1))
            if x < 7 and y < 7:
                target_piece, target_color = get_piece_at_position(x+1, y+1)
                if target_piece and target_color == 'white':
                    moves.append((x+1, y+1))
    
    elif piece_type == 'R':
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    target_piece, target_color = get_piece_at_position(new_x, new_y)
                    if target_piece is None:
                        moves.append((new_x, new_y))
                    elif target_color != piece_color:
                        moves.append((new_x, new_y))
                        break
                    else:
                        break
                else:
                    break
    
    elif piece_type == 'B': 
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    target_piece, target_color = get_piece_at_position(new_x, new_y)
                    if target_piece is None:
                        moves.append((new_x, new_y))
                    elif target_color != piece_color:
                        moves.append((new_x, new_y))
                        break
                    else:
                        break
                else:
                    break
    
    elif piece_type == 'N': 
        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dx, dy in knight_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target_piece, target_color = get_piece_at_position(new_x, new_y)
                if target_piece is None or target_color != piece_color:
                    moves.append((new_x, new_y))
    
    elif piece_type == 'Q': 
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in directions:
            for i in range(1, 8):
                new_x, new_y = x + dx*i, y + dy*i
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    target_piece, target_color = get_piece_at_position(new_x, new_y)
                    if target_piece is None:
                        moves.append((new_x, new_y))
                    elif target_color != piece_color:
                        moves.append((new_x, new_y))
                        break
                    else:
                        break
                else:
                    break
    
    elif piece_type == 'K': 
        king_moves = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dx, dy in king_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target_piece, target_color = get_piece_at_position(new_x, new_y)
                if target_piece is None or target_color != piece_color:
                    moves.append((new_x, new_y))
    
    return moves

def check_for_win():
    white_king_exists = any(name[0] == 'K' for name in white_position.keys())
    black_king_exists = any(name[0] == 'K' for name in black_position.keys())
    
    if not white_king_exists:
        return 'black'
    elif not black_king_exists:
        return 'white'
    return None

def update_game_status():
    global game_over, winner
    winner = check_for_win()
    if winner:
        game_over = True

def get_status_text():
    if game_over:
        if winner == 'white':
            return "White Wins!"
        else:
            return "Black Wins!"
    else:
        if turn_step == 0:
            return "White's Turn"
        elif turn_step == 1:
            return "White's Turn (Piece Selected)"
        elif turn_step == 2:
            return "Black's Turn"
        else:
            return "Black's Turn (Piece Selected)"

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
            target_piece, target_color = get_piece_at_position(x, y)
            if target_piece and target_color == 'black':
                captured_piece = (x, y)
                capture_timer = 30
                del black_position[target_piece]
            
            white_position[selected_piece] = (x, y)
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
            # Make the move
            target_piece, target_color = get_piece_at_position(x, y)
            if target_piece and target_color == 'white':
                # Remove captured piece and set capture effect
                captured_piece = (x, y)
                capture_timer = 30  # 30 frames = 1 second at 30 FPS
                del white_position[target_piece]
            
            black_position[selected_piece] = (x, y)
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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                handle_click(event.pos)
    
    pygame.display.update()