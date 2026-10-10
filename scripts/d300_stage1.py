#!/usr/bin/env python3
"""Stage 1: generate prospective Class-D roll-call guesses."""
import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--lexicon',type=Path,required=True)
parser.add_argument('--templates',type=Path,required=True,help='Frozen D24 roll-call guesses')
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
manifest=args.manifest
lexicon=args.lexicon
prior=args.templates # guesses only, no controls or AB reveal
dest=args.output_dir;dest.mkdir(parents=True,exist_ok=True)
people=list(csv.DictReader(manifest.open(encoding='utf-8-sig',newline='')))
pairs=list(csv.DictReader(lexicon.open(newline='')))
assert len(people)==300 and len(pairs)==48
assert len({p['d_id'] for p in people})==len({p['author'] for p in people})==300

# Frozen, prospective template vectors from the earlier D panel. These are
# heuristics, not coordinates or learned corpus statistics. Template use is
# explicit per author and does not change the roll-call instrument.
old={}
for r in csv.DictReader(prior.open(newline='')):
 if r['predicted_score_0_10']:
  old.setdefault(r['author_id'],{})[r['pair_id']]=float(r['predicted_score_0_10'])
templates={
 'literary':'D0013', 'restrained':'D0020', 'experimental':'D0005',
 'speculative':'D0008', 'fantasy':'D0001', 'horror':'D0009',
 'children':'D0012', 'detection':'D0020', 'noir':'D0010',
 'satire':'D0022', 'classic':'D0003', 'modernist':'D0004',
 'realist':'D0014', 'essay':'D0007', 'philosophical':'D0016',
 'translated':'D0017', 'epic':'D0006', 'minimalist':'D0002',
 'interior':'D0023', 'expansive':'D0024',
}

# Explicit author-level categorical priors, keyed solely to manifest IDs.
# A code is an imperfect starting hypothesis, not an author classification.
code=['realist']*300
def assign(profile, ids):
 for i in ids:
  assert 1<=i<=300
  code[i-1]=profile
def span(profile,a,b):assign(profile,range(a,b+1))
span('speculative',8,24);span('horror',25,33);span('fantasy',34,48)
span('children',49,60);span('detection',61,68);span('noir',69,82)
span('classic',105,129);span('speculative',193,218)
span('translated',260,287)
assign('literary',[1,3,5,13,84,88,90,95,98,100,102,131,132,134,139,145,151,154,156,158,159,167,170,172,177,178,180,185,186,188,222,223,224,225,230,232,233,234,235,236,240,244,245,246,251,252,254,255,256,273,274,277,282,285,289,292,293,298,300])
assign('restrained',[2,6,26,63,64,65,66,76,77,78,79,81,83,87,91,92,93,94,96,97,99,103,104,107,131,149,155,160,161,162,168,179,183,184,187,189,202,227,231,247,248,249,250,253,257,258,259,260,261,263,265,266,268,269,271,275,280,286,287,288,290,291,295,297,299])
assign('experimental',[7,20,30,36,38,41,86,89,95,106,144,146,166,169,171,174,176,190,192,219,221,226,235,238,267,276,278,279,283,284,294,296])
assign('philosophical',[13,16,19,37,38,109,141,144,150,156,192,200,205,210,212,216,237,240,245,262,264,267,273,281,282,284])
assign('minimalist',[2,4,62,63,64,67,68,70,71,79,96,99,103,126,148,149,155,162,173,181,183,226,266,280,288,297])
assign('modernist',[3,4,7,36,95,98,102,103,104,105,106,114,118,121,151,157,176,185,186,190,219,221,222,226,228,233,259,263,270,271,279])
assign('epic',[3,4,5,8,17,19,20,35,36,45,90,95,111,114,115,116,143,144,153,157,170,178,186,200,217,220,221,234,241,243,251,252,273,274,275,277,278,281,289,292])
assign('satire',[11,22,23,46,49,50,69,70,72,75,84,85,86,92,96,101,109,115,116,123,126,127,128,129,130,133,135,138,142,143,147,173,174,191,207,238,246,250,257,266,284])
assign('essay',[52,85,103,109,123,129,137,138,140,141,142,143,152,189,223,229,237,239,247,248,262,286,290,291])
assign('interior',[2,3,26,28,32,51,87,89,91,93,94,95,98,99,102,131,134,136,149,151,155,156,157,163,168,172,177,178,179,180,183,187,188,226,228,230,231,233,243,251,255,263,264,265,272,279,285,288,289,290,294,300])
assign('expansive',[3,5,18,19,20,24,27,28,34,35,36,42,45,46,47,61,69,75,80,86,88,90,95,105,115,116,134,137,142,143,144,145,157,159,166,170,176,185,190,192,201,207,219,221,222,223,229,235,239,241,242,243,244,251,252,262,274,275,278,281,282,284,289,292])

