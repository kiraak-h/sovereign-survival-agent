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
    # Colors
    bg_color = (15, 23, 42) # Dark blue/gray (Slate 900)
    border_color = (6, 182, 212) # Cyan 500
    text_white = (248, 250, 252) # Slate 50
    green_color = (34, 197, 94) # Green 500
    red_color = (239, 68, 68) # Red 500
    
    # Dimensions
    width, height = 800, 450
    
    # Create image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw border
    border_width = 8
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=border_width)
    
    # Fonts
    font_title = get_font(40)
    font_token = get_font(60)
    font_pnl = get_font(120)
    font_footer = get_font(30)
    
    # Title
    draw.text((40, 40), "SOVEREIGN SNIPER", font=font_title, fill=border_color)
    
    # Token
    draw.text((40, 120), f"Token: {token_name}", font=font_token, fill=text_white)
    
    # PnL
    pnl_str = f"+{percentage:.2f}%" if percentage >= 0 else f"{percentage:.2f}%"
    pnl_color = green_color if percentage >= 0 else red_color
    draw.text((40, 200), pnl_str, font=font_pnl, fill=pnl_color)
    
    # Footer
    footer_text = "@TheSovSniper | Autonomous MEV Execution"
    draw.text((40, height - 80), footer_text, font=font_footer, fill=(148, 163, 184))
    
    # Ref link (Right aligned)
    if referrer_id:
        ref_text = f"Ref: ref_{referrer_id}"
        bbox = draw.textbbox((0,0), ref_text, font=font_footer)
        draw.text((width - bbox[2] - 40, height - 80), ref_text, font=font_footer, fill=border_color)
    
    # Save to buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

if __name__ == '__main__':
    buf = generate_pnl_image("PEPE/WETH", 420.69, "849201")
    with open("test_pnl.png", "wb") as f:
        f.write(buf.read())
    print("Test image generated.")
