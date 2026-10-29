import numpy as np,json,re,itertools
from pathlib import Path
s=Path('Proyecto/sitio/stands.js').read_text(encoding='utf-8')
d=np.array([json.loads(x) for x in re.findall(r'direction:(\[[^]]+\])',s)])
pts=np.array([[992,263],[660,611],[1072,570]])
q=np.column_stack(((pts[:,0]-537)/375,(375-pts[:,1])/375,np.ones(3)))
best=[]
for f in np.linspace(35,100,651):
 r=q.copy();r[:,:2]*=np.tan(np.radians(f/2));r/=np.linalg.norm(r,axis=1)[:,None]
 for ids in itertools.permutations(range(len(d)),3):
  a=d[list(ids)];err=np.sum((a@a.T-r@r.T)**2)
  if len(best)==0 or err<best[0][0]:best=[(err,f,ids,r)]
e,f,ids,r=best[0];u,_,v=np.linalg.svd(r.T@d[list(ids)]);R=u@v
mark=np.array([(486-537)/375,(375-329)/375,1.]);mark[:2]*=np.tan(np.radians(f/2));mark/=np.linalg.norm(mark);direction=mark@R
print('fit',e,'fov',f,'indices',ids,'direction',direction.tolist(),'det',np.linalg.det(R))
Path('Proyecto/posicion-nuevo-stand.json').write_text(json.dumps({'error':e,'fov':f,'markers':ids,'direction':direction.tolist()}))
