"""
Simple Tetris Game
Controls:
  A / D  - Move left / right
  S      - Soft drop (move down faster)
  W      - Hard drop (instant drop)
  J      - Rotate piece
  R      - Restart game (when game over)
  Q      - Quit
"""

import pygame
import random
import sys

# --- Constants ---
CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = CELL_SIZE * BOARD_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = CELL_SIZE * BOARD_HEIGHT

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (25, 25, 25)
LIGHT_GRAY = (128, 128, 128)

# Colors for each piece type
COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (160, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
    'J': (0, 0, 240),
    'L': (240, 160, 0),
}

# Tetromino shapes (each rotation state)
SHAPES = {
    'I': [
        [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]],
        [[0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0]],
        [[0,0,0,0], [0,0,0,0], [1,1,1,1], [0,0,0,0]],
        [[0,1,0,0], [0,1,0,0], [0,1,0,0], [0,1,0,0]],
    ],
    'O': [
        [[1,1], [1,1]],
    ],
    'T': [
        [[0,1,0], [1,1,1], [0,0,0]],
        [[0,1,0], [0,1,1], [0,1,0]],
        [[0,0,0], [1,1,1], [0,1,0]],
        [[0,1,0], [1,1,0], [0,1,0]],
    ],
    'S': [
        [[0,1,1], [1,1,0], [0,0,0]],
        [[0,1,0], [0,1,1], [0,0,1]],
        [[0,0,0], [0,1,1], [1,1,0]],
        [[1,0,0], [1,1,0], [0,1,0]],
    ],
    'Z': [
        [[1,1,0], [0,1,1], [0,0,0]],
        [[0,0,1], [0,1,1], [0,1,0]],
        [[0,0,0], [1,1,0], [0,1,1]],
        [[0,1,0], [1,1,0], [1,0,0]],
    ],
    'J': [
        [[1,0,0], [1,1,1], [0,0,0]],
        [[0,1,1], [0,1,0], [0,1,0]],
        [[0,0,0], [1,1,1], [0,0,1]],
        [[0,1,0], [0,1,0], [1,1,0]],
    ],
    'L': [
        [[0,0,1], [1,1,1], [0,0,0]],
        [[0,1,0], [0,1,0], [0,1,1]],
        [[0,0,0], [1,1,1], [1,0,0]],
        [[1,1,0], [0,1,0], [0,1,0]],
    ],
}


