import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        url = 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf'
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def generate_pnl_image(token_name: str, percentage: float, referrer_id: str = None) -> io.BytesIO:
    width, height = 700, 900
    img = Image.new('RGB', (width, height), color=(10, 10, 15))
    draw = ImageDraw.Draw(img)
    
    green = (34, 197, 94)
    red = (239, 68, 68)
    gold = (250, 204, 21)
    cyan = (6, 182, 212)
    
    # 1. Add Character Background
    char_path = 'core/assets/character.jpg'
    if os.path.exists(char_path):
        char = Image.open(char_path).convert('RGBA')
        # Resize to fit the height
        char = char.resize((900, 900))
        # Create an alpha mask to fade it out towards the left, and generally lower opacity
        mask = Image.new('L', char.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        # Gradient from left to right (0 to 180 opacity)
        for x in range(char.size[0]):
            alpha = int((x / char.size[0]) * 180)
            draw_mask.line([(x, 0), (x, char.size[1])], fill=alpha)
        char.putalpha(mask)
        # Paste on the right side
        img.paste(char, (width - char.size[0] + 150, 0), char)

    # 2. Diagonal Grid Lines
    for i in range(0, 1600, 20):
        draw.line([(i, 0), (0, i)], fill=(20, 20, 25), width=2)
        
    # 3. Logo Watermark
    logo_path = 'core/assets/logo.jpg'
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert('RGBA')
        small_size = 100
        small_logo = logo.resize((small_size, small_size))
        mask = Image.new('L', (small_size, small_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, small_size, small_size), fill=255)
        img.paste(small_logo, (width - small_size - 40, 40), mask)

    # Fonts
    font_large = get_font(140)
    font_med = get_font(80)
    font_small = get_font(40)
    font_tiny = get_font(25)
    
    # Top Logo/Name
    draw.text((40, 60), "SOVEREIGN SNIPER", font=font_small, fill=(255, 255, 255))
    draw.line([(40, 110), (width - 160, 110)], fill=cyan, width=3)
    
    # Token
    draw.text((40, 150), token_name, font=font_med, fill=(255, 255, 255))
    
    # PnL
    color = green if percentage >= 0 else red
    sign = "+" if percentage >= 0 else ""
    draw.text((40, 300), f"{sign}{percentage:.2f}%", font=font_large, fill=color)
    
    # Multiplier
    multiplier = (percentage / 100) + 1
    draw.text((40, 480), f"{multiplier:.2f}x", font=font_med, fill=cyan)
    
    # Fake Entry/Current
    draw.text((40, 650), "Entry:   PROTECTED", font=font_small, fill=(150, 150, 150))
    draw.text((40, 710), "Current: PROTECTED", font=font_small, fill=(150, 150, 150))
    
    # Footer
    draw.rectangle([0, height-100, width, height], fill=(15, 15, 20))
    draw.text((40, height - 70), "@TheSovSniper | t.me/SovereignSniperBot", font=font_tiny, fill=(200, 200, 200))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

if __name__ == '__main__':
    buf = generate_pnl_image("PEPE/WETH", 450.00)
    with open("test_character_pnl.png", "wb") as f:
        f.write(buf.read())
    print("Character PnL generated.")
