import pandas as pd, numpy as np
from style import *
df = pd.read_parquet('clean.parquet')

# ===== DIAGNOSTICS =====
print("="*60,"\nANOMALY CHECKS\n","="*60)
# (a) 4-5am spike: concentrated on few dates (artifact) or spread (real)?
early = df[df.hour.isin([4,5])]
print(f"4-5am records: {len(early):,} ({len(early)/len(df)*100:.1f}% of all)")
print("  distinct dates with 4-5am activity:", early['date'].nunique(), "of 151")
top_dates = early.groupby('date').size().sort_values(ascending=False)
print("  top 5 dates' share of the 4-5am bucket: %.0f%%" % (top_dates.head(5).sum()/len(early)*100))
print("  4-5am by station (top 4):"); print(early['police_station'].value_counts().head(4).to_string())
# (b) coordinate precision
dec = df['latitude'].astype(str).str.split('.').str[1].str.len()
print("\nlat decimal places: median=%d  (precision ~%.0fm)" % (dec.median(), 111000/10**dec.median()))
# (c) repeat vehicles
print("\n# records / unique device (officer proxy): median=%.0f" % df.groupby('h3_10').size().median())

# ===== Fig 4: geographic density (hexbin) =====
fig,ax=plt.subplots(figsize=(8.2,8))
hb=ax.hexbin(df.longitude, df.latitude, gridsize=130, cmap='inferno', mincnt=1, bins='log')
ax.set_title('Where violations happen: Bengaluru density\n(log color scale)')
ax.set_xlabel('longitude'); ax.set_ylabel('latitude'); ax.set_aspect('equal','box')
plt.colorbar(hb,ax=ax,label='log(violations)',shrink=.7); plt.tight_layout()
plt.savefig('plots/04_spatial_density.png'); plt.close()

# ===== concentration: Lorenz over H3 res-10 cells =====
hex_counts = df.groupby('h3_10').size().sort_values()
c = np.sort(hex_counts.values); cum = np.cumsum(c)/c.sum(); x=np.arange(1,len(c)+1)/len(c)
gini = 1 - 2*np.trapezoid(cum, x)
# top-k coverage
def cov(frac): 
    k=int(len(c)*frac); return c[-k:].sum()/c.sum()*100
fig,axes=plt.subplots(1,2,figsize=(13.5,4.6))
axes[0].plot(x*100, cum*100, color=ACC, lw=2.5); axes[0].plot([0,100],[0,100],'--',color='gray',lw=1)
axes[0].fill_between(x*100, cum*100, x*100, color=ACC, alpha=.12)
axes[0].set_title(f'Spatial concentration of violations\nGini={gini:.2f}  ·  hotspots are extreme')
axes[0].set_xlabel('% of hotspot cells (H3 ~65m, sorted)'); axes[0].set_ylabel('% of violations')
axes[0].annotate(f'top 1% cells = {cov(.01):.0f}% of violations\ntop 5% cells = {cov(.05):.0f}%\ntop 10% cells = {cov(.10):.0f}%',
    xy=(2,55), fontsize=10, bbox=dict(boxstyle='round',fc='white',ec=ACC))
st = df['police_station'].value_counts().head(15)[::-1]
axes[1].barh(range(len(st)), st.values, color=INK); axes[1].set_yticks(range(len(st)))
axes[1].set_yticklabels(st.index, fontsize=9); axes[1].set_title('Top 15 police stations by volume')
axes[1].set_xlabel('violations')
plt.tight_layout(); plt.savefig('plots/05_spatial_concentration.png'); plt.close()

# ===== top hotspot locations (named) =====
loc = df['location'].value_counts().head(15)[::-1]
fig,ax=plt.subplots(figsize=(11,5.2))
ax.barh(range(len(loc)), loc.values, color=GRN)
ax.set_yticks(range(len(loc))); ax.set_yticklabels([l[:55] for l in loc.index], fontsize=8.5)
ax.set_title('Top 15 recurring violation locations (by text address)'); ax.set_xlabel('violations')
plt.tight_layout(); plt.savefig('plots/06_top_locations.png'); plt.close()

print("\nGINI (H3-10 cells)= %.3f" % gini)
print("n hotspot cells res10=%d  res9=%d  res8=%d" % (df.h3_10.nunique(), df.h3_9.nunique(), df.h3_8.nunique()))
print("top1%%=%.0f%% top5%%=%.0f%% top10%%=%.0f%% of violations" % (cov(.01),cov(.05),cov(.10)))
print("junction-tagged share: %.1f%%" % (df.has_junction.mean()*100))
print("plots saved: 04,05,06")
