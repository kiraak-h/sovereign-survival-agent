import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_font(size):
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf'
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def generate_advanced_pnl(token_name: str, percentage: float) -> Image:
    width, height = 800, 500
    
    # 1. Background Gradient
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    color_top = (2, 6, 23)   # Slate 950
    color_bottom = (15, 23, 42) # Slate 900
    
    for y in range(height):
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * y / height)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * y / height)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Cyberpunk Grid
    grid_color = (30, 41, 59) # Slate 800
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # 3. Sniper Corner Brackets (Cyan)
    cyan = (6, 182, 212)
    b_len = 40
    b_thick = 6
    margin = 20
    # Top Left
    draw.rectangle([margin, margin, margin+b_len, margin+b_thick], fill=cyan)
    draw.rectangle([margin, margin, margin+b_thick, margin+b_len], fill=cyan)
    # Top Right
    draw.rectangle([width-margin-b_len, margin, width-margin, margin+b_thick], fill=cyan)
    draw.rectangle([width-margin-b_thick, margin, width-margin, margin+b_len], fill=cyan)
    # Bottom Left
    draw.rectangle([margin, height-margin-b_thick, margin+b_len, height-margin], fill=cyan)
    draw.rectangle([margin, height-margin-b_len, margin+b_thick, height-margin], fill=cyan)
    # Bottom Right
    draw.rectangle([width-margin-b_len, height-margin-b_thick, width-margin, height-margin], fill=cyan)
    draw.rectangle([width-margin-b_thick, height-margin-b_len, width-margin, height-margin], fill=cyan)

    # 4. Texts
    font_title = get_font(35)
    font_token = get_font(50)
    font_pnl = get_font(130)
    font_footer = get_font(25)
    
    # Title
    draw.text((60, 40), "SOVEREIGN SNIPER UI", font=font_title, fill=cyan)
    draw.line([(60, 85), (380, 85)], fill=cyan, width=2)
    
    # Token
    draw.text((60, 130), f"TARGET :: {token_name}", font=font_token, fill=(248, 250, 252))
    
    # PnL with drop shadow
    pnl_str = f"+{percentage:.2f}%" if percentage >= 0 else f"{percentage:.2f}%"
    green_glow = (21, 128, 61)
    green_bright = (34, 197, 94)
    red_glow = (185, 28, 28)
    red_bright = (239, 68, 68)
    
    glow_color = green_glow if percentage >= 0 else red_glow
    bright_color = green_bright if percentage >= 0 else red_bright
    
    # Shadow/Glow
    draw.text((63, 213), pnl_str, font=font_pnl, fill=glow_color)
    draw.text((60, 210), pnl_str, font=font_pnl, fill=bright_color)
    
    # Footer
    footer_text = "@TheSovSniper | AST SECURITY ACTIVE"
    draw.text((60, height - 65), footer_text, font=font_footer, fill=(148, 163, 184))

    return img

if __name__ == '__main__':
    img = generate_advanced_pnl("BASE/WETH", 345.50)
    img.save("preview_pnl.png")
    print("Preview generated.")
