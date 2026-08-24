import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_path = "Roboto-Bold.ttf"
    return ImageFont.truetype(font_path, size)

def var_trojan(token_name: str, percentage: float) -> Image:
    # Trojan uses vertical or square cards for mobile dominance
    width, height = 700, 900
    img = Image.new('RGB', (width, height), color=(10, 10, 15))
    draw = ImageDraw.Draw(img)
    
    green = (34, 197, 94)
    red = (239, 68, 68)
    gold = (250, 204, 21)
    
    font_large = get_font(140)
    font_med = get_font(80)
    font_small = get_font(40)
    font_tiny = get_font(25)
    
    # Background pattern (subtle diagonal lines)
    for i in range(0, 1600, 20):
        draw.line([(i, 0), (0, i)], fill=(20, 20, 25), width=2)
        
    # Top Logo/Name
    draw.text((40, 40), "SOVEREIGN SNIPER", font=font_small, fill=(255, 255, 255))
    draw.line([(40, 90), (450, 90)], fill=gold, width=3)
    
    # Token
    draw.text((40, 150), token_name, font=font_med, fill=(255, 255, 255))
    
    # PnL
    color = green if percentage >= 0 else red
    sign = "+" if percentage >= 0 else ""
    draw.text((40, 300), f"{sign}{percentage:.2f}%", font=font_large, fill=color)
    
    # Multiplier
    multiplier = (percentage / 100) + 1
    draw.text((40, 480), f"{multiplier:.2f}x", font=font_med, fill=gold)
    
    # Fake Entry/Current (since we don't track it yet)
    draw.text((40, 650), "Entry:   PROTECTED", font=font_small, fill=(150, 150, 150))
    draw.text((40, 710), "Current: PROTECTED", font=font_small, fill=(150, 150, 150))
    
    # Footer
    draw.rectangle([0, height-100, width, height], fill=(15, 15, 20))
    draw.text((40, height - 70), "@TheSovSniper | t.me/SovereignSniperBot", font=font_tiny, fill=(200, 200, 200))
    
    return img

if __name__ == '__main__':
    var_trojan("PEPE/WETH", 450.00).save("var_trojan.png")
    print("Trojan var generated.")
