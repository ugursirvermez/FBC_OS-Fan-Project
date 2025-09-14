try:
    import pyfiglet
except Exception:
    pyfiglet = None

def warning_ascii_lines(text="WARNING!"):
    if pyfiglet:
        try:
            art = pyfiglet.figlet_format(text, font="standard")
            return art.rstrip("\n").split("\n")
        except Exception:
            pass
    return [text]

def tokenize_words(text: str):
    return [t for t in text.replace("\t", " ").split(" ") if t != ""]

def wrap_tokens_to_lines(tokens, font, max_width):
    lines, cur, cur_w = [], [], 0
    space_w = font.size(" ")[0]
    for tok in tokens:
        tok_w = font.size(tok)[0]
        if not cur:
            cur, cur_w = [tok], tok_w
        else:
            if cur_w + space_w + tok_w <= max_width:
                cur.append(tok); cur_w += space_w + tok_w
            else:
                lines.append(cur); cur, cur_w = [tok], tok_w
    if cur: lines.append(cur)
    return lines
