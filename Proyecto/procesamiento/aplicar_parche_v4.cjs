const fs=require('fs'),path=require('path');
const sharp=require('C:/Users/jeyne/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{
 const r=path.resolve('panorama-expo-360'),d=path.join(r,'revision-v4');
 const generated='C:/Users/jeyne/.codex/generated_images/01a14c5d-b815-7ed0-8bd2-727d8c49ca9c/exec-d83304e7-eb43-4e5c-8e29-55a2d79c7e59.png';
 fs.copyFileSync(generated,path.join(d,'edicion-generada.png'));
 const img=await sharp(generated).resize(800,800).removeAlpha().raw().toBuffer();
 const base=await sharp(path.join(r,'revision-v3/Panorama-360.jpg')).removeAlpha().raw().toBuffer({resolveWithObject:true});
 const svg=Buffer.from(`<svg width="800" height="800"><path d="M645 359 L680 365 L701 389 L701 417 L714 446 L696 460 L660 463 L627 451 L632 438 L608 432 L575 441 L530 445 L479 443 L450 435 L451 422 L478 414 L529 412 L579 407 L610 398 L636 391 Z" fill="white"/></svg>`);
 const mask=await sharp(svg).blur(2).ensureAlpha().raw().toBuffer();
 const ratios=[[],[],[]]; for(let y=390;y<490;y++)for(let x=430;x<745;x++){if(mask[(y*800+x)*4+3]>0)continue; const b=((y+2217)*6000+x+7)*3,s=(y*800+x)*3;for(let c=0;c<3;c++)if(img[s+c]>15)ratios[c].push(base.data[b+c]/img[s+c]);} const gains=ratios.map(a=>a.sort((x,y)=>x-y)[Math.floor(a.length/2)]); console.log({gains}); const out=Buffer.from(base.data);let count=0;
 for(let y=345;y<475;y++)for(let x=440;x<725;x++){
 const alpha=mask[(y*800+x)*4+3]/255;if(!alpha)continue;
 const b=((y+2217)*6000+x+7)*3,s=(y*800+x)*3;for(let c=0;c<3;c++)out[b+c]=Math.round(base.data[b+c]*(1-alpha)+img[s+c]*gains[c]*alpha);count++;
 }
 await sharp(out,{raw:base.info}).webp({lossless:true,effort:5}).toFile(path.join(d,'Panorama-360.webp'));
 await sharp(out,{raw:base.info}).extract({left:7,top:2217,width:800,height:780}).png().toFile(path.join(d,'verificacion.png'));
 const check=await sharp(path.join(d,'Panorama-360.webp')).raw().toBuffer();let diffs=0;for(let i=0;i<out.length;i++)if(check[i]!==out[i])diffs++;
 console.log(JSON.stringify({modifiedAreaPixels:count,losslessDifferences:diffs,size:fs.statSync(path.join(d,'Panorama-360.webp')).size}));
})();

