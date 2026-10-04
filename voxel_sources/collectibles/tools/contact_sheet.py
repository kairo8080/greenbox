"""A contact sheet from actual Blender geometry renders, no synthetic artwork."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]

def font(size):
 for name in ('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
  if Path(name).is_file(): return ImageFont.truetype(name,size)
 return ImageFont.load_default()

def main():
 catalog=json.loads((ROOT/'assets.json').read_text(encoding='utf-8')); qa=json.loads((ROOT/'pack_validation.json').read_text(encoding='utf-8'))
 canvas=Image.new('RGB',(1248,1770),'#e7e9d8'); draw=ImageDraw.Draw(canvas)
 draw.text((28,20),'GREENBOX / COLLECTIBLES',font=font(32),fill='#263c33')
 draw.text((28,65),'Original occupied cubes - Garden palette - actual 3D geometry renders',font=font(20),fill='#536457')
 for i,item in enumerate(catalog['assets']):
  x=24+(i%3)*408; y=108+(i//3)*540
  image=Image.open(ROOT/item['preview']).convert('RGB').resize((384,480),Image.Resampling.LANCZOS)
  canvas.paste(image,(x,y))
  draw.text((x+2,y+485),item['label'],font=font(19),fill='#263c33')
  draw.text((x+2,y+511),f"{item['triangles']} triangles / {item['rarity']}",font=font(15),fill='#536457')
 draw.text((28,1740),f"Nine assets / {qa['total_filled_voxels']:,} occupied cubes / {qa['total_triangles']:,} exposed-surface triangles",font=font(17),fill='#263c33')
 canvas.save(ROOT/'collectibles_contact_sheet.png')

if __name__=='__main__': main()
