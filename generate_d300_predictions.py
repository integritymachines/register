#!/usr/bin/env python3
"""Complete a frozen Class-D roll-call panel with speculative numeric guesses.

This script is intentionally upstream of measurement and projection. It reads a
previously frozen prediction release, verifies its hashes, preserves every
existing numeric prediction, fills abstentions, and emits a separately hashed
complete release. It never reads A/B or C measurements or 10D coordinates.
"""
import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('input_dir',type=Path,help='Frozen v1 directory containing D300_ROLLCALL.csv and FREEZE.json')
parser.add_argument('-o','--output-dir',type=Path,default=Path('D300_predictions_full'))
parser.add_argument('--archive',type=Path,help='Optional .zip output path')
args=parser.parse_args()
src=args.input_dir
out=args.output_dir
out.mkdir(parents=True,exist_ok=True)
frozen=json.loads((src/'FREEZE.json').read_text())
for name,digest in frozen['outputs_sha256'].items():
 assert hashlib.sha256((src/name).read_bytes()).hexdigest()==digest,name
old=list(csv.DictReader((src/'D300_ROLLCALL.csv').open(newline='')))
people=list(csv.DictReader((src/'D300_AUTHORS.csv').open(newline='')))
lex=list(csv.DictReader((src/'LEXICON.csv').open(newline='')))
assert len(old)==300*48 and len(people)==300 and len(lex)==48

def clip(x):return max(0,min(10,round(x*2)/2))
def get(r,p):return float(r[p]['predicted_score_0_10'])
by_author={p['d_id']:{} for p in people}
for r in old:by_author[r['d_id']][r['pair_id']]=r

# An explicit set of guesses for the two mostly illustrated or rhymed corpora.
# These concern the author's *written verbal material*, not the illustrations.
picture={
 'D050':[6,1,8,8,8,2,1,0,1,1,3,8,6,5,9,8,7,2,2,6,3,7,9,9,9,3,7,8,5,0,1,1,7,0,8,0,0,2,0,0,1,1,1,7,7,8,3,8],
 'D051':[4,2,6,7,7,3,2,2,2,2,3,7,6,4,6,7,5,2,2,5,3,6,8,8,8,5,3,6,3,1,2,2,5,1,7,1,1,3,1,1,2,2,2,6,5,7,3,7],
}
assert all(len(v)==48 for v in picture.values())

# For the eleven previously abstained pairs, make the dependence on the
# earlier speculative guesses explicit. There is no fitted parameter here.
def derive(pid,r):
 v=lambda p:get(r,p)-5
 if pid=='P009':return 5+.6*v('P001')-.35*v('P004')+.25*v('P011')
 if pid=='P010':return 5+.5*v('P001')-.45*v('P004')
 if pid=='P026':return 5-.4*v('P003')+.25*v('P008')
 if pid=='P031':return 5+.4*v('P012')+.25*v('P030')-.2*v('P004')
 if pid=='P033':return 5+.35*v('P015')+.25*v('P004')
 if pid=='P034':return 5+.5*v('P011')+.25*v('P029')+.15*v('P001')
 if pid=='P035':return 5+.65*v('P012')
 if pid=='P036':return 5+.35*v('P001')-.55*v('P004')+.2*v('P012')
 if pid=='P037':return 5+.35*v('P012')-.4*v('P004')
 if pid=='P040':return 5+.25*v('P039')+.15*v('P018')
 if pid=='P043':return 5+.7*v('P006')
 raise KeyError(pid)

translation_missing={'P001','P007','P008','P030','P032','P038'}
def translation_guess(pid,r,profile):
 # Based on the declared profile and author cue tags, never a translator's text.
 base={'P001':5,'P007':5,'P008':5,'P030':5,'P032':4,'P038':5}
 val=base[pid]
 if profile in {'classic','epic','fantasy','horror','literary'}:
  val+= {'P001':1.5,'P007':1,'P008':1,'P030':1,'P032':1,'P038':1}[pid]
 if profile in {'minimalist','restrained','translated'}:
  val+= {'P001':-1,'P007':-1,'P008':-.5,'P030':-1,'P032':0,'P038':-.5}[pid]
 cues=r['P002']['author_cues']
 if 'O' in cues and pid in {'P001','P007','P030'}:val+=1
 if 'K' in cues and pid in {'P001','P030'}:val-=.5
 if 'I' in cues and pid in {'P008','P038'}:val-=.5
 return val

