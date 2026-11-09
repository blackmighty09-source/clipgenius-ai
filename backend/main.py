from pathlib import Path
import shutil, subprocess, uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE=Path(__file__).resolve().parent
FRONT=BASE.parent/'frontend'
OUT=BASE/'outputs'; UP=BASE/'uploads'
OUT.mkdir(exist_ok=True); UP.mkdir(exist_ok=True)
app=FastAPI(title='ClipGenius AI')
app.mount('/static',StaticFiles(directory=FRONT),name='static')

def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode: raise RuntimeError(p.stderr[-1800:])
 return p.stdout
@app.get('/',response_class=HTMLResponse)
def home(): return (FRONT/'index.html').read_text()
@app.post('/api/create')
async def create(video:UploadFile=File(...), seconds:int=Form(35), count:int=Form(3), ratio:str=Form('9:16'), quality:str=Form('1080p')):
 if Path(video.filename or '').suffix.lower() not in {'.mp4','.mov','.mkv','.webm','.m4v'}: raise HTTPException(400,'Upload MP4, MOV, MKV, WEBM or M4V.')
 if not 5<=seconds<=60 or not 1<=count<=10: raise HTTPException(400,'Choose 5–60 seconds and 1–10 clips.')
 dims={'9:16':(720,1280),'16:9':(1280,720),'1:1':(1080,1080),'4:5':(864,1080)}
 if ratio not in dims or quality not in ('720p','1080p'): raise HTTPException(400,'Invalid output settings.')
 jid=uuid.uuid4().hex[:10]; src=UP/(jid+Path(video.filename).suffix.lower())
 with src.open('wb') as f: shutil.copyfileobj(video.file,f)
 try:
  dur=float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(src)]).strip())
  n=min(count,max(1,int(dur//seconds))) if dur>=seconds else 1
  starts=[0.0] if n==1 and dur<=seconds else ([max(0,(dur-seconds)/2)] if n==1 else [max(0,dur-seconds)*i/(n-1) for i in range(n)])
  w,h=dims[ratio]
  if quality=='720p': w=round(w*720/h); h=720; w-=w%2
  else: h=1080; w=round(w*1080/dims[ratio][1]); w-=w%2
  clips=[]
  for i,s in enumerate(starts,1):
   name=f'{jid}-clip-{i}.mp4'; dest=OUT/name
   vf=f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1'
   run(['ffmpeg','-y','-ss',str(s),'-i',str(src),'-t',str(min(seconds,dur-s)),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-movflags','+faststart',str(dest)])
   clips.append({'name':name,'url':'/download/'+name,'start':round(s,1),'duration':round(min(seconds,dur-s),1)})
  return {'clips':clips,'note':'Prototype uses evenly spaced segments, not AI-ranked highlights yet.'}
 except FileNotFoundError: raise HTTPException(500,'Install FFmpeg and ffprobe, then restart the app.')
 except Exception as e: raise HTTPException(500,str(e)[:400])
 finally: src.unlink(missing_ok=True)
@app.get('/download/{name}')
def download(name:str):
 p=OUT/Path(name).name
 if not p.is_file() or p.suffix!='.mp4': raise HTTPException(404,'Clip not found')
 return FileResponse(p,media_type='video/mp4',filename=p.name)
