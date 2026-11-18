import { useState } from 'react';
import { Play, Loader2, Satellite } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api, ApiError } from '@/services/api';
import { PAGE_ACCENT } from '@/lib/theme-colors';

const YEARS = Array.from({length:8},(_,i)=>2026-i).reverse();
export default function TimeMachine(){
 const [lat,setLat]=useState(31.634); const [lon,setLon]=useState(74.8723); const [year,setYear]=useState(2026); const [playing,setPlaying]=useState(false); const [error,setError]=useState<string|null>(null);
 const [scene,setScene]=useState<any>(null); const [loading,setLoading]=useState(false);
 const load=async(y:number)=>{setYear(y);setLoading(true);setError(null);try{const start=`${y}-01-01`,end=`${y}-12-31`;const r=await api.satelliteScenes(lat,lon,start,end,10);if(!r.scenes.length)throw new Error('No Sentinel-2 L2A acquisition found for this year.');setScene(r.scenes[0]);}catch(e){setError(e instanceof ApiError?e.message:e instanceof Error?e.message:'Could not load satellite scene.')}finally{setLoading(false)}};
 const play=async()=>{if(playing)return;setPlaying(true);for(const y of YEARS){await load(y);await new Promise(r=>setTimeout(r,900));}setPlaying(false)};
 return <div><PageHeader title="Earth Time Machine" subtitle="Real Sentinel-2 historical acquisitions — selected by location and year."/><div className="max-w-4xl space-y-5 p-6">
  <div className="grid gap-3 sm:grid-cols-2"><label className="text-xs">Latitude<input value={lat} onChange={e=>setLat(Number(e.target.value))} type="number" step="0.0001" className="mt-1 w-full rounded-lg border p-2" style={{background:'var(--surface)',borderColor:'var(--border)'}}/></label><label className="text-xs">Longitude<input value={lon} onChange={e=>setLon(Number(e.target.value))} type="number" step="0.0001" className="mt-1 w-full rounded-lg border p-2" style={{background:'var(--surface)',borderColor:'var(--border)'}}/></label></div>
  <div className="rounded-xl border p-4" style={{borderColor:'var(--border)',background:'var(--surface)'}}><div className="flex items-center justify-between"><span className="text-sm font-medium">Acquisition year: {year}</span><button onClick={play} disabled={playing} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs" style={{background:PAGE_ACCENT.timemachine,color:'#1c1330'}}>{playing?<Loader2 className="animate-spin" size={13}/>:<Play size={13}/>} Play Timeline</button></div><input className="mt-4 w-full" type="range" min={0} max={YEARS.length-1} value={YEARS.indexOf(year)} onChange={e=>load(YEARS[Number(e.target.value)])}/><div className="mt-1 flex justify-between text-[10px]">{YEARS.map(y=><span key={y}>{y}</span>)}</div></div>
  {error&&<div className="rounded-lg border p-3 text-sm" style={{borderColor:'var(--color-alert)',color:'var(--color-alert)'}}>{error}</div>}
  <div className="overflow-hidden rounded-xl border" style={{borderColor:'var(--border)',background:'var(--surface)'}}>{loading?<div className="flex aspect-video items-center justify-center"><Loader2 className="animate-spin"/></div>:scene?<img src={api.satelliteImageUrl(lat,lon,scene.datetime?.slice(0,10))} className="aspect-video w-full object-cover"/>:<div className="flex aspect-video items-center justify-center text-sm" style={{color:'var(--text-muted)'}}><Satellite size={18} className="mr-2"/>Choose a year to retrieve a real Sentinel-2 scene.</div>}</div>
  {scene&&<div className="grid gap-3 sm:grid-cols-3 text-xs"><div>Acquisition<br/><b>{scene.datetime}</b></div><div>Cloud cover<br/><b>{scene.cloud_cover ?? 'n/a'}%</b></div><div>Source<br/><b>Copernicus Sentinel-2 L2A</b></div></div>}
 </div></div>
}
