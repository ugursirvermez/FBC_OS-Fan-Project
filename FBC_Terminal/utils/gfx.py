import pygame, math
from ..settings import FG, ACCENT, BORDER

def draw_text(surface, text, size, color, *, center=None, topleft=None, bold=False):
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", size, bold=bold)
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:  rect.center = center
    if topleft: rect.topleft = topleft
    surface.blit(surf, rect)
    return rect

def tint_green(surf: pygame.Surface, gain: float = 1.1) -> pygame.Surface:
    out = surf.convert_alpha()
    gray = pygame.Surface(out.get_size()).convert_alpha()
    gray.fill((180, 180, 180, 255))
    out.blit(gray, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    green = pygame.Surface(out.get_size()).convert_alpha()
    g = min(255, int(220 * gain))
    green.fill((0, g, 0, 255))
    out.blit(green, (0, 0), special_flags=pygame.BLEND_MULT)
    return out

def make_scanlines(size, alpha: int = 36) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 2):
        pygame.draw.line(s, (0, 0, 0, alpha), (0, y), (w, y))
    return s

def load_logo(logo_path, surface_size, scale=0.55):
    try:
        img = pygame.image.load(logo_path).convert_alpha()
    except Exception:
        font = pygame.font.SysFont("consolas,monospace", 72, bold=True)
        return font.render("FBC", True, FG)
    sw, sh = surface_size
    factor = (sh * scale) / img.get_height()
    new = (int(img.get_width()*factor), int(img.get_height()*factor))
    img = pygame.transform.smoothscale(img, new)
    return tint_green(img, gain=1.1)

def draw_header_with_right_logo(s: pygame.Surface, title: str, logo_path=None,
                                logo_scale_h=0.55, top_pad=36, side_pad=40):
    """Logo sağda, başlık solda. İçerik alanı Rect döner."""
    w, h = s.get_size()
    logo = load_logo(logo_path, (w, h), scale=logo_scale_h) if logo_path else None
    if logo:
        logo_rect = logo.get_rect()
        logo_rect.right = w - side_pad
        logo_rect.top = top_pad
        s.blit(logo, logo_rect)
    else:
        logo_rect = pygame.Rect(w - side_pad - 120, top_pad, 120, 80)

    base = max(28, min(64, w // 22))
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", base, bold=True)
    max_title_width = max(120, logo_rect.left - 2*side_pad)
    text_surf = font.render(title, True, FG)
    while text_surf.get_width() > max_title_width and base > 24:
        base -= 2
        font = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", base, bold=True)
        text_surf = font.render(title, True, FG)
    title_rect = text_surf.get_rect()
    title_rect.topleft = (side_pad, top_pad)
    s.blit(text_surf, title_rect)

    content_left   = side_pad
    content_top    = title_rect.bottom + 24
    content_right  = logo_rect.left - side_pad
    content_bottom = h - 40
    if content_right <= content_left:
        content_right = w - side_pad
    return pygame.Rect(content_left, content_top,
                       max(50, content_right - content_left),
                       max(50, content_bottom - content_top))

def draw_pulsing_highlight(s: pygame.Surface, rect: pygame.Rect, pulse_alpha: int):
    bar = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bar.fill((0, 255, 0, pulse_alpha))
    s.blit(bar, rect.topleft)
    pygame.draw.rect(s, BORDER, rect, 1)
