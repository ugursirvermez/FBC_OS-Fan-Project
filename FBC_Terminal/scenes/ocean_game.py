# oceanview_atmo.py
# Minimal 2.5D raycaster — Oceanview Motel: Lobby + Corridor (atmospheric)
import sys, math, pygame

# ------------------ Tunables ------------------
FULLSCREEN = True
FPS = 60
FOV = math.radians(60)
MOVE_SPEED, STRAFE_SPEED, ROT_SPEED = 3.1, 2.7, 2.4
MAX_DEPTH = 32.0

# base palette (will be graded per distance/zone)
WALL  = (92, 62, 32)     # brown wood panels
DOOR  = (155, 165, 180)  # motel doors (cool gray-blue)
FLOOR = (126, 52, 36)    # warm lobby carpet
CEIL  = (70, 70, 73)     # cool grey
UI    = (180, 230, 180)

# ------------------ Map ------------------
# 0 empty, 1 wall, 2 door
# Lobby (left), reception desk area, then long corridor with rooms.
# 22x20 grid — corridor with 6 doors (3 symbol, 3 numbered) + Casino + Janitor
RAW = [
    "1111111111111111111111",
    "1111111111202111111111",
    "1111111111101111111111",
    "1111111111202111111111",
    "1111111111101111111111",
    "1111111111202111111111",
    "1111111111101111111111",
    "1111111111000001111111",
    "1111111112000001111111",
    "1111111112000001111111",
    "1111111111000002111111",
    "1111111111000001111111",
    "1111111111101111111111",
    "1111111111202111111111",
    "1111111111101111111111",
    "1111111111202111111111",
    "1111111111101111111111",
    "1111111111202111111111",
    "1111111111111111111111",
    "1111111111111111111111",
]
# parse
H, W = len(RAW), len(RAW[0])
WORLD = [[int(c) for c in row] for row in RAW]

# Clean: spaces → 0
RAW = [r.replace(' ', '0') for r in RAW]
H, W = len(RAW), len(RAW[0])
WORLD = [[int(c) for c in r] for r in RAW]

# label & color for special cells
DOOR_LABELS = {
    # symbols (triangle, circle, square)
    (6,1): "△", (6,3): "△", (6,15): "△",
    (12,1): "○", (12,3): "○", (12,15): "○",
    # numbered 
    (6,5): "222", (12,5): "223", (6,13): "224", (12,13): "225",
    # casino & janitor
    (6,17): "CASINO", (19,17): "DOOR",
}
COLOR_LOOKUP = {
    1: (92,62,32),     # wall (wood)
    2: (155,165,180),  # numbered doors
    3: (140,160,200),  # symbol doors
    4: (230,180,80),   # casino 
    5: (120,190,150),  # janitor 
}
# --- Embed-friendly exit flag ---
EXIT_TO_MENU = False

# --- Floor/Ceiling palette---
CHECK_CELL = 16  # checker piksel  (16-24)
CHECK_A    = 26  # checker  alpha
CHECK_COL1 = (18, 22, 18)   
CHECK_COL2 = (24, 28, 22)   

DOOR_FRAME_W = 0.05  # 0.03-0.08
DOOR_FONT = None  # global placeholder

# Door meta
# (gx, gy)
DOOR_META = {
    (10, 5): "DOOR",
    (15, 12): "CASINO",
    (8, 7): "ROOM 101",
    (9, 7): "ROOM 102",
    (12, 7): "TRIANGLE SYMBOL",
    (13, 7): "CIRCLE SYMBOL",
}

# Checker cache 
_FLOOR_CHECKER_CACHE = {"size": None, "surf": None}

