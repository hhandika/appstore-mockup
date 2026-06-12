from PIL import Image, ImageDraw, ImageFilter

def create_rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask

def apply_rounded_corners(image: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return image
    mask = create_rounded_mask(image.size, radius)
    rounded_image = image.copy()
    rounded_image.putalpha(mask)
    return rounded_image

def apply_color_border(image: Image.Image, border_size: int, color: str, radius: int) -> Image.Image:
    if border_size <= 0:
        return image
    
    new_width = image.width + border_size * 2
    new_height = image.height + border_size * 2
    
    background = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(background)
    outer_radius = radius + border_size if radius > 0 else 0
    draw.rounded_rectangle((0, 0, new_width, new_height), radius=outer_radius, fill=color)
    
    background.paste(image, (border_size, border_size), image)
    return background

def apply_glass_border(image: Image.Image, border_size: int, radius: int) -> Image.Image:
    if border_size <= 0:
        return image
        
    new_width = image.width + border_size * 2
    new_height = image.height + border_size * 2
    
    background = image.copy().resize((new_width, new_height))
    background = background.filter(ImageFilter.GaussianBlur(radius=border_size))
    background = background.convert("RGBA")
    
    overlay = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 64))
    background = Image.alpha_composite(background, overlay)
    
    outer_radius = radius + border_size if radius > 0 else 0
    mask = create_rounded_mask((new_width, new_height), outer_radius)
    background.putalpha(mask)
    
    background.paste(image, (border_size, border_size), image)
    return background
