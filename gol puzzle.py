import pygame
import numpy as np
import json
import os

pygame.display.init()
something = min(pygame.display.Info().current_h, pygame.display.Info().current_w)
SAVE_FILE = "save_data.json"
CELL_SIZE = (0.9 * something) // 20
GRID_WIDTH = 20
GRID_HEIGHT = 20
FPS = 10
MAX_PLACED = 10
history = []

BG_COLOR = (10, 10, 10)
GRID_COLOR = (40, 40, 40)
CELL_COLOR = (255, 255, 255)

pygame.init()
SIDE_PANEL_WIDTH = 0
screen = pygame.display.set_mode((GRID_WIDTH * CELL_SIZE + SIDE_PANEL_WIDTH, GRID_HEIGHT * CELL_SIZE))
clock = pygame.time.Clock()
running = True
paused = True
started = False
total_gen = 0
gen = 0
placed = 0
rules = "3/23"
win = False
level = -1
frame_advance = False
glider = "glider"
showing_info = False


def new_level():
    global level, walls, rules, destination, MAX_PLACED, placeable, grid, showing_info, GRID_WIDTH, GRID_HEIGHT, CELL_SIZE
    showing_info = True
    level += 1
    try:
        with open(f"levels/level-{level}.json", "r") as f:
            level_data = json.load(f)
            walls = np.array(level_data["walls"], dtype=int)
            rules = level_data["rules"]
            destination = level_data["destination"]
            MAX_PLACED = level_data["MAX_PLACED"]
            GRID_WIDTH, GRID_HEIGHT = level_data.get("GRID_SIZE", (GRID_WIDTH)), level_data.get("GRID_SIZE", (GRID_HEIGHT))
            placeable = np.array(level_data.get("placeable", np.random.choice([1], size=(GRID_HEIGHT, GRID_WIDTH))), dtype=int)
            grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        if walls.shape != (GRID_HEIGHT, GRID_WIDTH):
            walls = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        if placeable.shape != (GRID_HEIGHT, GRID_WIDTH):
            placeable = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        
    except FileNotFoundError:
        GRID_WIDTH, GRID_HEIGHT = 40, 40
        grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        walls = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        placeable = np.ones((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        destination = [[0, 0]]
        rules = "3/23"
        MAX_PLACED = 100000
    CELL_SIZE = min(screen.get_width() // GRID_WIDTH, screen.get_height() // GRID_HEIGHT)


def save_grid():
    global walls, rules, destination, grid, MAX_PLACED, level, GRID_WIDTH, placeable
    grid_list = walls.tolist()
    placeable = grid.tolist()
    level_data = {
        "walls": grid_list,
        "placeable": placeable,
        "rules": rules,
        "destination": destination,
        "MAX_PLACED": MAX_PLACED,
        "GRID_SIZE": GRID_WIDTH
    }
    with open(f"levels/level-{level}.json", "w") as f:
        json.dump(level_data, f)
        
def fit_text_to_button(text, font_name, max_width, max_height, max_font_size=30, min_font_size=8, return_size=False):
    """
    Returns a pygame.font.Font object with the largest font size that fits
    the text inside the given max_width and max_height bounds.
    """
    for size in range(max_font_size, min_font_size - 1, -1):
        font = pygame.font.Font(font_name, size)
        text_surface = font.render(text, True, (0, 0, 0))
        if text_surface.get_width() <= max_width and text_surface.get_height() <= max_height:
            return font if not return_size else (font, size)
    return pygame.font.Font(font_name, min_font_size) if not return_size else (pygame.font.Font(font_name, min_font_size), (min_font_size))

pygame.display.set_caption("Game of Life Puzzle")

class info():
    def __init__(self, title, text=None, font_name="freesansbold.ttf", max_width=200, max_height=100, surface=screen, image=None, max_frame=48):
        self.text = text
        self.title = title
        self.surface = surface
        self.image = image
        self.max_frame = max_frame
        if self.image:
            self.frame = 0
        self.rect = pygame.Rect(
            self.surface.get_width() / 2 - max_width / 2,
            self.surface.get_height() / 2 - max_height / 2,
            max_width,
            max_height
        )
        self.font = pygame.font.Font(font_name, 16)
        self.title_font = pygame.font.Font(font_name, 20)

    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        return lines

    def draw(self):
        pygame.draw.rect(self.surface, (0, 0, 20), self.rect)

        title_surface = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.rect.centerx, self.rect.top + 20))
        self.surface.blit(title_surface, title_rect)
        
        if self.text:
            lines = self.wrap_text(self.text, self.font, self.rect.width - 10)
            line_height = self.font.get_height()
            start_y = title_rect.bottom + 10

            for i, line in enumerate(lines):
                if start_y + i * line_height > self.rect.bottom - 10:
                    break
                text_surface = self.font.render(line, True, (255, 255, 255))
                text_rect = text_surface.get_rect(centerx=self.rect.centerx)
                text_rect.top = start_y + i * line_height
                self.surface.blit(text_surface, text_rect)
        if self.image:
            image = pygame.image.load(os.path.join(f"{self.image}", f"{self.frame}.png"))
            image = pygame.transform.smoothscale(image, (self.surface.get_width(), self.surface.get_height()))
            img_rect = image.get_rect(center=(self.rect.centerx, self.rect.centery))
            self.surface.blit(image, img_rect)
            self.frame += 1
            self.frame %= self.max_frame

# info_texts = [
#     info("Try reaching the goal by placing just 3 cells. The rules are: A new cell is born if exactly 3 neighbors surround an empty spot. A cell survives if it has 2 or 3 neighbors.", "First Steps", max_width=300, max_height=150),
#     info("Gliders are small patterns that move diagonally across the grid over time. They’re made of just 5 cells and are useful for reaching distant targets. To place a glider: Start with 3 cells in an L-shape (like an arrow pointing the direction you want it to move). Add a 4th cell to one wing of the L. Then place the 5th cell opposite the middle of the longer side. Gliders replicate their shape and move one step diagonally every few generations.", "Gliders", max_width=300, max_height=250),
#     info("Gliders are great — but sometimes, you need to move in a orthogonally. Good thing we have the Lightweight Spaceship (LWSS): a larger pattern that moves orthogonally across the grid using exactly 9 cells. To build one: Start with an L shape, just like a regular glider. Extend both arms of the L by one more cell. Now, extend the arm pointing away from your target a second time — this becomes the long side. Next, add a cell diagonally next to each end of the long and short arms. Finally, in the corner opposite the others (the one that doesn't touch any other cell), place a ninth cell. This finishes the rectangle that forms the LWSS.", "Big Gliders", max_width=300, max_height= 340),
#     info("The LWSS is just one of the many spaceships in its family but it happens to be the most versatile. One of its most useful features is that it can be used to create a glider by crashing it into a wall (or another LWSS). This glider will move back the way the LWSS was moving as well as moving to one of the sides (depending on the initial structure of the LWSS). This is useful for going around obstacles.", "Uh oh, Crash!", max_width=300, max_height= 240),]

info_texts = [
    info(""),
    info(title="Glider", image=glider),
    info("Turners", text="Turners are a large family of patterns that can be used to change the path of a glider. Be careful, they can often fail because they require a specific \"colour\" of glider to work. So if your glider fails, try swapping the long and short sides.", max_width=300, max_height=150),
    info("Big Glider", image="big glider", max_frame=17),
    info(""),
    info(""),
    info("Replicator", image="replicator", max_frame=15),

]

def draw_grid(surface, grid):
    surface.fill(BG_COLOR)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if walls[y][x] == 1:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (100, 100, 100), rect)
            elif grid[y][x] == 1:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, CELL_COLOR, rect)
            elif [x, y] in destination:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (255, 0, 0), rect)
            elif not started and placeable[y][x] == 1:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, (0, 100, 0), rect)
    for x in range(0, GRID_WIDTH * CELL_SIZE, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, GRID_HEIGHT * CELL_SIZE))
    for y in range(0, GRID_HEIGHT * CELL_SIZE, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (GRID_WIDTH * CELL_SIZE, y))

