import pandas as pd, numpy as np
from scipy import stats
from style import *
df = pd.read_parquet('clean.parquet')

# ---- aggregate to hotspot cells (H3 res-10 ~65m) ----
g = df.groupby('h3_10')
hexd = pd.DataFrame({
    'n': g.size(),
    'sev_sum': g['obstruct_w'].sum(),
    'pcu_sum': g['pcu'].sum(),
    'impact_sum': g['impact_proxy'].sum(),
})
n = hexd['n'].values.astype(float)

print("HOTSPOT-CELL VIOLATION COUNT (H3-10), n cells =", len(n))
print("  mean=%.1f  var=%.1f  median=%.0f  max=%.0f" % (n.mean(),n.var(),np.median(n),n.max()))
disp = n.var()/n.mean()
print("  DISPERSION (var/mean) = %.1f  -> %s" % (disp, "Poisson OK" if disp<2 else "OVERDISPERSED: use Negative Binomial"))
print("  skewness raw      = %.2f" % stats.skew(n))
logn = np.log1p(n)
print("  skewness log1p    = %.2f" % stats.skew(logn))
bc, lam = stats.boxcox(n)            # n>=1 so strictly positive
print("  skewness box-cox  = %.2f   (lambda=%.3f)" % (stats.skew(bc), lam))
# fraction zeros if we densify hex x hour (for prediction target)
print("  (note: for hex x hour prediction the target is zero-inflated)")

# ---- Fig 9: distributions + transforms (2x3) ----
fig,ax=plt.subplots(2,3,figsize=(15.5,8))
for j,(data,name,extra) in enumerate([(n,'Raw count',''),(logn,'log1p(count)',''),(bc,f'Box-Cox  λ={lam:.2f}','')]):
    ax[0,j].hist(data,bins=60,color=[ACC,ACC2,GRN][j],alpha=.85)
    ax[0,j].set_title(f'{name}\nskew={stats.skew(data):.2f}'); ax[0,j].set_ylabel('cells')
    stats.probplot(data, plot=ax[1,j]); ax[1,j].get_lines()[0].set_color([ACC,ACC2,GRN][j])
    ax[1,j].get_lines()[0].set_markersize(3); ax[1,j].get_lines()[1].set_color('k')
    ax[1,j].set_title('Q-Q vs normal')
fig.suptitle('Hotspot-cell violation counts: raw is extreme right-skew; Box-Cox normalizes best',
    fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout(); plt.savefig('plots/09_distribution_boxcox.png'); plt.close()

# ---- Fig 10: rank-frequency (power-law test) ----
s = np.sort(n)[::-1]; rank=np.arange(1,len(s)+1)
mask = s>=3
slope,intercept = np.polyfit(np.log(rank[mask]), np.log(s[mask]), 1)
fig,axx=plt.subplots(figsize=(7.5,5.2))
axx.loglog(rank, s, '.', color=INK, ms=3, alpha=.5)
axx.loglog(rank[mask], np.exp(intercept)*rank[mask]**slope, color=ACC, lw=2,
    label=f'power-law fit  slope={slope:.2f}')
axx.set_title('Rank–frequency of hotspot intensity\n(near-linear on log-log = heavy-tailed / power-law-like)')
axx.set_xlabel('hotspot rank'); axx.set_ylabel('violations in cell'); axx.legend(frameon=False)
plt.tight_layout(); plt.savefig('plots/10_rank_frequency.png'); plt.close()

# correlation of hex features (preview)
print("\nHEX-FEATURE CORRELATIONS (Pearson):")
print(hexd.corr().round(2).to_string())
print("plots saved: 09,10")
