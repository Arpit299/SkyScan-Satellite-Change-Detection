import argparse
import json
import math
from collections import deque
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
class SkyScan:
    def __init__(self,threshold=30,min_region=20,blur_radius=1):
        self.threshold=max(0,min(255,int(threshold)))
        self.min_region=max(1,int(min_region))
        self.blur_radius=max(0,int(blur_radius))
    def load(self,path):
        image=Image.open(path).convert("RGB")
        return image.filter(ImageFilter.GaussianBlur(self.blur_radius)) if self.blur_radius else image
    def normalize(self,a,b):
        if a.size==b.size:return a,b
        size=(max(a.width,b.width),max(a.height,b.height))
        return a.resize(size,Image.Resampling.BILINEAR),b.resize(size,Image.Resampling.BILINEAR)
    def diff_mask(self,a,b):
        mask=bytearray(a.width*a.height)
        changed=0
        scale=math.sqrt(3)
        ap=a.load()
        bp=b.load()
        for y in range(a.height):
            for x in range(a.width):
                c=ap[x,y]
                d=bp[x,y]
                distance=math.sqrt((c[0]-d[0])**2+(c[1]-d[1])**2+(c[2]-d[2])**2)/scale
                if distance>=self.threshold:
                    mask[y*a.width+x]=1
                    changed+=1
        return mask,changed
    def components(self,mask,width,height):
        seen=bytearray(len(mask))
        regions=[]
        for start in range(len(mask)):
            if not mask[start] or seen[start]:continue
            q=deque([start])
            seen[start]=1
            pixels=[]
            while q:
                idx=q.popleft()
                pixels.append(idx)
                x=idx%width
                y=idx//width
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx=x+dx
                    ny=y+dy
                    if 0<=nx<width and 0<=ny<height:
                        ni=ny*width+nx
                        if mask[ni] and not seen[ni]:
                            seen[ni]=1
                            q.append(ni)
            if len(pixels)>=self.min_region:
                xs=[p%width for p in pixels]
                ys=[p//width for p in pixels]
                regions.append({"id":len(regions)+1,"pixels":len(pixels),"x":min(xs),"y":min(ys),"width":max(xs)-min(xs)+1,"height":max(ys)-min(ys)+1,"area_percent":round(len(pixels)/(width*height)*100,4)})
        return sorted(regions,key=lambda x:x["pixels"],reverse=True)
    def classify(self,image,regions):
        px=image.load()
        result=[]
        for region in regions:
            samples=[]
            step=max(1,int(max(region["width"],region["height"])/20))
            for y in range(region["y"],region["y"]+region["height"],step):
                for x in range(region["x"],region["x"]+region["width"],step):samples.append(px[x,y])
            r=sum(p[0] for p in samples)/len(samples) if samples else 0
            g=sum(p[1] for p in samples)/len(samples) if samples else 0
            b=sum(p[2] for p in samples)/len(samples) if samples else 0
            if g>r*1.15 and g>b*1.05:label="vegetation"
            elif b>r*1.15 and b>g*1.05:label="water"
            elif r+g+b>620:label="bright_surface"
            elif r+g+b<180:label="dark_surface"
            else:label="built_or_bare"
            item=dict(region)
            item["type"]=label
            result.append(item)
        return result
    def outputs(self,mask,width,height,base,regions,outdir):
        outdir=Path(outdir)
        outdir.mkdir(parents=True,exist_ok=True)
        change_map=outdir/"change_map.png"
        overlay=outdir/"change_overlay.png"
        image=Image.new("RGB",(width,height),(0,0,0))
        pix=image.load()
        for i,v in enumerate(mask):
            if v:pix[i%width,i//width]=(255,0,0)
        image.save(change_map)
        marked=base.copy()
        draw=ImageDraw.Draw(marked)
        for region in regions:
            x0=region["x"]
            y0=region["y"]
            x1=x0+region["width"]-1
            y1=y0+region["height"]-1
            draw.rectangle((x0,y0,x1,y1),outline=(255,0,0),width=2)
            draw.text((x0,max(0,y0-12)),str(region["id"]),fill=(255,0,0))
        marked.save(overlay)
        return str(change_map.resolve()),str(overlay.resolve())
    def analyze(self,before_path,after_path,outdir):
        before=self.load(before_path)
        after=self.load(after_path)
        before,after=self.normalize(before,after)
        mask,changed=self.diff_mask(before,after)
        regions=self.classify(after,self.components(mask,before.width,before.height),)
        change_map,overlay=self.outputs(mask,before.width,before.height,after,regions,outdir)
        total=before.width*before.height
        return {"before":str(Path(before_path).resolve()),"after":str(Path(after_path).resolve()),"width":before.width,"height":before.height,"threshold":self.threshold,"minimum_region_pixels":self.min_region,"changed_pixels":changed,"total_pixels":total,"changed_area_percent":round(changed/total*100,4) if total else 0,"regions":regions,"outputs":{"change_map":change_map,"change_overlay":overlay}}
def create_test_images(before_path,after_path):
    before=Image.new("RGB",(200,140),(85,125,65))
    after=before.copy()
    a=ImageDraw.Draw(before)
    a.rectangle((20,20,70,60),fill=(70,110,55))
    a.rectangle((90,25,150,70),fill=(90,90,90))
    a.rectangle((35,90,85,125),fill=(45,90,140))
    b=ImageDraw.Draw(after)
    b.rectangle((90,25,150,70),fill=(140,140,140))
    b.rectangle((145,80,185,125),fill=(180,165,120))
    b.rectangle((35,90,85,125),fill=(45,90,140))
    before.save(before_path)
    after.save(after_path)
def main():
    parser=argparse.ArgumentParser(prog="skyscan")
    parser.add_argument("before",nargs="?")
    parser.add_argument("after",nargs="?")
    parser.add_argument("--threshold",type=int,default=30)
    parser.add_argument("--min-region",type=int,default=20)
    parser.add_argument("--blur",type=int,default=1)
    parser.add_argument("--output",default="skyscan_output")
    parser.add_argument("--json",dest="json_path",default="")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    try:
        if args.self_test or not args.before or not args.after:
            root=Path.cwd()/"skyscan_self_test"
            root.mkdir(parents=True,exist_ok=True)
            before=root/"before.png"
            after=root/"after.png"
            create_test_images(before,after)
        else:
            before=Path(args.before).expanduser().resolve()
            after=Path(args.after).expanduser().resolve()
            if not before.exists() or not after.exists():raise FileNotFoundError("One or both images do not exist.")
        report=SkyScan(args.threshold,args.min_region,args.blur).analyze(before,after,args.output)
        print("SKYSCAN SATELLITE CHANGE DETECTION")
        print("="*60)
        print(f"Image Size: {report['width']}x{report['height']}")
        print(f"Changed Pixels: {report['changed_pixels']}")
        print(f"Changed Area: {report['changed_area_percent']}%")
        print(f"Change Regions: {len(report['regions'])}")
        print("\nREGIONS")
        for region in report["regions"]:print(f"#{region['id']} {region['type']} | pixels={region['pixels']} | bbox=({region['x']},{region['y']},{region['width']},{region['height']}) | area={region['area_percent']}%")
        print("\nOUTPUTS")
        print(report["outputs"]["change_map"])
        print(report["outputs"]["change_overlay"])
        if args.json_path:
            out=Path(args.json_path).expanduser().resolve()
            out.write_text(json.dumps(report,indent=2),encoding="utf-8")
            print(f"Saved: {out}")
        if args.self_test:
            assert report["changed_pixels"]>0
            assert len(report["regions"])>=2
            assert Path(report["outputs"]["change_map"]).exists()
            assert Path(report["outputs"]["change_overlay"]).exists()
            print("\nRESULT: PASS")
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
if __name__=="__main__":main()
