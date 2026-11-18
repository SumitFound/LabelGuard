from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[1]/'sample_images'; OUT.mkdir(exist_ok=True)
font_path='C:/Windows/Fonts/arial.ttf'
def font(size):
    try: return ImageFont.truetype(font_path,size)
    except OSError: return ImageFont.load_default()
def make(idx, compliant=True, tiny=False, nodate=False, nomrp=False):
    image=Image.new('RGB',(1000,700),'#fffdf4'); d=ImageDraw.Draw(image)
    d.rounded_rectangle((35,30,965,670),radius=30,outline='#1b6b4b',width=8)
    d.text((75,65),'SUNRISE FOODS',font=font(56),fill='#165c3e')
    d.text((75,150),'Product name: Premium Tea',font=font(34),fill='#222')
    d.text((75,220),'Manufactured by: Sunrise Foods, Pune, Maharashtra',font=font(27),fill='#222')
    d.text((75,280),'Net Quantity: 500 g',font=font(13 if tiny else 30),fill='#222')
    if not nodate: d.text((75,340),'Date of packing: 08/2026',font=font(28),fill='#222')
    if not nomrp: d.text((75,400),'MRP Rs. 120 inclusive of all taxes',font=font(28),fill='#222')
    d.text((75,460),'Consumer Care: help@example.in | 020-12345678',font=font(25),fill='#222')
    d.text((75,555),'Made in India',font=font(24),fill='#222')
    image.save(OUT/f'label_{idx}.png')
if __name__=='__main__':
    for i in range(1,4): make(i)
    make(4,False,nomrp=True); make(5,False,nodate=True); make(6,False,tiny=True)
