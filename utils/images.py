import io
from PIL import Image, ImageDraw, ImageFont

def generate_stats_card(username: str, balance: int, rank: int, gems: int, kills: int, xp: int) -> bytes:
    """
    Renders a high-quality customizable statistics card using Pillow.
    Returns the image data in bytes (PNG).
    """
    width, height = 600, 350
    image = Image.new("RGBA", (width, height), (30, 30, 45, 255))
    draw = ImageDraw.Draw(image)

    # Draw card border
    draw.rounded_rectangle(
        [(15, 15), (width - 15, height - 15)],
        radius=15,
        fill=(18, 18, 28, 255),
        outline=(114, 137, 218, 255),
        width=3
    )

    try:
        title_font = ImageFont.load_default(size=26)
        normal_font = ImageFont.load_default(size=18)
    except Exception:
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()

    # Draw Title Header
    draw.text((40, 35), "USER STATS CARD", fill=(255, 255, 255, 255), font=title_font)
    draw.line([(40, 75), (width - 40, 75)], fill=(114, 137, 218, 255), width=2)

    # Column 1 Information
    draw.text((50, 100), f"Name: {username}", fill=(240, 240, 255, 255), font=normal_font)
    draw.text((50, 150), f"Coins / ZEXIS: {balance}", fill=(255, 215, 0, 255), font=normal_font)
    draw.text((50, 200), f"Gems: {gems}", fill=(0, 255, 255, 255), font=normal_font)

    # Column 2 Information
    draw.text((320, 100), f"Global Rank: #{rank}", fill=(255, 100, 100, 255), font=normal_font)
    draw.text((320, 150), f"Kill Count: {kills}", fill=(255, 0, 0, 255), font=normal_font)
    draw.text((320, 200), f"Experience (XP): {xp}", fill=(100, 255, 100, 255), font=normal_font)

    # Progress/Visual Accent Bar at the bottom
    progress_ratio = min(1.0, xp / 10000.0) if xp > 0 else 0
    bar_width = int((width - 100) * progress_ratio)
    draw.text((50, 260), "Level Progress:", fill=(200, 200, 200, 255), font=normal_font)
    draw.rounded_rectangle(
        [(50, 290), (width - 50, 310)],
        radius=5,
        fill=(50, 50, 70, 255)
    )
    if bar_width > 0:
        draw.rounded_rectangle(
            [(50, 290), (50 + bar_width, 310)],
            radius=5,
            fill=(114, 137, 218, 255)
        )

    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.read()

def generate_welcome_card(group_name: str) -> bytes:
    """
    Renders a customizable group welcome banner using Pillow.
    """
    width, height = 650, 250
    image = Image.new("RGBA", (width, height), (20, 25, 35, 255))
    draw = ImageDraw.Draw(image)

    # Draw border with pink/purple accent
    draw.rounded_rectangle(
        [(10, 10), (width - 10, height - 10)],
        radius=12,
        fill=(13, 15, 23, 255),
        outline=(255, 105, 180, 255),
        width=3
    )

    try:
        large_font = ImageFont.load_default(size=30)
        sub_font = ImageFont.load_default(size=20)
    except Exception:
        large_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.text((40, 40), "🌸 WELCOME TO OUR GROUP! 🌸", fill=(255, 105, 180, 255), font=large_font)
    draw.text((40, 100), f"Guild/Group: {group_name}", fill=(255, 255, 255, 255), font=sub_font)
    draw.text((40, 140), "Hope you have an amazing stay!", fill=(200, 200, 255, 255), font=sub_font)
    draw.text((40, 180), "Play games, catch waifus, and make friends!", fill=(100, 255, 100, 255), font=sub_font)

    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.read()

def generate_spawn_card(waifu_name: str, rarity: str, price: int) -> bytes:
    """
    Renders a stunning customized waifu character card for active auto-spawns.
    """
    width, height = 400, 500
    image = Image.new("RGBA", (width, height), (35, 35, 45, 255))
    draw = ImageDraw.Draw(image)

    # Border color depends on Rarity
    colors = {
        "Common": (180, 180, 180, 255),
        "Rare": (30, 144, 255, 255),
        "Epic": (138, 43, 226, 255),
        "Legendary": (255, 215, 0, 255),
        "Velora": (255, 20, 147, 255)
    }
    rarity_color = colors.get(rarity, (255, 255, 255, 255))

    # Outer border
    draw.rounded_rectangle(
        [(15, 15), (width - 15, height - 15)],
        radius=20,
        fill=(15, 15, 20, 255),
        outline=rarity_color,
        width=4
    )

    try:
        title_font = ImageFont.load_default(size=24)
        subtitle_font = ImageFont.load_default(size=18)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # Draw Waifu Illustration Box
    draw.rectangle(
        [(35, 35), (width - 35, 280)],
        fill=(40, 40, 55, 255),
        outline=(100, 100, 100, 255),
        width=1
    )
    # Simple placeholder text inside drawing box
    draw.text((120, 140), "[ CHARACTER ART ]", fill=(150, 150, 150, 255), font=subtitle_font)

    # Info footer
    draw.text((40, 310), waifu_name.upper(), fill=(255, 255, 255, 255), font=title_font)
    draw.text((40, 360), f"Rarity: {rarity}", fill=rarity_color, font=subtitle_font)
    draw.text((40, 400), f"Base Price: {price} Coins", fill=(255, 215, 0, 255), font=subtitle_font)
    draw.text((40, 440), "Type /grasp to capture!", fill=(0, 255, 127, 255), font=subtitle_font)

    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output.read()
