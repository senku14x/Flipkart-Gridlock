import pandas as pd, numpy as np
from style import *
df = pd.read_parquet('clean.parquet')
df['created_ist']=pd.to_datetime(df['created_ist'])

# ---- Fig 1: daily time series ----
daily = df.groupby('date').size()
daily.index = pd.to_datetime(daily.index)
full = pd.date_range(daily.index.min(), daily.index.max(), freq='D')
daily = daily.reindex(full, fill_value=0)
fig,ax=plt.subplots(figsize=(13,4.2))
ax.plot(daily.index, daily.values, color=INK, lw=1, alpha=.6, label='daily')
ax.plot(daily.index, daily.rolling(7,center=True).mean(), color=ACC, lw=2.5, label='7-day avg')
for d in daily.index:
    if d.dayofweek>=5: ax.axvspan(d, d+pd.Timedelta(days=1), color=ACC2, alpha=.05)
ax.set_title('Daily parking-violation volume (IST)  ·  weekends shaded')
ax.set_ylabel('violations / day'); ax.legend(loc='upper right', frameon=False)
ax.margins(x=0.01); plt.tight_layout(); plt.savefig('plots/01_temporal_daily.png'); plt.close()

# ---- Fig 2: hour / dow / month profiles ----
fig,axes=plt.subplots(1,3,figsize=(15,4.3))
hr = df.groupby('hour').size()
cols=[ACC if (8<=h<=10 or 17<=h<=20) else INK for h in hr.index]
axes[0].bar(hr.index, hr.values, color=cols)
axes[0].set_title('By hour of day (IST)\n(peaks highlighted)'); axes[0].set_xlabel('hour'); axes[0].set_xticks(range(0,24,2))
order=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
dw=df['dow_name'].value_counts().reindex(order)
axes[1].bar(range(7), dw.values, color=[INK]*5+[ACC2]*2)
axes[1].set_xticks(range(7)); axes[1].set_xticklabels([d[:3] for d in order]); axes[1].set_title('By day of week')
mo=df.groupby('month').size()
axes[2].bar(range(len(mo)), mo.values, color=GRN)
axes[2].set_xticks(range(len(mo))); axes[2].set_xticklabels(mo.index, rotation=45, ha='right'); axes[2].set_title('By month\n(Nov & Apr partial)')
plt.tight_layout(); plt.savefig('plots/02_temporal_profiles.png'); plt.close()

# ---- Fig 3: hour x dow heatmap ----
piv = df.pivot_table(index='dow_name', columns='hour', values='id', aggfunc='count').reindex(order)
piv = piv.reindex(columns=range(24)).fillna(0)
fig,ax=plt.subplots(figsize=(13,4.6))
sns.heatmap(piv, cmap='rocket_r', ax=ax, cbar_kws={'label':'violations'}, linewidths=.3, linecolor='white')
ax.set_yticklabels([d[:3] for d in order], rotation=0)
ax.set_title('When do violations happen?  Hour × Day-of-week (IST)'); ax.set_xlabel('hour of day')
plt.tight_layout(); plt.savefig('plots/03_temporal_heatmap.png'); plt.close()

# ---- stats ----
print("BUSIEST HOURS (IST):"); print(hr.sort_values(ascending=False).head(6).to_string())
print("\nshare in defined peaks (AM8-10 / PM17-20): %.1f%%" % (df['is_peak'].mean()*100))
wd = df[~df.is_weekend].groupby('date').size().mean(); we = df[df.is_weekend].groupby('date').size().mean()
print("avg/day weekday=%.0f  weekend=%.0f  (weekend is %.0f%% of weekday)" % (wd,we,we/wd*100))
print("\nDOW totals:"); print(dw.to_string())
print("\nbusiest single (dow,hour) cells:")
s=piv.stack().sort_values(ascending=False).head(5)
for (d,h),v in s.items(): print(f"  {d[:3]} {int(h):02d}:00 -> {int(v):,}")
print("\nplots saved: 01,02,03")
