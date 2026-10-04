"""Combine actual Garden character renders into a labelled inspection sheet."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
NAMES=('rasta_grower','corporate_boss','robot','chef','blonde_lady','party_woman','skeleton')
LABELS=('Rasta grower','Corporate boss','Helper robot','Chef','Blonde neighbor','Party neighbor','Skeleton')

def font(size):
    candidates=('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    for name in candidates:
        if Path(name).is_file(): return ImageFont.truetype(name,size)
    return ImageFont.load_default()

def main():
    canvas=Image.new('RGB',(1280,1000),'#e7e9d8'); draw=ImageDraw.Draw(canvas)
    draw.text((24,22),'GREENBOX / GARDEN CHIBI',font=font(32),fill='#263c33')
    draw.text((24,67),'Original voxel cast - shared Garden palette - actual 3D source renders',font=font(20),fill='#536457')
    qa=json.loads((ROOT/'pack_validation.json').read_text(encoding='utf-8'))
    stats={r['asset']:r for r in qa['assets']}
    for i,(name,label) in enumerate(zip(NAMES,LABELS)):
        x=16+(i%4)*316; y=115+(i//4)*418
        preview=Image.open(ROOT/name/(name+'_preview.png')).convert('RGB')
        preview=preview.resize((296,370),Image.Resampling.LANCZOS)
        canvas.paste(preview,(x,y))
        draw.text((x+2,y+374),label,font=font(18),fill='#263c33')
        draw.text((x+2,y+397),f"{stats[name]['glb']['triangles']} triangles",font=font(14),fill='#536457')
    x=16+3*316; y=115+418
    draw.text((x+15,y+60),'Large cubic heads',font=font(20),fill='#263c33')
    draw.text((x+15,y+96),'Tiny bodies / short legs',font=font(18),fill='#536457')
    draw.text((x+15,y+136),'Six movable rigid parts',font=font(18),fill='#536457')
    draw.text((x+15,y+176),'0.05 m occupied cubes',font=font(18),fill='#536457')
    draw.text((x+15,y+230),'Editable VOX + GLB + BLEND',font=font(17),fill='#536457')
    draw.text((24,966),f"Seven characters / {qa['total_filled_voxels']:,} occupied cubes / {qa['total_triangles']:,} surface triangles",font=font(17),fill='#263c33')
    canvas.save(ROOT/'garden_cast_contact_sheet.png')

if __name__=='__main__': main()
