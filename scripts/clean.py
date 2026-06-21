import pandas as pd, numpy as np, json, warnings, h3
from collections import Counter
warnings.filterwarnings('ignore')

RAW = 'violations.csv'
df = pd.read_csv(RAW)
n0 = len(df)

# ---------- DATA QUALITY PROFILE ----------
print("="*70); print("DATA QUALITY PROFILE"); print("="*70)
print(f"rows={len(df):,}  cols={df.shape[1]}")
prof = pd.DataFrame({
    'dtype': df.dtypes.astype(str),
    'null_%': (df.isna().mean()*100).round(1),
    'n_unique': df.nunique(),
})
prof['unique_%'] = (prof['n_unique']/len(df)*100).round(2)
print(prof.to_string())

# ---------- TIME: parse + IST ----------
df['created_utc'] = pd.to_datetime(df['created_datetime'], utc=True, errors='coerce')
df['modified_utc'] = pd.to_datetime(df['modified_datetime'], utc=True, errors='coerce')
df = df.dropna(subset=['created_utc']).copy()
df['created_ist'] = df['created_utc'].dt.tz_convert('Asia/Kolkata')
df['hour'] = df['created_ist'].dt.hour
df['dow']  = df['created_ist'].dt.dayofweek            # 0=Mon
df['dow_name'] = df['created_ist'].dt.day_name()
df['date'] = df['created_ist'].dt.date
df['month'] = df['created_ist'].dt.to_period('M').astype(str)
df['is_weekend'] = df['dow'].isin([5,6])
def tod(h):
    if h<6:  return 'night'
    if h<10: return 'morning'
    if h<17: return 'midday'
    if h<21: return 'evening'
    return 'late'
df['time_of_day'] = df['hour'].map(tod)
# peak (IST): AM 8-11, PM 17-21
df['is_am_peak'] = df['hour'].between(8,10)
df['is_pm_peak'] = df['hour'].between(17,20)
df['is_peak'] = df['is_am_peak'] | df['is_pm_peak']
# diurnal exposure weight (proxy for road utilization by hour)
EXPO = {0:.1,1:.1,2:.1,3:.1,4:.1,5:.2,6:.4,7:.7,8:1.0,9:1.0,10:1.0,11:.8,
        12:.6,13:.6,14:.6,15:.7,16:.8,17:1.0,18:1.0,19:1.0,20:.9,21:.6,22:.3,23:.2}
df['expo_weight'] = df['hour'].map(EXPO)
# processing lag (created->modified), hours
df['proc_lag_h'] = (df['modified_utc'] - df['created_utc']).dt.total_seconds()/3600

# ---------- VIOLATIONS: parse arrays ----------
def parse(s):
    try:
        v=json.loads(s); return v if isinstance(v,list) else []
    except: return []
df['vt_list'] = df['violation_type'].apply(parse)
df['n_violations'] = df['vt_list'].apply(len)

OBSTRUCT = {  # carriageway-blocking severity 0..1
 'PARKING IN A MAIN ROAD':1.0,'DOUBLE PARKING':1.0,
 'PARKING NEAR ROAD CROSSING':0.9,'PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS':0.9,
 'PARKING OPPOSITE TO ANOTHER PARKED VEHICLE':0.8,
 'PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC':0.7,
 'WRONG PARKING':0.6,'NO PARKING':0.5,'PARKING OTHER THAN BUS STOP':0.5,
 'PARKING ON FOOTPATH':0.3,
}
def obstruct(lst):
    ws=[OBSTRUCT.get(v,0.1) for v in lst]
    return max(ws) if ws else 0.0
df['obstruct_w'] = df['vt_list'].apply(obstruct)
df['primary_violation'] = df['vt_list'].apply(lambda l: max(l, key=lambda v: OBSTRUCT.get(v,0.1)) if l else 'UNKNOWN')
for flag,key in [('f_main_road','PARKING IN A MAIN ROAD'),('f_double','DOUBLE PARKING'),
                 ('f_crossing','PARKING NEAR ROAD CROSSING'),('f_signal','PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS'),
                 ('f_footpath','PARKING ON FOOTPATH'),('f_bsh','PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC')]:
    df[flag] = df['vt_list'].apply(lambda l,k=key: k in l)
