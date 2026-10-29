import numpy as np,json,re
from pathlib import Path
s=Path('Proyecto/sitio/stands.js').read_text(encoding='utf-8');d=np.array([json.loads(x) for x in re.findall(r'direction:(\[[^]]+\])',s)])
a=d[[0,11]];target=np.array([[676.,298.],[671.,516.]])
def project(v):
 yaw,pitch,fov=v;cy,sy=np.cos(yaw),np.sin(yaw);cp,sp=np.cos(pitch),np.sin(pitch);x,y,z=a.T;ax=x*cy-z*sy;az=x*sy+z*cy;dy=y*cp-az*sp;dz=y*sp+az*cp;t=np.tan(fov/2);return np.column_stack((501+358.5*ax/dz/t,358.5-358.5*dy/dz/t))
best=None
for yaw in np.linspace(-1,1,7):
 v=np.array([yaw,-.7,1.]);
 for i in range(60):
  r=(project(v)-target).ravel();J=np.column_stack([((project(v+np.eye(3)[j]*1e-5)-project(v))/1e-5).ravel() for j in range(3)]);step=np.linalg.lstsq(J,r,rcond=None)[0];v-=np.clip(step,-.1,.1)
 err=np.linalg.norm(project(v)-target)
 if .3<v[2]<2 and (best is None or err<best[0]):best=(err,v)
err,(yaw,pitch,fov)=best
ray=np.array([(516-501)/358.5*np.tan(fov/2),(358.5-240)/358.5*np.tan(fov/2),1]);ray/=np.linalg.norm(ray);x,y,z=ray;ay=y*np.cos(pitch)+z*np.sin(pitch);az=-y*np.sin(pitch)+z*np.cos(pitch);direction=[x*np.cos(yaw)+az*np.sin(yaw),ay,-x*np.sin(yaw)+az*np.cos(yaw)]
entry="{name:'Intexconexión',direction:"+json.dumps(direction)+",photos:['stands/intexconexion-1.jpg','stands/intexconexion-2.jpg']},"
assert "name:'Intexconexión'" not in s
Path('Proyecto/sitio/stands.js').write_text(s.replace('const stands=[','const stands=['+entry,1),encoding='utf-8')
p=Path('Proyecto/sitio/index.html');p.write_text(p.read_text(encoding='utf-8').replace('stands.js?v=18','stands.js?v=19'),encoding='utf-8')
print('Ajuste en píxeles:',round(err,2),'dirección:',direction)