# Author-specific corrections to template: O ornate, A abstract, C categorical,
# K compressed, I intimate, V adversarial, H heated, T temporally dynamic,
# L nonlinear, Q dialogic, X explicitly explanatory. Each modifier is small;
# it is an openly subjective author-level cue, never learned from A/B data.
mods={
 1:'AI',2:'KI',3:'OIH',4:'CKHT',5:'OALH',6:'AK',7:'OAL',8:'AH',9:'VI',10:'AX',11:'KVI',12:'AK',13:'AK',14:'AX',15:'AX',16:'VC',17:'OAT',18:'AK',19:'AXL',20:'OAVL',21:'OAL',22:'KVI',23:'QIH',24:'OI',
 25:'VI',26:'IK',27:'OH',28:'OIH',29:'VI',30:'KA',31:'OIH',32:'KT',33:'VI',34:'AX',35:'OAT',36:'OAL',37:'AX',38:'OA',39:'OH',40:'OV',41:'OA',42:'OHT',43:'OAL',44:'OIT',45:'QHT',46:'OV',47:'QI',48:'OI',
 49:'VI',50:'OQ',51:'OI',52:'KX',53:'QI',54:'OQI',55:'OQI',56:'OQI',57:'OQT',58:'OQI',59:'OQI',60:'OQI',
 61:'OT',62:'KX',63:'KT',64:'AX',65:'QT',66:'QT',67:'KV',68:'KV',69:'VHK',70:'KQT',71:'KVT',72:'VK',73:'KV',74:'VI',75:'VHT',76:'KT',77:'IT',78:'AT',79:'KT',80:'VQT',81:'KX',82:'AT',
 83:'OI',84:'KV',85:'AV',86:'ALK',87:'IK',88:'IQ',89:'OI',90:'OIT',91:'OA',92:'KV',93:'I',94:'OA',95:'OHI',96:'KI',97:'IQ',98:'OI',99:'KI',100:'OI',101:'VA',102:'I',103:'KI',104:'KI',
 105:'OIL',106:'OIL',107:'K',108:'AX',109:'CV',110:'HT',111:'OT',112:'OQT',113:'OV',114:'IA',115:'QHT',116:'OVQ',117:'VQ',118:'OIH',119:'OI',120:'OI',121:'OHT',122:'OHT',123:'OV',124:'TK',125:'OH',126:'VK',127:'QI',128:'VA',129:'VQ',130:'QI',
 131:'KI',132:'OI',133:'KI',134:'OI',135:'VI',136:'OI',137:'HV',138:'AV',139:'IK',140:'KV',141:'AX',142:'VH',143:'HV',144:'AL',145:'AI',146:'AI',147:'KVI',148:'KA',149:'IV',150:'AK',151:'OI',152:'KI',153:'OI',154:'I',155:'KI',156:'IA',157:'OIT',158:'IT',159:'KHT',160:'KI',161:'KT',162:'KI',163:'VH',164:'VH',165:'IH',166:'VHL',167:'AK',168:'IA',169:'AL',170:'OI',171:'AI',172:'A',173:'VK',174:'VHK',175:'I',176:'AOL',177:'OI',178:'OIT',179:'KI',180:'KI',181:'KI',182:'IHT',183:'IK',184:'QI',185:'OIT',186:'AK',187:'I',188:'IH',189:'A',190:'VK',191:'VH',192:'AHL',
 193:'OAH',194:'AXK',195:'AK',196:'AX',197:'IQ',198:'AX',199:'IK',200:'AHT',201:'QT',202:'IK',203:'AT',204:'I',205:'AV',206:'AT',207:'VHK',208:'OI',209:'AV',210:'OAT',211:'OAH',212:'OAT',213:'AT',214:'AV',215:'OAH',216:'AV',217:'AX',218:'XT',
 219:'VHL',220:'TH',221:'AL',222:'AV',223:'VI',224:'VC',225:'QI',226:'IA',227:'IK',228:'OH',229:'IH',230:'IH',231:'IK',232:'QIH',233:'OIH',234:'OIH',235:'VQ',236:'AV',237:'AV',238:'VK',239:'IH',240:'VQI',241:'QI',242:'VA',243:'OVI',244:'OIH',245:'AK',246:'VI',247:'IT',248:'AV',249:'QI',250:'AV',251:'OAV',252:'OAT',253:'OI',254:'IT',255:'IK',256:'OI',257:'KAV',258:'KI',259:'VI',
 260:'IO',261:'VOH',262:'AVI',263:'IK',264:'IK',265:'IK',266:'KVI',267:'AV',268:'OIT',269:'KAV',270:'OI',271:'IH',272:'IO',273:'OHT',274:'OHT',275:'VA',276:'AL',277:'OIT',278:'VHL',279:'OIH',280:'KI',281:'OAL',282:'AOV',283:'OL',284:'AX',285:'OI',286:'KV',287:'IK',288:'IK',289:'OAH',290:'KI',291:'AV',292:'OIT',293:'IT',294:'VK',295:'TH',296:'VHT',297:'IK',298:'OIT',299:'AT',300:'OIH',
}
assert set(mods)==set(range(1,301))

