import numpy as np
from scipy import ndimage
d = dict(np.load('/home/claude/pe/med/terrain.npz'))
topo, lat, lon, med = d['topo'].copy(), d['lat'], d['lon'], d['med']
LON, LAT = np.meshgrid(lon, lat)
# carve the Strait of Sicily so its sill matches the real ~430 m (10-arcmin grid smooths it to ~90 m)
for f in np.linspace(0, 1, 500):
    lo = 10.5 + (16.5 - 10.5) * f; la = 38.2 + (34.8 - 38.2) * f
    i = np.argmin(abs(lat - la)); j = np.argmin(abs(lon - lo))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if med[i+di, j+dj]:
                topo[i+di, j+dj] = min(topo[i+di, j+dj], -430.0)
def land_path(a, b):
    ia=(np.argmin(abs(lat-a[1])),np.argmin(abs(lon-a[0]))); ib=(np.argmin(abs(lat-b[1])),np.argmin(abs(lon-b[0])))
    for L in np.arange(0,-3000,-5):
        lab,_=ndimage.label(topo>=L)
        if lab[ia]==lab[ib] and lab[ia]>0: return L
print("Tunisia-Sicily land bridge at level", land_path((10.6,36.6),(13.5,37.6)))
# re-run drying model on fixed grid
cell=1/6; area=(111.32*cell)*(111.32*cell*np.cos(np.radians(LAT)))
def vol_area(h):
    dz=np.clip(h-topo,0,None)*med; return (dz*area).sum()/1000.0,(area*(med&(topo<h))).sum()
V0,A0=vol_area(0.0)
hs=np.linspace(0,topo[med].min(),1200); VA=np.array([vol_area(h) for h in hs])
E,R=1.35,60.0; y,h,V=0.0,0.0,V0; yrs=[0.0]; lev=[0.0]
while y<3000:
    A=np.interp(-h,-hs,VA[:,1]); V=max(V-(E*A/1000-R),0); h=float(np.interp(V,VA[::-1,0],hs[::-1])); y+=1; yrs.append(y); lev.append(h)
yrs=np.array(yrs); lev=np.array(lev)
# scale so that 90% of the volume is gone at year 1,100 (literature: ~1,000 years)
vl=np.interp(lev,hs[::-1],VA[::-1,0])/V0
y90=yrs[np.argmax(vl<0.1)]; S=1100/y90; yrs_s=yrs*S
print("V0 km3",round(V0),"area",round(A0),"scale",round(S,3))
for L in (-22,-100,-430,-1000,-2000):
    print(f"level {L}: year {yrs_s[np.argmax(lev<=L)]:.0f}")
for Y in (10,50,100,200,500,1000,1100,1500):
    print(f"year {Y}: level {np.interp(Y,yrs_s,lev):.0f} m, volume left {np.interp(Y,yrs_s,vl)*100:.0f}%")
print("global sea level rise m:", V0/361e6*1000)
np.savez('terrain2.npz', topo=topo, lat=lat, lon=lon, med=med, yrs=yrs_s, levels=lev, vleft=vl)
