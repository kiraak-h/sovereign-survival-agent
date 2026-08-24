import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_path = "Roboto-Bold.ttf"
    return ImageFont.truetype(font_path, size)

def var_final(token_name: str, percentage: float) -> Image:
    width, height = 700, 900
    img = Image.new('RGB', (width, height), color=(10, 10, 15))
    draw = ImageDraw.Draw(img)
    
    green = (34, 197, 94)
    red = (239, 68, 68)
    gold = (250, 204, 21)
    cyan = (6, 182, 212)
    
    font_large = get_font(140)
    font_med = get_font(80)
    font_small = get_font(40)
    font_tiny = get_font(25)
    
    # Background pattern
    for i in range(0, 1600, 20):
        draw.line([(i, 0), (0, i)], fill=(20, 20, 25), width=2)
        
    # Paste Watermark Logo (Center, Low Opacity)
    logo_path = 'core/assets/logo.jpg'
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert('RGBA')
        # Resize logo for watermark
        wm_size = 500
        wm_logo = logo.resize((wm_size, wm_size))
        # Create alpha mask for watermark
        alpha = wm_logo.split()[3]
        alpha = alpha.point(lambda p: p * 0.1) # 10% opacity
        wm_logo.putalpha(alpha)
        # Paste watermark in center
        img.paste(wm_logo, (int((width-wm_size)/2), int((height-wm_size)/2)), wm_logo)
        
        # Paste crisp logo in top right
        small_size = 100
        small_logo = logo.resize((small_size, small_size))
        # Need to handle JPG transparency (JPG has no alpha)
        # We convert to RGBA above, but JPG has solid background.
        # It's a dark logo, so it might look fine as a square, or we draw a circular mask.
        mask = Image.new('L', (small_size, small_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, small_size, small_size), fill=255)
        
        img.paste(small_logo, (width - small_size - 40, 40), mask)

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
    
    return img

if __name__ == '__main__':
    var_final("PEPE/WETH", 450.00).save("var_final.png")
    print("Final var generated.")
