#!/usr/bin/env python3
"""Renderer 16:9 terpisah dari mesin Shorts KlikTahu.
Render preview: python longform/render_longform.py --preview
Render video tanpa VO: python longform/render_longform.py --render
"""
import argparse,json,os,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.dirname(os.path.abspath(__file__))
EP=os.path.join(ROOT,os.environ.get('LONGFORM_EP','ep01_besar_tapi_miskin'))
W,H=1920,1080
FONT=os.path.join(os.path.dirname(ROOT),'fonts')
def f(name,size): return ImageFont.truetype(os.path.join(FONT,name),size)
def wrap(d,text,ft,maxw):
 out=[]
 for para in text.split('\n'):
  cur=''
  for w in para.split():
   t=(cur+' '+w).strip()
   if d.textbbox((0,0),t,font=ft)[2]<=maxw: cur=t
   else: out.append(cur);cur=w
  if cur: out.append(cur)
 return out
def frame(sc,idx,total=9):
 accent=sc.get('accent','#F2B84B'); col=tuple(bytes.fromhex(accent[1:])); im=Image.new('RGB',(W,H),(13,18,28)); d=ImageDraw.Draw(im)
 # cinematic grid and glow
 for x in range(-200,W+300,180): d.line((x,0,x+H,H),fill=(20,29,43),width=2)
 for y in range(80,H,140): d.line((0,y,W,y),fill=(18,27,40),width=2)
 d.ellipse((1250,-210,2050,590),fill=tuple(min(255,int(v*.22+25)) for v in col))
 d.rectangle((0,0,W,8),fill=col)
 d.text((92,60),'KLIKT AHU  /  LONG-FORM',font=f('Poppins-SemiBold.ttf',28),fill=(180,192,208))
 d.text((W-380,62),f'{idx:02d}  /  {total:02d}',font=f('Poppins-SemiBold.ttf',26),fill=col)
 # visual motif: connected nodes
 cx,cy=1500,600
 for j in range(5):
  x=cx+(j-2)*125; y=cy+(j%2)*100-50
  d.line((cx,cy,x,y),fill=tuple(min(255,int(v*.7+40)) for v in col),width=5)
  d.ellipse((x-28,y-28,x+28,y+28),fill=col)
 d.ellipse((cx-42,cy-42,cx+42,cy+42),outline=col,width=8)
 # text block
 title=sc['title']; ft=f('Poppins-Bold.ttf',76)
 lines=wrap(d,title,ft,1050); y=280
 for line in lines:
  d.text((100,y),line,font=ft,fill=(245,247,250),stroke_width=1); y+=92
 d.rounded_rectangle((100,y+35,650,y+93),radius=29,fill=col)
 d.text((130,y+46),'PENJELASAN UTAMA',font=f('Poppins-SemiBold.ttf',25),fill=(13,18,28))
 body=wrap(d,sc['body'],f('Poppins-Regular.ttf',34),920); y+=155
 for line in body[:4]: d.text((100,y),line,font=f('Poppins-Regular.ttf',34),fill=(181,194,210)); y+=52
 d.text((100,970),'Indonesia · Singapura · institusi · kesempatan',font=f('Poppins-Regular.ttf',24),fill=(120,140,160))
 return im

def main():
 global EP
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--episode',default=os.environ.get('LONGFORM_EP','ep01_besar_tapi_miskin'));a=ap.parse_args()
 EP=os.path.join(ROOT,a.episode)
 if not os.path.isdir(EP): raise SystemExit(f"episode tidak ditemukan: {EP}")
 data=json.load(open(os.path.join(EP,'content.json'))); out=os.path.join(EP,'preview');os.makedirs(out,exist_ok=True)
 ims=[]
 for i,sc in enumerate(data['scenes'],1):
  p=os.path.join(out,f'{i:02d}_{sc["id"]}.png'); im=frame(sc,i,len(data['scenes'])); im.save(p); ims.append(im)
 # contact sheet always, lightweight QC deliverable
 rows=(len(ims)+1)//2
 sheet=Image.new('RGB',(960,270*max(1,rows)),(8,12,20))
 for i,im in enumerate(ims): sheet.paste(im.resize((480,270)),((i%2)*480,(i//2)*270))
 sheet.save(os.path.join(EP,'preview_sheet.jpg'),quality=92)
 if a.render:
  # Scene cards become a clean animatic; replace with mixed VO in final pipeline.
  concat=os.path.join(EP,'preview','frames.txt'); fps=30
  with open(concat,'w') as h:
   for i,sc in enumerate(data['scenes'],1):
    card=os.path.abspath(os.path.join(out, f"{i:02d}_{sc['id']}.png"))
    h.write(f"file '{card}'\nduration 4\n")
   last=os.path.abspath(os.path.join(out, f"{len(data['scenes']):02d}_{data['scenes'][-1]['id']}.png"))
   h.write(f"file '{last}'\n")
  out_name=data.get('out_name') or os.path.basename(os.path.normpath(EP))
  dest=os.path.join(EP,f'{out_name}_animatic.mp4')
  subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-vf','fps=30,format=yuv420p','-c:v','libx264','-preset','medium','-crf','19',dest],check=True)
  print(dest)
 print('preview:',os.path.join(EP,'preview_sheet.jpg'))
if __name__=='__main__': main()