def make_floor_checker(size, cell=CHECK_CELL, col1=CHECK_COL1, col2=CHECK_COL2, alpha=CHECK_A):
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            c = col1 if ((x//cell + y//cell) % 2 == 0) else col2
            r = pygame.Rect(x, y, cell, cell)
            s = pygame.Surface((cell, cell), pygame.SRCALPHA)
            s.fill((*c, alpha))
            surf.blit(s, r.topleft)
    return surf

def find_doors(WORLD):
    coords = []
    for y, row in enumerate(WORLD):
        for x, cell in enumerate(row):
            if cell in (2,3,4,5):  
                coords.append((x, y, cell))
    return coords

for gx, gy, typ in find_doors(WORLD):
    print(f"Door at ({gx},{gy}) type={typ}")

def cell(x, y):
    if 0 <= x < W and 0 <= y < H: return WORLD[y][x]
    return 1
def set_cell(x, y, v):
    if 0 <= x < W and 0 <= y < H: WORLD[y][x] = v

# ------------------ Player ------------------
class Player:
    def __init__(self, x, y, a):
        self.x, self.y, self.a = x, y, a
    def move(self, dt, keys):
        
        forward = (
            keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_i]
        ) - (
            keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_k])
        strafe = (
            keys[pygame.K_d] or keys[pygame.K_l]
        ) - (
            keys[pygame.K_a] or keys[pygame.K_j])

        # Shift
        speed_mul = 1.0 + (1.0 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 0.0)

        fwd = forward * MOVE_SPEED * speed_mul * dt
        stf = strafe  * STRAFE_SPEED * speed_mul * dt

        ca, sa = math.cos(self.a), math.sin(self.a)
        nx = self.x + (ca*fwd - sa*stf)
        ny = self.y + (sa*fwd + ca*stf)

        
        if cell(int(nx), int(self.y)) == 0: self.x = nx
        if cell(int(self.x), int(ny)) == 0: self.y = ny

        # ← → or Q/E
        if keys[pygame.K_LEFT]  or keys[pygame.K_q]: self.a -= ROT_SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_r]: self.a += ROT_SPEED * dt


# ------------------ Raycast ------------------
def raycast(px, py, ang):
    rayDirX = math.cos(ang)
    rayDirY = math.sin(ang)

    mapX, mapY = int(px), int(py)

    # avoid div/0
    deltaDistX = abs(1.0 / rayDirX) if rayDirX != 0 else 1e30
    deltaDistY = abs(1.0 / rayDirY) if rayDirY != 0 else 1e30

    if rayDirX < 0:
        stepX = -1
        sideDistX = (px - mapX) * deltaDistX
    else:
        stepX = 1
        sideDistX = (mapX + 1.0 - px) * deltaDistX

    if rayDirY < 0:
        stepY = -1
        sideDistY = (py - mapY) * deltaDistY
    else:
        stepY = 1
        sideDistY = (mapY + 1.0 - py) * deltaDistY

    side = 0
    hit_type = 1

    for _ in range(1024):  # safety
        if sideDistX < sideDistY:
            sideDistX += deltaDistX
            mapX += stepX
            side = 0
        else:
            sideDistY += deltaDistY
            mapY += stepY
            side = 1

        hit_type = cell(mapX, mapY)
        if hit_type in (1,2,3,4,5):
            break

    # perpendicular wall distance
    if side == 0:
        perpDist = (mapX - px + (1 - stepX) * 0.5) / (rayDirX if rayDirX != 0 else 1e-6)
    else:
        perpDist = (mapY - py + (1 - stepY) * 0.5) / (rayDirY if rayDirY != 0 else 1e-6)

    return abs(perpDist), (side == 1), hit_type, (mapX, mapY)

