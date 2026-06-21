import pandas as pd, numpy as np, json
from scipy.stats import entropy
from style import *
df = pd.read_parquet('clean.parquet')
NDAYS = df['date'].nunique()

def hour_entropy(h):
    c=np.bincount(h.values, minlength=24).astype(float)
    return entropy(c+1e-9, base=2)
def modal(s): 
    return s.mode().iloc[0] if len(s) else None

KEY='h3_9'
g=df.groupby(KEY)
feat=pd.DataFrame({
 # --- VOLUME / PERSISTENCE ---
 'n_violations'      : g.size(),
 'n_days_active'     : g['date'].nunique(),
 # --- INTENSITY / COMPOSITION (per-violation; not collinear with volume) ---
 'mean_obstruct_w'   : g['obstruct_w'].mean(),
 'mean_pcu'          : g['pcu'].mean(),
 'heavy_share'       : g['is_heavy'].mean(),
 'main_road_share'   : g['f_main_road'].mean(),
 'crossing_signal_share': g.apply(lambda d:(d.f_crossing|d.f_signal).mean()),
 'footpath_share'    : g['f_footpath'].mean(),
 'junction_share'    : g['has_junction'].mean(),
 # --- TEMPORAL ---
 'peak_share'        : g['is_peak'].mean(),
 'am_peak_share'     : g['is_am_peak'].mean(),
 'pm_peak_share'     : g['is_pm_peak'].mean(),
 'night_share'       : g.apply(lambda d:(d.hour<6).mean()),
 'weekend_share'     : g['is_weekend'].mean(),
 'mean_expo'         : g['expo_weight'].mean(),
 'hour_entropy'      : g['hour'].apply(hour_entropy),
 'modal_hour'        : g['hour'].apply(modal),
 # --- WORKFLOW / QUALITY ---
 'approval_rate'     : g.apply(lambda d: d.is_approved.sum()/max((d.validation_status.notna()).sum(),1)),
 'scita_share'       : g['data_sent_to_scita'].mean(),
 # --- IMPACT proxy ---
 'impact_sum'        : g['impact_proxy'].sum(),
 # --- SPATIAL ---
 'lat'               : g['latitude'].mean(),
 'lon'               : g['longitude'].mean(),
 'dom_station'       : g['police_station'].apply(modal),
 'dom_violation'     : g['primary_violation'].apply(modal),
})
feat['active_days_ratio']  = feat['n_days_active']/NDAYS
feat['vio_per_active_day'] = feat['n_violations']/feat['n_days_active']
feat['impact_per_violation']= feat['impact_sum']/feat['n_violations']
feat['log_n']              = np.log1p(feat['n_violations'])
feat.to_csv('hex_features_res9.csv')
print("Saved hex_features_res9.csv  ->", feat.shape, "(rows=hotspot cells, cols=features)")
print("\nfeature dtypes/sample (head):")
print(feat[['n_violations','n_days_active','vio_per_active_day','mean_obstruct_w','heavy_share',
            'main_road_share','junction_share','peak_share','night_share','hour_entropy',
            'modal_hour','approval_rate','impact_per_violation']].describe().round(2).T.to_string())

# zero-inflation for prediction target (hex x date)
present = df.groupby([KEY,'date']).size()
possible = feat.shape[0]*NDAYS
print("\nPREDICTION-TARGET SPARSITY (hex × day): %.1f%% of cells are zero (-> zero-inflated)" %
      (100*(1 - len(present)/possible)))

# ---- Fig 11: feature correlation (intensity + temporal subset) ----
num=['log_n','n_days_active','vio_per_active_day','mean_obstruct_w','mean_pcu','heavy_share',
     'main_road_share','crossing_signal_share','footpath_share','junction_share',
     'peak_share','am_peak_share','pm_peak_share','night_share','weekend_share','hour_entropy',
     'approval_rate','impact_per_violation']
C=feat[num].corr()
fig,ax=plt.subplots(figsize=(12.5,10))
sns.heatmap(C, cmap='RdBu_r', center=0, vmin=-1, vmax=1, annot=True, fmt='.2f',
    annot_kws={'size':7}, square=True, linewidths=.4, linecolor='white', cbar_kws={'shrink':.7})
ax.set_title('Hotspot-cell feature correlations\n(volume decoupled from intensity → both axes carry signal)')
plt.tight_layout(); plt.savefig('plots/11_feature_correlation.png'); plt.close()

# ---- Fig 12: volume vs intensity (motivates 2-axis impact score) ----
big=feat[feat.n_violations>=20]
fig,ax=plt.subplots(figsize=(9.5,6.5))
sc=ax.scatter(big.n_violations, big.mean_obstruct_w, s=12+big.heavy_share*600,
    c=big.junction_share, cmap='viridis', alpha=.6, edgecolor='none')
ax.set_xscale('log'); ax.set_xlabel('volume: violations in cell (log)'); ax.set_ylabel('intensity: mean obstruction severity')
ax.axhline(big.mean_obstruct_w.median(), ls='--', color='gray', lw=1)
ax.axvline(big.n_violations.median(), ls='--', color='gray', lw=1)
ax.set_title('Volume ≠ Intensity: hotspots split into 4 quadrants\n(size = heavy-vehicle share · color = junction share)')
ax.text(0.97,0.96,'HIGH-PRIORITY\n(busy & obstructive)',ha='right',va='top',transform=ax.transAxes,
    fontsize=9,color=ACC,fontweight='bold')
plt.colorbar(sc,ax=ax,label='junction share',shrink=.8); plt.tight_layout()
plt.savefig('plots/12_volume_vs_intensity.png'); plt.close()
print("plots saved: 11,12")