# The mapping is to *fixed observed roll calls*, not latent axes. Pairs absent
# from the prior pilot have no numerical hypothesis here and are explicit nulls.
affects={
 'O': {'P001':1,'P007':.4,'P030':.5},
 'A': {'P002':1,'P023':-1,'P041':1,'P018':.4,'P019':.4},
 'C': {'P003':1,'P044':1},
 'K': {'P004':1,'P011':-0.3},
 'I': {'P005':1,'P025':.5,'P039':-0.5,'P016':.25},
 'V': {'P006':1,'P017':.5,'P046':.5},
 'H': {'P015':.7,'P016':1,'P042':-1,'P046':1},
 'T': {'P018':-0.5,'P024':.5,'P048':1},
 'L': {'P011':1,'P020':-.4,'P029':.5},
 'Q': {'P013':1,'P038':-.5},
 'X': {'P021':1,'P022':1,'P047':1},
}

def clamp(x):return max(0,min(10,x))
foreign=set(range(260,288))|{13,194,196,210,215,243,273,274,275,276,277,278,279,280,281,282,283,284,285,286,289,298}
# Unstable estimates of English typography/word choice under translation.
translator_sensitive={'P001','P007','P008','P030','P032','P038'}
prose_limited={50,51} # dominant verse or illustrated picture-book corpus
rows=[]
for ix,person in enumerate(people,1):
 pcode=code[ix-1];template=old[templates[pcode]]
 for pair in pairs:
  pid=pair['pair_id'];reason='';score='';lo='';hi='';confidence='abstain'
  if ix in prose_limited:
   reason='Dominant verse, illustrated book, or dramatic dialogue; prose author aggregate is ill-defined.'
  elif pid not in template:
   reason='Pair requires direct text for a defensible numerical background guess.'
  elif ix in foreign and pid in translator_sensitive:
   reason='English lexical/surface register depends materially on translator and edition.'
  else:
   # Shrink a prior D template toward the frozen scale midpoint; add the
   # author-specific prospective corrections, without corpus observations.
   value=5+.75*(template[pid]-5)
   for tag in mods[ix]: value+=affects[tag].get(pid,0)*1.2
   value=round(clamp(value)*2)/2
   score=f'{value:.1f}';lo=f'{max(0,value-4):.1f}';hi=f'{min(10,value+4):.1f}'
   confidence='very_low';reason='Subjective background hypothesis; template and explicit author modifiers, no text checked.'
  rows.append([person['d_id'],pid,score,lo,hi,confidence,'none',pcode,mods[ix],reason])

