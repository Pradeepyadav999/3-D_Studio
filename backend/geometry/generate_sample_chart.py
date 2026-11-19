"""Generate a realistic synthetic size chart image for testing OCR."""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_sample_chart(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Image dimensions
    w, h = 1000, 550
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Use default bitmap font or load standard font
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
        cell_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        cell_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Draw Title and Subtitle
    draw.text((50, 30), "MEN'S REGULAR FIT T-SHIRT SIZE CHART", fill=(20, 20, 30), font=title_font)
    draw.text((50, 75), "All garment measurements are in centimeters (cm)", fill=(100, 100, 110), font=sub_font)

    # Table coordinates
    start_x = 50
    start_y = 120
    row_height = 55
    col_widths = [220, 130, 130, 130, 130, 130]

    headers = ["Measurement", "S", "M", "L", "XL", "XXL"]
    rows = [
        ["Chest", "96", "101", "107", "112", "118"],
        ["Shoulder", "40", "43", "46", "48", "50"],
        ["Length", "66", "68", "71", "73", "75"],
        ["Sleeve", "18", "19", "20", "21", "22"],
    ]

    # Draw Header background
    draw.rectangle([start_x, start_y, start_x + sum(col_widths), start_y + row_height], fill=(240, 242, 246))

    # Draw Header text
    curr_x = start_x
    for i, h_text in enumerate(headers):
        draw.text((curr_x + 18, start_y + 16), h_text, fill=(30, 41, 59), font=header_font)
        curr_x += col_widths[i]

    # Draw Row backgrounds and values
    curr_y = start_y + row_height
    for r_idx, row in enumerate(rows):
        bg_col = (255, 255, 255) if r_idx % 2 == 0 else (248, 250, 252)
        draw.rectangle([start_x, curr_y, start_x + sum(col_widths), curr_y + row_height], fill=bg_col)
        
        curr_x = start_x
        for c_idx, val in enumerate(row):
            font = header_font if c_idx == 0 else cell_font
            fill = (15, 23, 42) if c_idx == 0 else (51, 65, 85)
            draw.text((curr_x + 18, curr_y + 16), val, fill=fill, font=font)
            curr_x += col_widths[c_idx]
        curr_y += row_height

    # Draw table borders
    table_w = sum(col_widths)
    table_h = row_height * (len(rows) + 1)
    draw.rectangle([start_x, start_y, start_x + table_w, start_y + table_h], outline=(203, 213, 225), width=2)
    
    # Horizontal grid lines
    for r in range(1, len(rows) + 1):
        y_line = start_y + r * row_height
        draw.line([(start_x, y_line), (start_x + table_w, y_line)], fill=(226, 232, 240), width=1)

    # Vertical grid lines
    line_x = start_x
    for w_col in col_widths[:-1]:
        line_x += w_col
        draw.line([(line_x, start_y), (line_x, start_y + table_h)], fill=(226, 232, 240), width=1)

    # Footnote
    draw.text((50, curr_y + 25), "* Standalone garment measurements. Measured flat across garment.", fill=(148, 163, 184), font=sub_font)

    img.save(output_path, "PNG")
    print(f"Sample size chart saved to: {output_path}")

if __name__ == "__main__":
    generate_sample_chart("storage/sample_size_chart.png")
    generate_sample_chart("storage/uploads/sample_chart.png")
