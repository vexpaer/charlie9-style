"""Build a two-row README gallery, preserving complete example images."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'reports' / 'style-tests'
ROWS = (
    ('batch-02/06-07-montage.png', '03-creature-encounter.png'),
    ('batch-02/03-lakeside-glow.png', 'basketball-court-comparison.png'),
)

def main():
    # 同行等高、宽度按原始比例分配，两行总宽度相同，不裁切。
    width, gap = 1600, 12
    strips = []
    for names in ROWS:
        pictures = [Image.open(EXAMPLES / name).convert('RGB') for name in names]
        ratios = [picture.width / picture.height for picture in pictures]
        height = round((width - gap) / sum(ratios))
        first_width = round(height * ratios[0])
        strip = Image.new('RGB', (width, height), 'white')
        left = 0
        for picture, target_width in zip(pictures, (first_width, width - gap - first_width)):
            strip.paste(picture.resize((target_width, height), Image.Resampling.LANCZOS), (left, 0))
            left += target_width + gap
        strips.append(strip)
    gallery = Image.new('RGB', (width, sum(strip.height for strip in strips) + gap), 'white')
    top = 0
    for strip in strips:
        gallery.paste(strip, (0, top))
        top += strip.height + gap
    destination = EXAMPLES / 'readme-gallery.jpg'
    gallery.save(destination, quality=94, optimize=True)
    print(f'{destination}: {gallery.width} x {gallery.height}')

if __name__ == '__main__':
    main()
