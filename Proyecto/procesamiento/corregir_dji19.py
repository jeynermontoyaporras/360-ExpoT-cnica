from pathlib import Path
import sys
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r/'herramientas'))
import cv2 as cv,numpy as np
from PIL import Image
cv.setNumThreads(4)
a=np.load(r/'alineacion.npz'); R=a['R'][18].astype(np.float32); f=float(a['f']); k=float(a['k'])
read=lambda p:cv.imdecode(np.frombuffer(p.read_bytes(),np.uint8),1)
base=read(r/'revision-v2/Panorama-360.jpg');src=read(r/'originales/DJI_0019.JPG');h,w=base.shape[:2]
lon=np.linspace(-np.pi,np.pi,w,endpoint=False,dtype=np.float32);lat=np.linspace(np.pi/2,-np.pi/2,h,dtype=np.float32)
d=np.stack(np.broadcast_arrays(np.sin(lon)[None,:]*np.cos(lat)[:,None],-np.sin(lat)[:,None],np.cos(lon)[None,:]*np.cos(lat)[:,None]),-1)
v=d@R; z=v[:,:,2];xy=v[:,:,:2]/np.maximum(z[:,:,None],.00001);rr=np.sum(xy*xy,2);xy*= (1+k*rr)[:,:,None];mx=xy[:,:,0]*f+1000;my=xy[:,:,1]*f+750
valid=(z>0)&(rr<2)&(mx>30)&(mx<1970)&(my>500)&(my<1470)
# Replace the whole lower scene from a single exposure, feathering only its perimeter.
edge=np.minimum.reduce([mx-30,1970-mx,my-500,1470-my]);alpha=np.clip(edge/110,0,1)*valid
warped=cv.remap(src,mx.astype('float32'),my.astype('float32'),cv.INTER_LINEAR)
# Match broad illumination without disturbing original photographic detail.
safe=(alpha>.95)&(warped.mean(2)>35)&(warped.mean(2)<220)
gain=np.median(base[safe].astype(float)/np.maximum(warped[safe],1),axis=0);gain=np.clip(gain,.85,1.2)
patch=np.clip(warped.astype(float)*gain,0,255)
out=np.uint8(np.clip(base*(1-alpha[:,:,None])+patch*alpha[:,:,None],0,255))
dest=r/'revision-v3';dest.mkdir(exist_ok=True)
Image.fromarray(cv.cvtColor(out,cv.COLOR_BGR2RGB)).save(dest/'Panorama-360.jpg',quality=94,subsampling=0)
# Compare in the exact original camera projection.
yy,xx=np.mgrid[0:1500,0:2000].astype('float32'); xx=(xx-1000)/f;yy=(yy-750)/f; fac=1+k*(xx*xx+yy*yy); rays=np.stack([xx/fac,yy/fac,np.ones_like(xx)],-1)@R.T;rays/=np.linalg.norm(rays,axis=2)[:,:,None]
u=(np.arctan2(rays[:,:,0],rays[:,:,2])/(2*np.pi)+.5)*w;vv=(.5+np.arcsin(rays[:,:,1])/np.pi)*h
for name,img in [('antes',base),('despues',out)]:
 view=cv.remap(img,u.astype('float32'),vv.astype('float32'),cv.INTER_LINEAR,borderMode=cv.BORDER_WRAP)
 Image.fromarray(cv.cvtColor(view[650:1450,450:1950],cv.COLOR_BGR2RGB)).resize((1125,600)).save(dest/(name+'.jpg'))
print('Patched pixels',int((alpha>0).sum()),'gain',gain)