with (dest/'D300_ROLLCALL.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['d_id','pair_id','predicted_score_0_10','plausible_low','plausible_high','confidence','corpus_coverage','prior_template','author_cues','prediction_notes']);w.writerows(rows)
with (dest/'D300_AUTHORS.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['d_id','author','class','status','prior_template','author_cues','evidence_basis','notes'])
 for ix,p in enumerate(people,1):
  w.writerow([p['d_id'],p['author'],p['class'],p['status'],code[ix-1],mods[ix],'name and general literary background only','Translation-sensitive scores abstained where applicable; no membership lookup or text retrieval.'])

with (dest/'D300_DIRECT_10D.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['d_id','status','reason'])
 for p in people:w.writerow([p['d_id'],'abstain','Frozen 10D axis definitions, polarity, origin, and scale not supplied.'])
shutil.copyfile(lexicon,dest/'LEXICON.csv')
shutil.copyfile(manifest,dest/'MANIFEST.csv')
shutil.copyfile(prior,dest/'D24_TEMPLATE_GUESSES.csv')
shutil.copyfile(__file__,dest/'generation_code.py')
(dest/'METHOD.md').write_text('''# D300 background prediction freeze\n\nThis is a prospective *guess* panel, not a measured author corpus. The 300 names and IDs come only from the supplied predictive manifest. No A/B author inventory, A/B scores, C measurements, coordinates, or projection data were inspected during this pass. There is deliberately no post-freeze validation in this release. `FREEZE.json` hashes the input and output files before any such reveal.\n\nThe 48 pair IDs and operational definitions in `LEXICON.csv` are copied unchanged from the saved instrument. There is one prediction row per author × pair. Numerical scores are rough forecasts on the repository's A/B **empirical percentile** scale (5 = calibration median, not an absolute semantic midpoint). Empty scores mean abstention; they are never encoded as 5. Subjective ±4 plausible ranges are wide heuristic bands, not calibrated intervals. All numeric guesses carry very low confidence and no sampled corpus coverage. The authors were not checked for A/B membership.\n\nConstruction is intentionally auditable: each author has an explicit prospective `prior_template` and `author_cues`. The templates are earlier frozen Class D guesses, shrunk toward the median; lettered cues shift only named roll-call pairs by small amounts. They are based on general literary background, not text analysis or inferred latent axes. Shared templates create correlated and sometimes identical predictions; **these rows do not represent 10,000 independent judgments**. The code `make_d300.py` defines the exact mapping. O ornament; A abstractness; C categorical assertion; K compression; I intimacy; V adversarial tone; H emotional heat; T temporal motion; L nonlinear progression; Q dialogue; X explicit exposition.\n\nEleven pairs requiring stronger textual evidence are routinely abstained. Scores sensitive to English vocabulary and surface wording are additionally abstained for authors whose likely English evidence is translation dependent. D050 Dr. Seuss and D051 Maurice Sendak are left entirely unscored because their illustrated/verse work does not warrant a generic prose aggregate from background knowledge alone. Translation status here is a conservative forecast, not an edition-by-edition determination. Genre mixture, career change, translator variation, and celebrity reputation can substantially invalidate predictions.\n\n`D300_DIRECT_10D.csv` abstains for all 300. The manifest supplies no frozen 10D definitions, orientation, origin, or units. Direct numeric coordinates would be arbitrary. They can be created in a separate, independently frozen prediction stage once the axis specification is available, before any measured/projection reveal.\n''')

input_hash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (manifest,lexicon,prior)}
output_hash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in list(dest.glob('*.csv'))+[dest/'METHOD.md',dest/'generation_code.py']}
(dest/'FREEZE.json').write_text(json.dumps({'freeze_date_utc':datetime.now(timezone.utc).isoformat(),'phase':'predictions_only_before_any_AB_or_C_lookup','inputs_sha256':input_hash,'outputs_sha256':output_hash,'author_count':300,'pair_count':48,'numeric_predictions':sum(bool(r[2]) for r in rows),'abstentions':sum(not bool(r[2]) for r in rows),'direct_10D_status':'outside this pipeline'},indent=2)+'\n')
print('authors',len(people),'rows',len(rows),'numeric',sum(bool(r[2]) for r in rows),'null',sum(not bool(r[2]) for r in rows),'profile_dist',dict(Counter(code)))
