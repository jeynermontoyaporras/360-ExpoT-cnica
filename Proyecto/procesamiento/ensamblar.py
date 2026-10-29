from pathlib import Path
import sys,re,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'herramientas'))
import cv2 as cv
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from PIL import Image,ImageDraw,ImageFont
cv.setNumThreads(4)
files=sorted((ROOT/'originales').glob('*.JPG'))
def matrix(y,p):
 y,p=np.radians([y,p]); r=np.array([np.cos(y),0,-np.sin(y)]); u=np.array([-np.sin(y)*np.sin(p),np.cos(p),-np.cos(y)*np.sin(p)]); f=np.array([np.sin(y)*np.cos(p),np.sin(p),np.cos(y)*np.cos(p)])
 return np.diag([1,-1,1])@np.stack([r,-u,f],axis=1)
Rs=[]
for path in files:
 s=path.read_bytes().decode('latin1')
 y,p=[float(re.search(k+'="([^"]+)"',s).group(1)) for k in ['GimbalYawDegree','GimbalPitchDegree']]
 Rs.append(matrix(y,p))
Rs=np.array(Rs); base=Rotation.from_matrix(Rs).as_rotvec()
cache=ROOT/'alineacion.npz'
if not cache.exists():
 sift=cv.SIFT_create(nfeatures=4500)
 feats=[]
 for path in files:
  im=cv.resize(cv.imdecode(np.frombuffer(path.read_bytes(),np.uint8),cv.IMREAD_COLOR),(1000,750)); kp,des=sift.detectAndCompute(cv.cvtColor(im,cv.COLOR_BGR2GRAY),None)
  feats.append((np.array([k.pt for k in kp]),des))
 print('Caracteristicas detectadas en 26 fotos',flush=True)
 pairs=[]; ai=[]; aj=[]; pi=[]; pj=[]
 matcher=cv.BFMatcher()
 for i in range(26):
  for j in range(i+1,26):
   if np.dot(Rs[i,:,2],Rs[j,:,2])<np.cos(np.radians(85)):continue
   matches=matcher.knnMatch(feats[i][1],feats[j][1],k=2)
   good=[m for m,n in matches if m.distance<.70*n.distance]
   if len(good)<15:continue
   a=np.array([feats[i][0][m.queryIdx] for m in good]); b=np.array([feats[j][0][m.trainIdx] for m in good])
   def rays(x,R):
    v=np.column_stack([(x[:,0]-500)/693.4,(x[:,1]-375)/693.4,np.ones(len(x))]); v=v@R.T; return v/np.linalg.norm(v,axis=1)[:,None]
   ok=np.linalg.norm(rays(a,Rs[i])-rays(b,Rs[j]),axis=1)<.10
   a,b=a[ok],b[ok]
   if len(a)<12:continue
   _,mask=cv.findHomography(a,b,cv.RANSAC,2.5)
   if mask is None:continue
   a,b=a[mask.ravel()>0],b[mask.ravel()>0]
   if len(a)<12:continue
   take=np.linspace(0,len(a)-1,min(150,len(a))).astype(int); a,b=a[take],b[take]
   ai.extend([i]*len(a));aj.extend([j]*len(a));pi.extend(a);pj.extend(b);pairs.append((i+1,j+1,len(a)))
 ai,aj=np.array(ai),np.array(aj);pi,pj=np.array(pi),np.array(pj)
 print('Pares y puntos:',len(pairs),len(ai),flush=True)
 def residual(x):
  rr=Rotation.from_rotvec(x[:78].reshape(26,3)).as_matrix();f=x[78];k=x[79]
  def ray(p,idx):
   xy=(p-[500,375])/f; xy=xy/(1+k*np.sum(xy*xy,axis=1)[:,None]);v=np.column_stack([xy,np.ones(len(xy))]);v=np.einsum('nij,nj->ni',rr[idx],v);return v/np.linalg.norm(v,axis=1)[:,None]
  e=(ray(pi,ai)-ray(pj,aj)).ravel()*700
  prior=(x[:78]-base.ravel())*3
  return np.r_[e,prior,(x[78]-693.4)*.008,x[79]*5]
 x=np.r_[base.ravel(),693.4,0.]
 opt=least_squares(residual,x,loss='soft_l1',f_scale=1.5,max_nfev=70,diff_step=1e-5)
 Rs=Rotation.from_rotvec(opt.x[:78].reshape(26,3)).as_matrix();f=opt.x[78]*2;k=opt.x[79]
 np.savez(cache,R=Rs,f=f,k=k)
 print('Alineado. Focal:',f,'Distorsion:',k,'Error mediano:',float(np.median(abs(residual(opt.x)[:len(ai)*3]))),flush=True)
 (ROOT/'informe-alineacion.json').write_text(json.dumps({'imagenes':26,'pares':pairs,'puntos':len(ai),'focal_px':f,'distorsion':k,'error_mediano_px':float(np.median(abs(residual(opt.x)[:len(ai)*3])))},indent=2))
