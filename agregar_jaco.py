from pathlib import Path
import numpy as np,json,re
p=Path('Proyecto/sitio/stands.js');s=p.read_text(encoding='utf-8');d=np.array([json.loads(x) for x in re.findall(r'direction:(\[[^]]+\])',s)])
# Correspondencias de los botones visibles en la captura.
ids=[0,1,12,3,2,4];pts=np.array([[259,413],[461,383],[586,537],[761,307],[914,280],[818,483]])
a=d[ids];best=None
for f in np.linspace(35,100,1301):
 r=np.column_stack(((pts[:,0]-532)/421*np.tan(np.radians(f/2)),(421-pts[:,1])/421*np.tan(np.radians(f/2)),np.ones(len(pts))));r/=np.linalg.norm(r,axis=1)[:,None]
 u,_,v=np.linalg.svd(r.T@a);R=u@np.diag([1,1,np.linalg.det(u@v)])@v;err=np.linalg.norm(r@R-a)
 if best is None or err<best[0]:best=(err,f,R)
err,f,R=best;ray=np.array([(627-532)/421*np.tan(np.radians(f/2)),(421-327)/421*np.tan(np.radians(f/2)),1]);ray/=np.linalg.norm(ray);direction=(ray@R).tolist()
assert "name:'CTP de Jacó'" not in s
entry="{name:'CTP de Jacó',direction:"+json.dumps(direction)+",photo:'stands/ctp-jaco.jpg'},"
p.write_text(s.replace('const stands=[','const stands=['+entry,1),encoding='utf-8')
p=Path('Proyecto/sitio/index.html');p.write_text(p.read_text(encoding='utf-8').replace('stands.js?v=19','stands.js?v=20'),encoding='utf-8')
assert Path('Proyecto/sitio/stands/ctp-jaco.jpg').stat().st_size>0
print('Foto vinculada. Total:',len(d)+1,'estands. Error angular de ajuste:',round(float(err),4))
