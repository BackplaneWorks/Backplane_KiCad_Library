#!/usr/bin/env python3
"""Compose native KiCad plots into an overview and full visual footprint index."""
from pathlib import Path
import io,json,math
from PIL import Image,ImageDraw,ImageFont
import cairosvg
ROOT=Path(__file__).resolve().parents[1]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def raster(path,width=1200,color=None,palette=None):
    data=path.read_text()
    if color:data=data.replace('#000000',color)
    for before,after in (palette or {}).items():data=data.replace(before,after)
    data=data.replace('<svg\n','<svg shape-rendering="crispEdges"\n',1)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data.encode(),output_width=width))).convert('RGBA')

def overview():
    layers=ROOT/'verification/catalogue-layers'
    sample=raster(layers/'library_catalogue-F_Cu.svg',2400,'#d4ad55')
    board=Image.new('RGBA',sample.size,'#234c3e')
    board.alpha_composite(sample)
    board.alpha_composite(raster(layers/'library_catalogue-F_Silkscreen.svg',2400,'#f5f2d9'))
    # Substrate openings are visualized separately; they are mask removal,
    # not copper pads. Cu overwrites gold face/pads after mask rendering.
    mask=raster(layers/'library_catalogue-F_Mask.svg',2400,'#b9ae7e')
    base=Image.new('RGBA',sample.size,'#234c3e');base.alpha_composite(mask)
    base.alpha_composite(sample)
    base.alpha_composite(raster(layers/'library_catalogue-F_Silkscreen.svg',2400,'#f5f2d9'))
    result=Image.new('RGB',(2400,base.height+140),'#eeeee5')
    result.paste(base,(0,140))
    d=ImageDraw.Draw(result)
    d.text((35,20),'BACKPLANE KICAD LIBRARY',font=font(38,True),fill='#17271d')
    d.text((35,77),'199 footprints · 5 libraries · native KiCad layer composite · illustrative colours',font=font(25),fill='#17271d')
    result.save(ROOT/'previews/catalogue.png')

def index():
    entries=[]
    for lib in sorted((ROOT/'libraries').glob('*.pretty')):
        for footprint in sorted(lib.glob('*.kicad_mod')):
            name=footprint.stem
            if 'MountingHole' in lib.stem:
                svg=ROOT/'verification/holes/footprint-load'/f'{name}.svg'
            elif 'Shoggoth' in lib.stem:
                svg=ROOT/'verification/shoggoth/footprint-load'/f'{name}.svg'
            else:
                density=lib.stem.rsplit('_',1)[1].lower()
                svg=ROOT/'verification/passives/svg'/density/f'{name}.svg'
            assert svg.exists(),svg
            entries.append((lib.stem,name,svg))
    assert len(entries)==199
    columns=5;cw=460;ch=220;header=105
    out=Image.new('RGB',(columns*cw,header+math.ceil(len(entries)/columns)*ch),'#f1f0e8')
    d=ImageDraw.Draw(out)
    d.text((24,15),'BACKPLANE / ALL 199 FOOTPRINTS',font=font(30,True),fill='#17271d')
    d.text((24,60),'Native KiCad footprint plots · individual cells fit to view, not to common scale',font=font(20),fill='#17271d')
    for i,(lib,name,svg) in enumerate(entries):
        x=(i%columns)*cw;y=header+(i//columns)*ch
        d.rectangle((x+7,y+7,x+cw-7,y+ch-7),fill='white',outline='#a6aa9e',width=1)
        d.text((x+15,y+14),lib.replace('Backplane_',''),font=font(16,True),fill='#173b2c')
        # Two short lines retain complete identifiers instead of truncating them.
        chunks=[name[j:j+43] for j in range(0,len(name),43)]
        for j,s in enumerate(chunks):d.text((x+15,y+38+j*18),s,font=font(14),fill='#17271d')
        palette={'#F2EDA1':'#263829','#AFAFAF':'#62665e'}
        if 'Shoggoth' in lib:palette.update({'#D864FF':'#d6ad45','#C83434':'#d6ad45'})
        art=raster(svg,900,palette=palette)
        # Trim plot whitespace (including invisible SVG backdrop), keep geometry.
        bounds=art.getbbox()
        if bounds:art=art.crop(bounds)
        art.thumbnail((cw-40,115),Image.Resampling.LANCZOS)
        out.paste(art,(x+(cw-art.width)//2,y+89+(115-art.height)//2),art)
    out.save(ROOT/'previews/footprint-index.png')

if __name__=='__main__':overview();index()