def draw_ui(surface):
    global font
    global showing_info
    font, size = fit_text_to_button(f"Press SPACE to start. | Cells placed: {placed}/{MAX_PLACED} | Rules: {rules}", None, surface.get_width() - 20, 100, return_size=True)
    big_font = pygame.font.Font(None, int(size * 1.5))

    if showing_info:
        try:
            if info_texts[level].title != "":
                info_texts[level].draw()
                prompt_text = font.render("Press ENTER to continue...", True, (255, 255, 0))
                surface.blit(prompt_text, (surface.get_width() // 2 - prompt_text.get_width() // 2, surface.get_height() - 40))
            else: raise IndexError
            return
        except IndexError:
            showing_info = False

    if not started:
        start_text = font.render(f"Press SPACE to start. | Cells placed: {placed}/{MAX_PLACED} | Rules: {rules}", True, (255, 255, 255))
        surface.blit(start_text, (10, 10))

    if win:
        win_text = big_font.render("You reached the destination!", True, (0, 255, 0))
        continue_text = font.render("Press ENTER to continue to the next level.", True, (0, 255, 0))
        surface.blit(win_text, (GRID_WIDTH * CELL_SIZE // 2 - win_text.get_width() // 2, GRID_HEIGHT * CELL_SIZE // 2 - win_text.get_height() // 2))
        surface.blit(continue_text, (GRID_WIDTH * CELL_SIZE // 2 - continue_text.get_width() // 2, GRID_HEIGHT * CELL_SIZE // 2 + win_text.get_height() // 2))

def update(grid):
    new_grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            total = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    ny = (y + dy)
                    nx = (x + dx)
                    total += grid[ny][nx] if (0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH) and walls[ny][nx] != 1 else 0

            current = grid[y][x]
            new = 0
            if walls[y][x] == 1:
                continue
            
            if current == 1 and str(total) in rules.split('/')[1]:
                new = 1
            elif current == 0 and str(total) in rules.split('/')[0]:
                new = 1

            new_grid[y][x] = new

    return new_grid

def save_game():
    data = {
        "level": level-1
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_game():
    global level
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            level = data.get("level", -1)
            
import sys

class Button:
    def __init__(self, rect, text, font, color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_surf = font.render(text, True, (255, 255, 255))

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        screen.blit(self.text_surf, self.text_surf.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

def show_title_screen(screen, font):
    screen.fill((0, 0, 0))
    w, h = screen.get_size()
    extra = 125
    background = pygame.image.load(os.path.join(f"title screen",f"{1}.png"))
    background = pygame.transform.smoothscale(background, (w, h))
    screen.blit(background, (0, 0))

    button_width, button_height = 250, 60
    spacing = 80

    buttons = {
        "new": Button(((w - button_width)//2, h//2 - spacing + extra, button_width, button_height), "New Game", font, (200, 200, 200), (255, 255, 255)),
        "continue": Button(((w - button_width)//2, h//2 + extra, button_width, button_height), "Continue", font, (200, 200, 200), (255, 255, 255)),
        "quit": Button(((w - button_width)//2, h//2 + spacing + extra, button_width, button_height), "Quit", font, (200, 200, 200), (255, 255, 255)),
    }
    
    pygame.display.flip()

    clock = pygame.time.Clock()

    while True:
        screen.fill((0, 0, 0))
        screen.blit(background, (0, 0))

        for btn in buttons.values():
            btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for name, btn in buttons.items():
                if btn.is_clicked(event):
                    if name == "quit":
                        pygame.quit()
                        sys.exit()
                    for i in range(3):
                        background = pygame.image.load(os.path.join(f"title screen", f"{i + 1}.png"))
                        background = pygame.transform.smoothscale(background, (w, h))
                        screen.blit(background, (0, 0))
                        pygame.display.flip()
                        clock.tick(2)
                    return name

        clock.tick(60)

draw_ui(screen)
screen.fill(BG_COLOR)

if show_title_screen(screen, font) == "continue":
    load_game()
new_level()

while running:
    if frame_advance:
        frame_advance = False
        paused = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
        elif event.type == pygame.KEYDOWN:
            if showing_info:
                if event.key == pygame.K_RETURN:
                    screen.fill(BG_COLOR)
                    showing_info = False
                    FPS = 10 if FPS == 1 else FPS
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    FPS = 1 if FPS == 10 else 10
            else:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    started = True
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    FPS = 20 if FPS == 10 else 10
                elif event.key == pygame.K_r and not started:
                    import random
                    placed = 0
                    grid.fill(0)
                    while placed < MAX_PLACED:
                        gx = random.randint(0, GRID_WIDTH - 1)
                        gy = random.randint(0, GRID_HEIGHT - 1)
                        if grid[gy][gx] == 0:
                            grid[gy][gx] = 1
                            placed += 1
                elif event.key == pygame.K_RETURN:
                    grid.fill(0)
                    placed = 0
                    if win:
                        grid.fill(0)
                        placed = 0
                        new_level()
                elif event.key == pygame.K_s:
                    save_grid()
                elif paused and event.key == pygame.K_KP6:
                    paused = False
                    started = True
                    frame_advance = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not showing_info:
            if not started:
                mx, my = event.pos
                if mx < GRID_WIDTH * CELL_SIZE and my < GRID_HEIGHT * CELL_SIZE:
                    gx, gy = mx // CELL_SIZE, my // CELL_SIZE
                    if MAX_PLACED > placed and walls[gy][gx] == 0 and grid[gy][gx] == 0 and [gx, gy] not in destination and placeable[gy][gx] == 1:
                        grid[gy][gx] = 1
                        placed += 1
                    elif grid[gy][gx] == 1:
                        grid[gy][gx] = 0
                        placed -= 1

    if grid.any() == 0 and started:
        total_gen += gen
        gen = 0
        placed = 0
        paused = True
        started = False
        save_game()
    for d in destination:
        if grid[d[1]][d[0]] == 1:
            win = True
        else:
            win = False
            break
    if win:
        paused = True
    
    if not paused:
        grid = update(grid)

        grid_hash = hash(grid.tobytes())
        history.append(grid_hash)
        gen += 1
        
    draw_grid(screen, grid)
    draw_ui(screen)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()