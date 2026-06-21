import pandas as pd, numpy as np, json
from collections import Counter
from style import *
df = pd.read_parquet('clean.parquet')
df['vt_list']=df['vt_list'].apply(json.loads)

# ---- Fig 7: categorical trio ----
fig,axes=plt.subplots(1,3,figsize=(16,4.8))
vt=Counter()
for l in df['vt_list']:
    for v in l: vt[v]+=1
vt=pd.Series(dict(vt)).sort_values().tail(11)
axes[0].barh(range(len(vt)),vt.values,color=ACC)
axes[0].set_yticks(range(len(vt))); axes[0].set_yticklabels([v[:32] for v in vt.index],fontsize=8.5)
axes[0].set_title('Violation types (exploded)')
vc=df['vehicle_type'].value_counts().tail(12).sort_values()
axes[1].barh(range(len(vc)),vc.values,color=ACC2)
axes[1].set_yticks(range(len(vc))); axes[1].set_yticklabels([v[:24] for v in vc.index],fontsize=8.5)
axes[1].set_title('Vehicle types (top 12)')
cl=df['vehicle_class'].value_counts()
vs=df['validation_status'].fillna('(null)').value_counts()
axes[2].bar(range(len(vs)),vs.values,color=[GRN if i=='approved' else (ACC if i=='rejected' else INK) for i in vs.index])
axes[2].set_xticks(range(len(vs))); axes[2].set_xticklabels(vs.index,rotation=35,ha='right',fontsize=9)
axes[2].set_title('Validation status')
plt.tight_layout(); plt.savefig('plots/07_categorical.png'); plt.close()

# ---- Fig 8: co-occurrence + vehicle x violation ----
TOP=['WRONG PARKING','NO PARKING','PARKING IN A MAIN ROAD','PARKING ON FOOTPATH',
     'PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC','DOUBLE PARKING','PARKING NEAR ROAD CROSSING',
     'PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS','PARKING OPPOSITE TO ANOTHER PARKED VEHICLE']
idx={v:i for i,v in enumerate(TOP)}
M=np.zeros((len(TOP),len(TOP)))
for l in df['vt_list']:
    present=[v for v in l if v in idx]
    for a in present:
        for b in present:
            M[idx[a],idx[b]]+=1
Mn=M/ (np.diag(M)[:,None]+1e-9)  # P(col | row)
fig,axes=plt.subplots(1,2,figsize=(16,6.2))
sns.heatmap(Mn, ax=axes[0], cmap='mako_r', xticklabels=[v[:18] for v in TOP], yticklabels=[v[:24] for v in TOP],
    annot=True, fmt='.2f', annot_kws={'size':7}, cbar_kws={'label':'P(col co-occurs | row)'})
axes[0].set_title('Violation co-occurrence  P(col | row)')
# vehicle class x primary violation
pv = df[df.primary_violation.isin(TOP)]
ct = pd.crosstab(pv['vehicle_class'], pv['primary_violation'], normalize='index')
ct = ct.reindex(columns=[c for c in TOP if c in ct.columns])
sns.heatmap(ct, ax=axes[1], cmap='rocket_r', annot=True, fmt='.2f', annot_kws={'size':7},
    xticklabels=[v[:18] for v in ct.columns], cbar_kws={'label':'row-normalized'})
axes[1].set_title('Vehicle class × primary violation'); axes[1].set_ylabel('')
plt.tight_layout(); plt.savefig('plots/08_cooccurrence.png'); plt.close()

print("VEHICLE CLASS shares:"); print((cl/cl.sum()*100).round(1).to_string())
print("\nvalidation status %:"); print((vs/vs.sum()*100).round(1).to_string())
print("\nmulti-violation records: %.1f%% have >1 type" % ((df.n_violations>1).mean()*100))
print("\nHEAVY-vehicle violations: %d (%.2f%%) (disproportionate PCU footprint)" % (df.is_heavy.sum(), df.is_heavy.mean()*100))
print("rejected rate among validated: %.1f%%" % (df.is_rejected.sum()/(df.validation_status.notna().sum())*100))
print("plots saved: 07,08")