class Piece:
    """Represents a falling Tetris piece."""

    def __init__(self, piece_type=None):
        self.type = piece_type or random.choice(list(SHAPES.keys()))
        self.shape = SHAPES[self.type][0]
        self.rotation = 0
        self.color = COLORS[self.type]
        # Start position: centered at top
        self.x = BOARD_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        """Rotate piece 90 degrees clockwise."""
        num_rotations = len(SHAPES[self.type])
        self.rotation = (self.rotation + 1) % num_rotations
        self.shape = SHAPES[self.type][self.rotation]

    def get_cells(self):
        """Return list of (x, y) cells occupied by this piece."""
        cells = []
        for row_idx, row in enumerate(self.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    cells.append((self.x + col_idx, self.y + row_idx))
        return cells


class TetrisGame:
    """Main Tetris game logic."""

    def __init__(self):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()

        # Drop timing
        self.drop_counter = 0
        self.drop_interval = 500  # milliseconds, decreases with level

        # Movement repeat timing (DAS - Delayed Auto Shift)
        self.das_counter = 0
        self.das_delay = 170      # ms before repeat starts
        self.das_repeat = 50      # ms between repeats
        self.moving_direction = 0  # -1=left, 0=none, 1=right

    def new_piece(self):
        """Create a new random piece."""
        return Piece()

    def get_drop_interval(self):
        """Calculate drop speed based on level."""
        return max(100, 500 - (self.level - 1) * 50)

    def collides(self, piece, offset_x=0, offset_y=0, new_shape=None):
        """Check if placing the piece at the offset would cause a collision."""
        shape = new_shape or piece.shape
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    new_x = piece.x + col_idx + offset_x
                    new_y = piece.y + row_idx + offset_y

                    # Check boundaries
                    if new_x < 0 or new_x >= BOARD_WIDTH:
                        return True
                    if new_y >= BOARD_HEIGHT:
                        return True

                    # Check occupied cells (ignore if above the board)
                    if new_y >= 0 and self.board[new_y][new_x] is not None:
                        return True
        return False

    def lock_piece(self):
        """Lock the current piece into the board."""
        for x, y in self.current_piece.get_cells():
            if y >= 0:
                self.board[y][x] = self.current_piece.color

        # Check for completed lines
        self.clear_lines()

        # Spawn next piece
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        # Check game over
        if self.collides(self.current_piece):
            self.game_over = True

    def clear_lines(self):
        """Clear completed lines and update score."""
        lines_to_clear = []
        for row_idx in range(BOARD_HEIGHT):
            if all(cell is not None for cell in self.board[row_idx]):
                lines_to_clear.append(row_idx)

        if not lines_to_clear:
            return

        # Remove completed lines (pop from bottom up so indices stay valid)
        for row_idx in sorted(lines_to_clear, reverse=True):
            self.board.pop(row_idx)

        # Add new empty lines at the top
        for _ in lines_to_clear:
            self.board.insert(0, [None for _ in range(BOARD_WIDTH)])

        # Score calculation: 100, 300, 500, 800 for 1-4 lines
        line_counts = len(lines_to_clear)
        points = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += points.get(line_counts, 0) * self.level
        self.lines_cleared += line_counts

        # Level up every 10 lines
        self.level = self.lines_cleared // 10 + 1

    def move_piece(self, dx, dy):
        """Move the current piece if possible."""
        if not self.collides(self.current_piece, offset_x=dx, offset_y=dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate_piece(self):
        """Rotate the current piece if possible."""
        new_shape = SHAPES[self.current_piece.type][(self.current_piece.rotation + 1) % len(SHAPES[self.current_piece.type])]

        # Try normal rotation
        if not self.collides(self.current_piece, new_shape=new_shape):
            self.current_piece.rotate()
            return

        # Wall kick attempts: try shifting left/right
        for kick in [-1, 1, -2, 2]:
            if not self.collides(self.current_piece, offset_x=kick, new_shape=new_shape):
                self.current_piece.x += kick
                self.current_piece.rotate()
                return

    def hard_drop(self):
        """Instantly drop the piece to the bottom."""
        while self.move_piece(0, 1):
            self.score += 2  # Bonus for hard drop
        self.lock_piece()
        self.drop_counter = 0

    def get_ghost_y(self):
        """Calculate where the piece would land (ghost piece position)."""
        ghost_y = self.current_piece.y
        while True:
            test_piece = Piece()
            test_piece.type = self.current_piece.type
            test_piece.rotation = self.current_piece.rotation
            test_piece.shape = self.current_piece.shape
            test_piece.x = self.current_piece.x
            test_piece.y = ghost_y + 1
            if self.collides(test_piece):
                break
            ghost_y += 1
        return ghost_y

    def update(self, dt):
        """Update game state with delta time in milliseconds."""
        if self.game_over or self.paused:
            return

        self.drop_counter += dt
        self.drop_interval = self.get_drop_interval()

        if self.drop_counter >= self.drop_interval:
            if not self.move_piece(0, 1):
                self.lock_piece()
            self.drop_counter = 0

    def draw(self, screen, font, small_font):
        """Draw the entire game state."""
        screen.fill(BLACK)

        # Draw board background
        pygame.draw.rect(screen, DARK_GRAY, (0, 0, CELL_SIZE * BOARD_WIDTH, CELL_SIZE * BOARD_HEIGHT), 1)

        # Draw grid lines
        for x in range(BOARD_WIDTH + 1):
            pygame.draw.line(screen, GRAY, (x * CELL_SIZE, 0), (x * CELL_SIZE, CELL_SIZE * BOARD_HEIGHT))
        for y in range(BOARD_HEIGHT + 1):
            pygame.draw.line(screen, GRAY, (0, y * CELL_SIZE), (CELL_SIZE * BOARD_WIDTH, y * CELL_SIZE))

        # Draw locked pieces on the board
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                if self.board[row][col] is not None:
                    self.draw_cell(screen, col, row, self.board[row][col])

        if not self.game_over:
            # Draw ghost piece (faint outline only)
            ghost_y = self.get_ghost_y()
            if ghost_y != self.current_piece.y:  # only draw if ghost is different from actual
                for row_idx, row in enumerate(self.current_piece.shape):
                    for col_idx, cell in enumerate(row):
                        if cell:
                            x = self.current_piece.x + col_idx
                            y = ghost_y + row_idx
                            if y >= 0:
                                self.draw_ghost_cell(screen, x, y, self.current_piece.color)

            # Draw current piece
            for x, y in self.current_piece.get_cells():
                if y >= 0:
                    self.draw_cell(screen, x, y, self.current_piece.color)

        # Draw sidebar
        self.draw_sidebar(screen, font, small_font)

        # Draw game over overlay
        if self.game_over:
            overlay = pygame.Surface((CELL_SIZE * BOARD_WIDTH, CELL_SIZE * BOARD_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            game_over_text = font.render("GAME OVER", True, WHITE)
            restart_text = small_font.render("Press R to restart", True, LIGHT_GRAY)
            screen.blit(game_over_text, (CELL_SIZE * BOARD_WIDTH // 2 - game_over_text.get_width() // 2,
                                         CELL_SIZE * BOARD_HEIGHT // 2 - 30))
            screen.blit(restart_text, (CELL_SIZE * BOARD_WIDTH // 2 - restart_text.get_width() // 2,
                                       CELL_SIZE * BOARD_HEIGHT // 2 + 10))

    def draw_cell(self, screen, x, y, color):
        """Draw a single cell with a slight 3D effect."""
        rect = pygame.Rect(x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(screen, color, rect)
        # Highlight
        pygame.draw.line(screen, color,
                         (x * CELL_SIZE + 1, y * CELL_SIZE + CELL_SIZE - 2),
                         (x * CELL_SIZE + 1, y * CELL_SIZE + 1), 2)
        pygame.draw.line(screen, color,
                         (x * CELL_SIZE + 1, y * CELL_SIZE + 1),
                         (x * CELL_SIZE + CELL_SIZE - 2, y * CELL_SIZE + 1), 2)

    def draw_ghost_cell(self, screen, x, y, color):
        """Draw a faint outline for the ghost piece."""
        rect = pygame.Rect(x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        # Dim the color significantly for the ghost
        dim_color = tuple(max(0, c - 200) for c in color)
        pygame.draw.rect(screen, dim_color, rect, 2)

    def draw_sidebar(self, screen, font, small_font):
        """Draw the sidebar with score, next piece, and controls."""
        sidebar_x = CELL_SIZE * BOARD_WIDTH + 10

        # Score
        score_label = small_font.render("SCORE", True, LIGHT_GRAY)
        score_text = font.render(str(self.score), True, WHITE)
        screen.blit(score_label, (sidebar_x, 20))
        screen.blit(score_text, (sidebar_x, 40))

        # Level
        level_label = small_font.render("LEVEL", True, LIGHT_GRAY)
        level_text = font.render(str(self.level), True, WHITE)
        screen.blit(level_label, (sidebar_x, 90))
        screen.blit(level_text, (sidebar_x, 110))

        # Lines
        lines_label = small_font.render("LINES", True, LIGHT_GRAY)
        lines_text = font.render(str(self.lines_cleared), True, WHITE)
        screen.blit(lines_label, (sidebar_x, 160))
        screen.blit(lines_text, (sidebar_x, 180))

        # Next piece
        next_label = small_font.render("NEXT", True, LIGHT_GRAY)
        screen.blit(next_label, (sidebar_x, 240))

        preview_x = sidebar_x + 10
        preview_y = 270
        piece_shape = self.next_piece.shape
        for row_idx, row in enumerate(piece_shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        preview_x + col_idx * (CELL_SIZE // 2),
                        preview_y + row_idx * (CELL_SIZE // 2),
                        CELL_SIZE // 2 - 1, CELL_SIZE // 2 - 1
                    )
                    pygame.draw.rect(screen, self.next_piece.color, rect)

        # Controls
        controls_label = small_font.render("CONTROLS", True, LIGHT_GRAY)
        screen.blit(controls_label, (sidebar_x, 400))

        controls = [
            "A/D - Move",
            "S - Soft Drop",
            "W - Hard Drop",
            "J - Rotate",
            "R - Restart",
            "Q - Quit",
        ]
        for i, ctrl in enumerate(controls):
            ctrl_text = small_font.render(ctrl, True, (100, 100, 100))
            screen.blit(ctrl_text, (sidebar_x, 430 + i * 22))

    def restart(self):
        """Restart the game."""
        self.__init__()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 36, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    game = TetrisGame()

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    game.restart()
                elif not game.game_over:
                    if event.key == pygame.K_w:
                        game.hard_drop()
                    elif event.key == pygame.K_j:
                        game.rotate_piece()

        # Handle movement with DAS (Delayed Auto Shift)
        if not game.game_over:
            keys = pygame.key.get_pressed()
            new_direction = 0
            if keys[pygame.K_a]:
                new_direction = -1
            elif keys[pygame.K_d]:
                new_direction = 1

            if new_direction != game.moving_direction:
                # Direction changed or released
                game.moving_direction = new_direction
                if new_direction != 0:
                    # First press: move immediately
                    game.move_piece(new_direction, 0)
                game.das_counter = 0
            else:
                if new_direction != 0:
                    # Still holding: DAS repeat logic
                    game.das_counter += dt
                    if game.das_counter >= game.das_delay:
                        # Only move once per DAS repeat interval
                        elapsed_since_delay = game.das_counter - game.das_delay
                        if int(elapsed_since_delay / game.das_repeat) > int((elapsed_since_delay - dt) / game.das_repeat):
                            game.move_piece(new_direction, 0)

            # Soft drop
            if keys[pygame.K_s]:
                if not game.move_piece(0, 1):
                    game.lock_piece()
                game.score += 1  # Small bonus for soft drop
                game.drop_counter = 0

        game.update(dt)
        game.draw(screen, font, small_font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
