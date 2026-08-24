import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_path = "Roboto-Bold.ttf"
    return ImageFont.truetype(font_path, size)

def var_hacker(token_name: str, percentage: float) -> Image:
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    neon_green = (57, 255, 20)
    
    # Border
    draw.rectangle([10, 10, width-10, height-10], outline=neon_green, width=3)
    
    # Fonts
    font_title = get_font(30)
    font_token = get_font(50)
    font_pnl = get_font(140)
    font_footer = get_font(25)
    
    draw.text((40, 40), "[sys.stdout] SOVEREIGN_SNIPER.exe", font=font_title, fill=neon_green)
    draw.text((40, 120), f"> TARGET_ACQUIRED: {token_name}", font=font_token, fill=(200, 255, 200))
    draw.text((40, 200), f"+{percentage:.2f}%", font=font_pnl, fill=neon_green)
    draw.text((40, height - 60), "ROOT@THESOVSNIPER:~$ _", font=font_footer, fill=neon_green)
    
    return img

def var_institutional(token_name: str, percentage: float) -> Image:
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color=(248, 250, 252)) # Very light gray/white
    draw = ImageDraw.Draw(img)
    
    dark_slate = (15, 23, 42)
    accent_blue = (37, 99, 235)
    profit_green = (22, 163, 74)
    
    # Clean top bar
    draw.rectangle([0, 0, width, 15], fill=accent_blue)
    
    font_title = get_font(35)
    font_token = get_font(55)
    font_pnl = get_font(130)
    font_footer = get_font(25)
    
    draw.text((50, 50), "SOVEREIGN INSTITUTIONAL", font=font_title, fill=accent_blue)
    draw.text((50, 130), f"Asset: {token_name}", font=font_token, fill=dark_slate)
    draw.text((50, 210), f"+{percentage:.2f}%", font=font_pnl, fill=profit_green)
    
    draw.line([(50, height - 80), (width - 50, height - 80)], fill=(203, 213, 225), width=2)
    draw.text((50, height - 60), "@TheSovSniper | Verified Execution", font=font_footer, fill=(100, 116, 139))
    
    return img

def var_neon(token_name: str, percentage: float) -> Image:
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color=(9, 9, 11)) # Zinc 950
    draw = ImageDraw.Draw(img)
    
    magenta = (217, 70, 239)
    cyan = (34, 211, 238)
    
    # Scanlines
    for y in range(0, height, 4):
        draw.line([(0, y), (width, y)], fill=(24, 24, 27), width=1)
        
    font_title = get_font(40)
    font_token = get_font(60)
    font_pnl = get_font(130)
    font_footer = get_font(30)
    
    # Title with glitch effect
    draw.text((52, 40), "SOVEREIGN SNIPER", font=font_title, fill=magenta)
    draw.text((50, 42), "SOVEREIGN SNIPER", font=font_title, fill=cyan)
    
    draw.text((50, 120), token_name, font=font_token, fill=(255, 255, 255))
    
    # PnL
    draw.text((50, 210), f"+{percentage:.2f}%", font=font_pnl, fill=(52, 211, 153))
    
    draw.rectangle([50, height-70, 350, height-30], fill=magenta)
    draw.text((60, height - 65), "@TheSovSniper", font=font_footer, fill=(0,0,0))
    
    return img

if __name__ == '__main__':
    var_hacker("BASE/WETH", 500.0).save("var1.png")
    var_institutional("BASE/WETH", 500.0).save("var2.png")
    var_neon("BASE/WETH", 500.0).save("var3.png")
    print("Variations generated.")
