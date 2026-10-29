from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'herramientas'))
import cv2 as cv
import numpy as np
from PIL import Image,ImageDraw,ImageFont
cv.setNumThreads(4)
files=sorted((ROOT/'originales').glob('*.JPG'))
data=np.load(ROOT/'alineacion.npz');Rs=data['R'].astype(np.float32);f=float(data['f']);k=float(data['k'])
def directions(w,h):
 lon=np.linspace(-np.pi,np.pi,w,endpoint=False,dtype=np.float32)
 lat=np.linspace(np.pi/2,-np.pi/2,h,dtype=np.float32)
 return np.stack(np.broadcast_arrays(np.sin(lon)[None,:]*np.cos(lat)[:,None],-np.sin(lat)[:,None],np.cos(lon)[None,:]*np.cos(lat)[:,None]),axis=-1)
def warp(src,R,dirs):
 v=dirs@R;z=v[:,:,2];xy=v[:,:,:2]/np.maximum(z[:,:,None],.00001);r2=np.sum(xy*xy,axis=2);xy*=(1+k*r2)[:,:,None]
 mx=(xy[:,:,0]*f+1000).astype(np.float32);my=(xy[:,:,1]*f+750).astype(np.float32)
 valid=(z>0)&(r2<2)&(mx>2)&(mx<1997)&(my>2)&(my<1497)
 return cv.remap(src,mx,my,cv.INTER_LINEAR),valid.astype(np.uint8)*255
sources=[cv.imdecode(np.frombuffer(p.read_bytes(),np.uint8),cv.IMREAD_COLOR) for p in files]
small=directions(1000,500);imgs=[];masks=[]
for src,R in zip(sources,Rs):
 im,ma=warp(src,R,small);imgs.append(im.astype(np.float32));masks.append(ma)
# Robust exposure ratios on overlap pixels, excluding clipped highlights and shadows.
rows=[];rhs=[]
grays=[cv.cvtColor(im,cv.COLOR_BGR2GRAY) for im in imgs]
for i in range(26):
 for j in range(i+1,26):
  ok=(masks[i]>0)&(masks[j]>0)&(grays[i]>30)&(grays[j]>30)&(grays[i]<220)&(grays[j]<220)
  if ok.sum()<500:continue
  diff=np.log(grays[j][ok]/grays[i][ok]);row=np.zeros(26);row[i]=1;row[j]=-1;rows.append(row);rhs.append(np.median(diff))
rows.append(np.ones(26));rhs.append(0)
gains=np.exp(np.linalg.lstsq(rows,rhs,rcond=None)[0]);gains=np.clip(gains,.8,1.25)
print('Compensacion de luz',gains.round(3).tolist(),flush=True)
imgs=[(im*g).astype(np.float32) for im,g in zip(imgs,gains)]
# Image-content seam placement avoids selecting straight polygon boundaries through people.
seamer=cv.detail_DpSeamFinder('COLOR_GRAD')
umasks=[cv.UMat(m) for m in masks]
result=seamer.find(imgs,[(0,0)]*26,umasks)
seams=[m.get() if hasattr(m,'get') else m for m in (result if result is not None else umasks)]
# Keep the moving visitor and her entire path from one original exposure.
ny=small[:,:,1];nx=(small[:,:,0]/np.maximum(ny,.001)/3.6+.5)*1400;nz=(small[:,:,2]/np.maximum(ny,.001)/3.6+.5)*1400
protect=(((nx-1030)/185)**2+((nz-475)/145)**2<1)&(ny>0)&(masks[22]>0)
for index in range(26):seams[index][protect]=255 if index==22 else 0
print('Uniones adaptadas al contenido',flush=True)
W,H=6000,3000;dirs=directions(W,H)
blender=cv.detail_MultiBandBlender();blender.setNumBands(7);blender.prepare((0,0,W,H))
coverage=np.zeros((H,W),np.uint8)
reference=np.zeros((H,W,3),np.float32);refweight=np.zeros((H,W),np.float32)
for i,(src,R,g,sm) in enumerate(zip(sources,Rs,gains,seams)):
 im,valid=warp(src,R,dirs)
 feather=np.minimum(cv.distanceTransform(valid,cv.DIST_L2,3)/250,1)**2
 reference+=im.astype(np.float32)*g*feather[:,:,None];refweight+=feather
 # A small overlap lets the multiband blend remove low-frequency exposure discontinuities.
 seam=cv.resize(cv.dilate(sm,np.ones((3,3),np.uint8)),(W,H),interpolation=cv.INTER_NEAREST)
 seam=cv.bitwise_and(seam,valid);coverage=cv.bitwise_or(coverage,valid)
 blender.feed(np.clip(im.astype(np.float32)*g,0,255).astype(np.int16),seam,(0,0))
 print('Fusion',i+1,flush=True)
out,_=blender.blend(None,None)
reference/=np.maximum(refweight[:,:,None],.001)
# Replace only broad illumination with a smoothly weighted reference. Fine detail and people remain from seam-selected photographs.
low=cv.resize(out.astype(np.float32),(1000,500),interpolation=cv.INTER_AREA)
ref=cv.resize(reference,(1000,500),interpolation=cv.INTER_AREA)
delta=cv.GaussianBlur(ref-low,(0,0),12)
out=np.clip(out.astype(np.float32)+cv.resize(delta,(W,H),interpolation=cv.INTER_LINEAR),0,255).astype(np.uint8);out[coverage==0]=(28,23,18)
im=Image.fromarray(cv.cvtColor(out,cv.COLOR_BGR2RGB));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',42)
for xx in [750,2250,3750,5250]:d.text((xx,350),'Zona superior no capturada',font=font,fill='#aebdc7',anchor='mm')
dest=ROOT/'revision-v2';dest.mkdir(exist_ok=True);p=dest/'Panorama-360.jpg';im.save(p,quality=94,subsampling=0)
old=(ROOT/'entrega/Panorama-360.jpg').read_bytes();start=old.find(b'http://ns.adobe.com/xap/1.0/\0');end=old.find(b'</x:xmpmeta>',start)+len(b'</x:xmpmeta>');payload=old[start:end];raw=p.read_bytes();p.write_bytes(raw[:2]+b'\xff\xe1'+(len(payload)+2).to_bytes(2,'big')+payload+raw[2:])
# Rectilinear nadir views permit direct comparison without equirectangular stretching.
for name,path in [('antes',ROOT/'entrega/Panorama-360.jpg'),('despues',p)]:
 source=cv.imdecode(np.frombuffer(path.read_bytes(),np.uint8),cv.IMREAD_COLOR)
 size=1400;v=np.linspace(-1.8,1.8,size,dtype=np.float32);xx,zz=np.meshgrid(v,v);yy=np.ones_like(xx);norm=np.sqrt(xx*xx+yy*yy+zz*zz)
 lon=np.arctan2(xx,zz);lat=np.arcsin(-yy/norm);mx=(lon/(2*np.pi)+.5)*W;my=(.5-lat/np.pi)*H
 view=cv.remap(source,mx,my,cv.INTER_LINEAR,borderMode=cv.BORDER_WRAP)
 Image.fromarray(cv.cvtColor(view,cv.COLOR_BGR2RGB)).save(dest/(name+'-centro.jpg'),quality=92)
im.resize((1800,900)).save(dest/'general.jpg')
print('LISTO',flush=True)