def cast_and_draw(surf, pl, door_hits):
    w, h = surf.get_size()
    horizon = h // 2

    # =========================
    #  CEILING — PANEL (GRID)
    # =========================
    pygame.draw.rect(surf, CEIL, (0, 0, w, horizon))
    CEIL_CELL  = 64                  
    CEIL_LINE  = (72, 72, 75)        

    for y in range(0, horizon, CEIL_CELL):
        pygame.draw.line(surf, CEIL_LINE, (0, y), (w, y), 1)
    for x in range(0, w, CEIL_CELL):
        pygame.draw.line(surf, CEIL_LINE, (x, 0), (x, horizon), 1)

    # ===============
    #  FLOOR + CHECKER
    # ===============
    pygame.draw.rect(surf, FLOOR, (0, horizon, w, h - horizon))

    global _FLOOR_CHECKER_CACHE
    need = (_FLOOR_CHECKER_CACHE["size"] != (w, h - horizon))
    if need or _FLOOR_CHECKER_CACHE["surf"] is None:
        _FLOOR_CHECKER_CACHE["size"] = (w, h - horizon)
        _FLOOR_CHECKER_CACHE["surf"] = make_floor_checker((w, h - horizon))
    surf.blit(_FLOOR_CHECKER_CACHE["surf"], (0, horizon))

    proj = (w / 2) / math.tan(FOV / 2)
    zbuf = [MAX_DEPTH] * w
    door_hits.clear()

    
    LABEL_MAX_DIST = 9.0
    FAR_FADE_START = 7.0
    FAR_FADE_END   = 14.0

    for x in range(w):
        
        ray_screen = (x / w) * 2.0 - 1.0
        ang = pl.a + math.atan(ray_screen * math.tan(FOV / 2))

        # simple raycast
        dist, side_is_y, typ, grid = raycast(pl.x, pl.y, ang)

        
        dist *= math.cos(ang - pl.a)
        if dist < 1e-4:
            dist = 1e-4
        zbuf[x] = dist

        wall_h = min(h, int((1.0 / dist) * proj))
        y0 = horizon - wall_h // 2

        
        if side_is_y:
            hitX = pl.x + math.cos(ang) * dist
        else:
            hitX = pl.y + math.sin(ang) * dist
        wall_u = hitX - math.floor(hitX)  # 0..1

        
        base = COLOR_LOOKUP.get(typ, COLOR_LOOKUP.get(1, (92, 62, 32)))
        shade = max(40, 255 - int(dist * 28))
        col = (base[0] * shade // 255,
               base[1] * shade // 255,
               base[2] * shade // 255)

        
        gx = int(pl.x + math.cos(ang) * dist)
        warm_zone = (gx < 7)
        if warm_zone:
            col = (min(255, col[0] + 18), max(0, col[1] - 4), max(0, col[2] - 8))
        else:
            b = min(40, int(dist * 2))
            col = (max(0, col[0] - b), max(0, col[1] - b // 2), min(255, col[2] + b))

        
        if side_is_y:
            col = (int(col[0] * 0.78), int(col[1] * 0.78), int(col[2] * 0.82))

        # DOOR_META
        tag = DOOR_META.get(grid) if typ in (2, 3, 4, 5) else None
        if tag == "JANITOR":
            tint = (40, 120, 120)
            t = min(1.0, max(0.0, (dist - 3.0) / 8.0))
            col = (int(col[0]*(1-t) + tint[0]*t),
                   int(col[1]*(1-t) + tint[1]*t),
                   int(col[2]*(1-t) + tint[2]*t))
        elif tag == "CASINO":
            tint = (200, 140, 40)
            t = max(0.0, 1.0 - dist/10.0)
            col = (int(col[0]*(1-t) + tint[0]*t),
                   int(col[1]*(1-t) + tint[1]*t),
                   int(col[2]*(1-t) + tint[2]*t))

        
        if typ in (2, 3, 4, 5) and dist > FAR_FADE_START:
            t = min(1.0, max(0.0, (dist - FAR_FADE_START) / (FAR_FADE_END - FAR_FADE_START)))
            wall_ref = COLOR_LOOKUP.get(1, (92, 62, 32))
            col = (
                int(col[0] * (1 - t) + wall_ref[0] * t),
                int(col[1] * (1 - t) + wall_ref[1] * t),
                int(col[2] * (1 - t) + wall_ref[2] * t),
            )

        # panel
        stripe = abs((wall_u - 0.5) * 2.0)               # 0 center, 1 margin
        panel_gain = 1.0 - 0.08 * (1.0 - (stripe ** 2)) 
        col = (int(col[0] * panel_gain),
               int(col[1] * panel_gain),
               int(col[2] * panel_gain))

        # Door width
        if typ in (2, 3, 4, 5):
            fw = DOOR_FRAME_W  # 0.03–0.08 arası deneyebilirsin
            if wall_u < fw or wall_u > 1.0 - fw:
                col = (int(col[0] * 0.55), int(col[1] * 0.55), int(col[2] * 0.60))

        # fog
        fog = min(120, int(dist * 10))
        col = (max(0, col[0] - fog // 3),
               max(0, col[1] - fog // 3),
               max(0, col[2] - fog // 2))

        #Draw Wall
        wall_h = max(1, wall_h)
        pygame.draw.line(surf, col, (x, y0), (x, y0 + wall_h), 1)

        
        base_h = max(1, wall_h // 12)
        bb_col = (int(col[0] * 0.6), int(col[1] * 0.6), int(col[2] * 0.7))
        by0 = y0 + wall_h - base_h
        if 0 <= by0 < h:
            pygame.draw.line(surf, bb_col, (x, by0), (x, min(h-1, by0 + base_h)), 1)

        # DoorLabel count
        if typ in (2, 3, 4, 5) and dist <= LABEL_MAX_DIST:
            door_hits.setdefault(grid, []).append((x, y0, wall_h, dist))

    return zbuf


# ------------------ Sprites ------------------
class Sprite:
    def __init__(self, x, y, color, size=1.0, emissive=0):
        self.x, self.y, self.color, self.size, self.em = x, y, color, size, emissive

def draw_sprites(surf, pl, sprites, zbuf):
    w,h = surf.get_size()
    horizon = h//2
    proj = (w/2)/math.tan(FOV/2)
    order = sorted(sprites, key=lambda s: (s.x-pl.x)**2+(s.y-pl.y)**2, reverse=True)

    for sp in order:
        dx, dy = sp.x-pl.x, sp.y-pl.y
        dist = math.hypot(dx,dy)
        if dist < 0.2: continue
        ang = math.atan2(dy,dx) - pl.a
        while ang<-math.pi: ang+=2*math.pi
        while ang> math.pi: ang-=2*math.pi
        if abs(ang) > (FOV/2)+0.25: continue

        screen_x = int((math.tan(ang)*proj) + w/2)
        hgt = int((1.0/dist)*proj*sp.size)
        wid = hgt//2
        top = horizon - hgt//2
        left = screen_x - wid//2

        # emissive halo (for lamps)
        if sp.em>0:
            halo = pygame.Surface((wid, hgt), pygame.SRCALPHA)
            halo.fill((sp.color[0], sp.color[1], sp.color[2], sp.em))
            surf.blit(halo, (left, top), special_flags=pygame.BLEND_RGBA_ADD)

        for x in range(max(0,left), min(w,left+wid)):
            if dist < zbuf[x]:
                pygame.draw.line(surf, sp.color, (x, top), (x, top+hgt), 1)

def label_doors(surf, door_hits):
    # ...
    for grid, spans in door_hits.items():
        x_min = min(s[0] for s in spans)
        x_max = max(s[0] for s in spans)
        y_avg = sum(s[1] for s in spans) // len(spans)
        
        name = "DOOR"
        if grid in DOOR_META:
            name = DOOR_META[grid]
      
        txt = DOOR_FONT.render(name, True, (230, 230, 210))
        rect = txt.get_rect(midbottom=( (x_min + x_max)//2, max(0, y_avg - 6) ))
       
        pad = 4
        bg = pygame.Surface((rect.width + pad*2, rect.height + pad*2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 110))
        surf.blit(bg, (rect.left - pad, rect.top - pad))
        surf.blit(txt, rect.topleft)

# Resception & lobby props (approx coords in grid units)
SPRITES = []

# ------------------ Interaction ------------------
def try_interact(pl):
    lx = pl.x + math.cos(pl.a)*0.9
    ly = pl.y + math.sin(pl.a)*0.9
    gx, gy = int(lx), int(ly)
    c = cell(gx,gy)
    if c==2:
        set_cell(gx,gy,0); pygame.quit(); sys.exit(0)
    if c==0:
        # close if original door position
        if (gx,gy) in DOOR_LABELS: set_cell(gx,gy,2); return "Door closed."
    return None

def draw_ui(surf, msg=None):
    w,h = surf.get_size()
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 18)
    tip = "[WASD / IJKL / ↑↓] move  [←→ / Q R] turn  [E] interact  [F11] fullscreen  [ESC] quit"
    surf.blit(font.render(tip, True, (160,230,160)), (12, 10))
    if msg:
        surf.blit(font.render(msg, True, (200,240,200)), (12, h-26))

# ------------------ Main ------------------
def main():
    pygame.init(); pygame.font.init()
    global DOOR_FONT  # <-- İmportant: global
    try:
        DOOR_FONT = pygame.font.SysFont("consolas", 18, bold=True)
        if DOOR_FONT is None:
            raise RuntimeError("sysfont not found")
    except Exception:
        DOOR_FONT = pygame.font.Font(None, 18) 
    flags = pygame.FULLSCREEN if FULLSCREEN else 0
    screen = pygame.display.set_mode((0,0), flags) if FULLSCREEN else pygame.display.set_mode((1280,720))
    pygame.display.set_caption("Oceanview Motel — Lobby + Corridor (Raycast)")
    clock = pygame.time.Clock()

    # Start in lobby facing corridor
    pl = Player(10.5, 10.5, 0.0)
    info=None; info_t=0.0
    door_hits={}

    running=True
    while running:
        dt = clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: running=False
                elif e.key==pygame.K_F11:
                    fs = screen.get_flags() & pygame.FULLSCREEN
                    pygame.display.quit(); pygame.display.init()
                    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN if not fs else 0)
                elif e.key==pygame.K_e:
                    info = try_interact(pl); info_t=1.4

        keys = pygame.key.get_pressed()
        pl.move(dt, keys)

        z = cast_and_draw(screen, pl, door_hits)
        label_doors(screen, door_hits)
        draw_sprites(screen, pl, SPRITES, z)

        if info_t>0: info_t-=dt
        else: info=None
        draw_ui(screen, info)

        pygame.display.flip()

    pygame.quit(); sys.exit(0)

if __name__ == "__main__":
    main()