else:
 data=np.load(cache);Rs,f,k=data['R'],float(data['f']),float(data['k'])
W=6000;H=3000
lon=np.linspace(-np.pi,np.pi,W,endpoint=False,dtype=np.float32)
lat=np.linspace(np.pi/2,-np.pi/2,H,dtype=np.float32)
dirs=np.stack(np.broadcast_arrays(np.sin(lon)[None,:]*np.cos(lat)[:,None],-np.sin(lat)[:,None],np.cos(lon)[None,:]*np.cos(lat)[:,None]),axis=-1)
def maps(R):
 v=dirs@R; z=v[:,:,2];xy=v[:,:,:2]/np.maximum(z[:,:,None],.00001);r2=np.sum(xy*xy,axis=2);xy*= (1+k*r2)[:,:,None]
 mx=(xy[:,:,0]*f+1000).astype(np.float32);my=(xy[:,:,1]*f+750).astype(np.float32)
 score=np.minimum(1-abs(mx-1000)/1000,1-abs(my-750)/750);score[(z<=0)|(score<=0)|(r2>2)]=-1
 return mx,my,score
best=np.full((H,W),-1,np.float32);owner=np.full((H,W),255,np.uint8)
for i,R in enumerate(Rs):
 _,_,score=maps(R); take=score>best;owner[take]=i;best[take]=score[take]
print('Cobertura calculada',flush=True)
# Narrow feather blends avoid large ghosted regions; selected source is closest to its frame center.
acc=np.zeros((H,W,3),np.float32);weight=np.zeros((H,W),np.float32)
for i,(path,R) in enumerate(zip(files,Rs)):
 mx,my,score=maps(R);mask=(owner==i).astype(np.float32);mask=cv.GaussianBlur(mask,(0,0),2.5);mask[score<0]=0
 img=cv.remap(cv.imdecode(np.frombuffer(path.read_bytes(),np.uint8),cv.IMREAD_COLOR),mx,my,cv.INTER_LINEAR,borderMode=cv.BORDER_CONSTANT)
 acc+=img*mask[:,:,None];weight+=mask
 print('Proyectada',i+1,flush=True)
out=np.clip(acc/np.maximum(weight[:,:,None],1e-6),0,255).astype(np.uint8)
out[weight<.001]=(28,23,18)
out=cv.cvtColor(out,cv.COLOR_BGR2RGB)
im=Image.fromarray(out)
d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',42)
for xx in [750,2250,3750,5250]:d.text((xx,350),'Zona superior no capturada',font=font,fill='#aebdc7',anchor='mm')
dest=ROOT/'entrega';dest.mkdir(exist_ok=True)
im.save(dest/'Panorama-360.jpg',quality=94,subsampling=0)
# Standard GPano XMP makes compatible viewers recognize this as a full spherical canvas.
p=dest/'Panorama-360.jpg';raw=p.read_bytes()
xmp=f'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description xmlns:GPano="http://ns.google.com/photos/1.0/panorama/" GPano:ProjectionType="equirectangular" GPano:UsePanoramaViewer="True" GPano:FullPanoWidthPixels="{W}" GPano:FullPanoHeightPixels="{H}" GPano:CroppedAreaImageWidthPixels="{W}" GPano:CroppedAreaImageHeightPixels="{H}" GPano:CroppedAreaLeftPixels="0" GPano:CroppedAreaTopPixels="0" GPano:PoseHeadingDegrees="0" GPano:InitialViewHeadingDegrees="80" GPano:InitialViewPitchDegrees="-20"/></rdf:RDF></x:xmpmeta>'
payload=b'http://ns.adobe.com/xap/1.0/\0'+xmp.encode();p.write_bytes(raw[:2]+b'\xff\xe1'+(len(payload)+2).to_bytes(2,'big')+payload+raw[2:])
im.resize((1800,900)).save(ROOT/'revision.jpg',quality=90)
print('LISTO',str(p),flush=True)