df['is_parking'] = df['obstruct_w']>=0.3  # parking-relevant record

# ---------- VEHICLE: PCU + class ----------
PCU = {'SCOOTER':0.5,'MOTOR CYCLE':0.5,'MOPED':0.5,
       'PASSENGER AUTO':1.2,'GOODS AUTO':1.2,
       'CAR':1.0,'VAN':1.0,'MAXI-CAB':1.4,'JEEP':1.0,
       'LGV':1.5,'TEMPO':1.5,
       'BUS (BMTC/KSRTC)':3.0,'PRIVATE BUS':3.0,'MINI BUS':2.2,
       'TRUCK':3.5,'TANKER':3.5,'HTV':3.5,'HGV':3.5,'TRACTOR':2.5,'TRAILER':4.0,
       'LORRY/GOODS VEHICLE':3.5,'MINI LORRY':2.0,
       'FACTORY BUS':3.0,'TOURIST BUS':3.0,'SCHOOL VEHICLE':2.0,'OTHERS':1.0}
HEAVY_SET = {'BUS (BMTC/KSRTC)','PRIVATE BUS','MINI BUS','TRUCK','TANKER','HTV','HGV',
             'TRACTOR','TRAILER','LORRY/GOODS VEHICLE','MINI LORRY','FACTORY BUS','TOURIST BUS'}
def vclass(v):
    if v in ('SCOOTER','MOTOR CYCLE','MOPED'): return '2W'
    if v in ('PASSENGER AUTO','GOODS AUTO'):   return '3W'
    if v in HEAVY_SET: return 'HEAVY'
    return '4W-light'
df['pcu'] = df['vehicle_type'].map(PCU).fillna(1.0)
df['vehicle_class'] = df['vehicle_type'].apply(vclass)
df['is_heavy'] = df['vehicle_class']=='HEAVY'
unmapped = sorted(set(df.loc[~df['vehicle_type'].isin(PCU),'vehicle_type'].dropna().unique()))
print("\nVehicle types NOT in PCU map (default 1.0):", unmapped[:20])

# ---------- SPATIAL ----------
df['has_junction'] = (df['junction_name'].fillna('No Junction')!='No Junction')
for r in (8,9,10):
    df[f'h3_{r}'] = [h3.latlng_to_cell(la,lo,r) for la,lo in zip(df.latitude,df.longitude)]

# ---------- VALIDATION ----------
df['is_approved'] = df['validation_status'].eq('approved')
df['is_rejected'] = df['validation_status'].eq('rejected')

# ---------- record-level impact proxy ----------
df['impact_proxy'] = df['obstruct_w'] * df['pcu'] * df['expo_weight']

keep = ['id','latitude','longitude','location','police_station','junction_name','has_junction',
        'created_ist','date','hour','dow','dow_name','month','is_weekend','time_of_day',
        'is_am_peak','is_pm_peak','is_peak','expo_weight','proc_lag_h',
        'vt_list','n_violations','primary_violation','obstruct_w','is_parking',
        'f_main_road','f_double','f_crossing','f_signal','f_footpath','f_bsh',
        'vehicle_type','pcu','vehicle_class','is_heavy',
        'validation_status','is_approved','is_rejected','data_sent_to_scita',
        'impact_proxy','h3_8','h3_9','h3_10']
out = df[keep].copy()
out['vt_list'] = out['vt_list'].apply(json.dumps)
out.to_parquet('clean.parquet')
print(f"\nSaved clean.parquet  rows={len(out):,}  (dropped {n0-len(out)} null-date rows)")

# quick spans
print("\nDate span IST:", df['created_ist'].min(), "->", df['created_ist'].max())
print("Distinct dates:", df['date'].nunique())
print("proc_lag_h: median=%.1f  p90=%.1f  (neg=%d)" % (df['proc_lag_h'].median(), df['proc_lag_h'].quantile(.9), (df['proc_lag_h']<0).sum()))
