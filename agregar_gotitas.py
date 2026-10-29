from pathlib import Path
import numpy as np,json,re,itertools
p=Path('Proyecto/sitio/stands.js');s=p.read_text(encoding='utf-8');d=np.array([json.loads(x) for x in re.findall(r'direction:(\[[^]]+\])',s)])
pts=np.array([[245,468],[374,607],[857,611]]);comb=np.array([(i,j,0) for i,j in itertools.permutations(range(1,len(d)),2)]);aa=d[comb];grams=aa@aa.transpose(0,2,1);best=None
for f in np.linspace(35,100,1301):
 r=np.column_stack(((pts[:,0]-541)/400.5*np.tan(np.radians(f/2)),(400.5-pts[:,1])/400.5*np.tan(np.radians(f/2)),np.ones(3)));r/=np.linalg.norm(r,axis=1)[:,None]
 errs=np.sum((grams-r@r.T)**2,axis=(1,2))
 for k in np.argsort(errs)[:3]:
  u,_,v=np.linalg.svd(r.T@aa[k]);R=u@v
  if np.linalg.det(R)<0:continue
  err=np.linalg.norm(r@R-aa[k])
  if best is None or err<best[0]:best=(err,f,R,comb[k])
err,f,R,ids=best;ray=np.array([(632-541)/400.5*np.tan(np.radians(f/2)),(400.5-416)/400.5*np.tan(np.radians(f/2)),1]);ray/=np.linalg.norm(ray);direction=(ray@R).tolist()
assert "name:'Gotitas'" not in s
entry="{name:'Gotitas',direction:"+json.dumps(direction)+",photo:'stands/gotitas.jpg'},"
p.write_text(s.replace('const stands=[','const stands=['+entry,1),encoding='utf-8')
p=Path('Proyecto/sitio/index.html');p.write_text(p.read_text(encoding='utf-8').replace('stands.js?v=21','stands.js?v=22'),encoding='utf-8')
assert Path('Proyecto/sitio/stands/gotitas.jpg').stat().st_size>0
print('16 estands. Ajuste:',round(float(err),4),'Referencias:',ids.tolist())