recs=[]
for person in people:
 aid=person['d_id']; rr=by_author[aid]
 for index,p in enumerate(lex):
  pid=p['pair_id']; prev=rr[pid]
  if prev['predicted_score_0_10']:
   val=float(prev['predicted_score_0_10'])
   lo=prev['plausible_low'];hi=prev['plausible_high']
   conf=prev['confidence'];origin='v1_frozen_unchanged';note=prev['prediction_notes']
  else:
   if aid in picture:
    val=picture[aid][index]; origin='illustrated_or_verse_guess'
    note='Speculative verbal-register guess for mixed verse/illustrated writing; a prose aggregate may be unstable.'
   elif pid in translation_missing:
    val=clip(translation_guess(pid,rr,person['prior_template']))
    origin='translation_sensitive_background_guess'
    note='English surface depends strongly on edition/translator; hypothesized without selecting a translation.'
   else:
    val=clip(derive(pid,rr));origin='derived_from_other_D_guesses'
    note='Subjective pair-specific extrapolation from other *predictions*, not independent evidence or corpus measurement.'
   lo=f'{max(0,val-4.5):.1f}';hi=f'{min(10,val+4.5):.1f}'
   conf='extremely_low'
   # Make preceding speculative fills available to later pair rules for the
   # same author; the original frozen CSV remains untouched.
   rr[pid]=dict(prev,predicted_score_0_10=f'{val:.1f}')
  recs.append([aid,pid,f'{val:.1f}',lo,hi,conf,'none',origin,note])

with (out/'D300_ROLLCALL_FULL.csv').open('w',newline='') as f:
 w=csv.writer(f)
 w.writerow(['d_id','pair_id','predicted_score_0_10','plausible_low','plausible_high','confidence','corpus_coverage','prediction_origin','prediction_notes'])
 w.writerows(recs)
for name in ['D300_AUTHORS.csv','LEXICON.csv','MANIFEST.csv']:
 shutil.copyfile(src/name,out/name)
shutil.copyfile(__file__,out/'generation_code.py')

(out/'README.md').write_text('''# D300 complete speculative forecast, v2\n\nThis release has all 300 × 48 = 14,400 **numeric background guesses**, with no abstentions. It preserves the 10,810 numeric values in the frozen v1 release exactly and fills the other 3,590. This is a new version: the original freeze remains intact. No A/B or C author membership, measurements, coordinates, or projections were read to create either version.\n\nThe fixed 48 pairs and manifest IDs are unchanged. The scale remains the repository's A/B empirical percentile scale, not a semantic midpoint scale. Uncertainty bands are subjective, not calibrated. The newly filled scores have extremely low confidence and are chiefly structured guesses extrapolated from the other Class D guesses. They are **not independent author-level observations**. Translation-sensitive predictions do not represent a known translator. Dr. Seuss and Maurice Sendak receive speculative estimates for verbal material despite the ill-defined prose aggregate; their visual and verse work makes those estimates especially fragile. `prediction_origin` identifies each mechanism. No score has text coverage.\n\n`FREEZE.json` hashes the input v1 freeze and every v2 output before any observed-data comparison. Direct 10D estimation and conversion remain outside this task.\n''')
output_hash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.name!='FREEZE.json'}
new_count=sum(r[7]!='v1_frozen_unchanged' for r in recs)
(out/'FREEZE.json').write_text(json.dumps({'date_utc':datetime.now(timezone.utc).isoformat(),'stage':'v2 background guesses only; no measured data consulted','input_v1_freeze_sha256':hashlib.sha256((src/'FREEZE.json').read_bytes()).hexdigest(),'unchanged_v1_numeric_rows':len(recs)-new_count,'newly_filled_rows':new_count,'total_numeric_rows':len(recs),'output_sha256':output_hash},indent=2)+'\n')
if args.archive:
 args.archive.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(args.archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(out.iterdir()):z.write(p,p.name)
print(f'{len(recs)} numeric predictions; {new_count} abstentions filled; output={out}')
