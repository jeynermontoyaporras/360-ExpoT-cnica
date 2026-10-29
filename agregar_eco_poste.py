from pathlib import Path
import numpy as np,json,re
p=Path('Proyecto/sitio/stands.js');s=p.read_text(encoding='utf-8');d=np.array([json.loads(x) for x in re.findall(r'direction:(\[[^]]+\])',s)])
pts=np.array([[636,184],[803,307],[728,527]]);a=d[[1,2,13]];best=None
for f in np.linspace(35,100,1301):
 r=np.column_stack(((pts[:,0]-512.5)/403*np.tan(np.radians(f/2)),(403-pts[:,1])/403*np.tan(np.radians(f/2)),np.ones(3)));r/=np.linalg.norm(r,axis=1)[:,None]
 u,_,v=np.linalg.svd(r.T@a);R=u@np.diag([1,1,np.linalg.det(u@v)])@v;err=np.linalg.norm(r@R-a)
 if best is None or err<best[0]:best=(err,f,R)
err,f,R=best;ray=np.array([(510-512.5)/403*np.tan(np.radians(f/2)),(403-312)/403*np.tan(np.radians(f/2)),1]);ray/=np.linalg.norm(ray);direction=(ray@R).tolist()
assert "name:'Eco Poste CR'" not in s
entry="{name:'Eco Poste CR',direction:"+json.dumps(direction)+",photo:'stands/eco-poste-cr.jpg'},"
p.write_text(s.replace('const stands=[','const stands=['+entry,1),encoding='utf-8')
p=Path('Proyecto/sitio/index.html');p.write_text(p.read_text(encoding='utf-8').replace('stands.js?v=20','stands.js?v=21'),encoding='utf-8')
assert Path('Proyecto/sitio/stands/eco-poste-cr.jpg').stat().st_size>0
print('15 estands. Ajuste:',round(float(err),4))
