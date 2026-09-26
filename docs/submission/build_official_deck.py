"""Fill the byte-verified official SIH2026 template without altering its master/branding."""
from pathlib import Path
import sys, zipfile
from xml.sax.saxutils import escape
from defusedxml import minidom

HERE=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1])
OUT=HERE/'TwinGuard-Aero-SIH2026-Template-Draft.pptx'
EMU=914400
NS='xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
BLUE='1F4E79'; INK='172F42'; MUTED='526879'; PALE='EAF2F8'; AMBER='976008'

with zipfile.ZipFile(SOURCE) as z: files={n:z.read(n) for n in z.namelist()}
# Structural operation before editing content: remove the instructions slide.
pres=minidom.parseString(files['ppt/presentation.xml'])
ids=pres.getElementsByTagName('p:sldId')
last=ids[-1]; rid=last.getAttribute('r:id');last.parentNode.removeChild(last)
files['ppt/presentation.xml']=pres.toxml(encoding='UTF-8')
rels=minidom.parseString(files['ppt/_rels/presentation.xml.rels'])
for rel in list(rels.getElementsByTagName('Relationship')):
    if rel.getAttribute('Id')==rid:rel.parentNode.removeChild(rel)
files['ppt/_rels/presentation.xml.rels']=rels.toxml(encoding='UTF-8')
for n in list(files):
    if n in {'ppt/slides/slide7.xml','ppt/slides/_rels/slide7.xml.rels','ppt/notesSlides/notesSlide6.xml','ppt/notesSlides/_rels/notesSlide6.xml.rels'}:del files[n]
ct=minidom.parseString(files['[Content_Types].xml'])
for n in list(ct.getElementsByTagName('Override')):
    if n.getAttribute('PartName') in {'/ppt/slides/slide7.xml','/ppt/notesSlides/notesSlide6.xml'}:n.parentNode.removeChild(n)
files['[Content_Types].xml']=ct.toxml(encoding='UTF-8')


def all_shapes(d):
    tree=d.getElementsByTagName('p:spTree')[0]
    return [x for x in tree.childNodes if getattr(x,'tagName','') in {'p:sp','p:pic','p:graphicFrame'}]


def by_name(d,name):
    for s in all_shapes(d):
        p=s.getElementsByTagName('p:cNvPr')
        if p and p[0].getAttribute('name')==name:return s
    raise ValueError(name)


def pxml(t,size=18,color=INK,bold=False,after=7,align='l',font='Arial'):
    return f'<a:p><a:pPr algn="{align}" marL="0" indent="0"><a:lnSpc><a:spcPct val="112000"/></a:lnSpc><a:spcAft><a:spcPts val="{after*100}"/></a:spcAft><a:buNone/></a:pPr><a:r><a:rPr lang="en-US" sz="{int(size*100)}" b="{1 if bold else 0}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/></a:rPr><a:t xml:space="preserve">{escape(t)}</a:t></a:r><a:endParaRPr lang="en-US" sz="{int(size*100)}"/></a:p>'


def replace_text(s,paras,margin=.06,anchor='t'):
    d=s.ownerDocument; tx=s.getElementsByTagName('p:txBody')[0]
    for child in list(tx.childNodes):tx.removeChild(child)
    frag=minidom.parseString(f'<p:txBody {NS}><a:bodyPr wrap="square" lIns="{int(margin*EMU)}" rIns="{int(margin*EMU)}" tIns="{int(margin*EMU)}" bIns="{int(margin*EMU)}" anchor="{anchor}"><a:noAutofit/></a:bodyPr><a:lstStyle/>'+''.join(paras)+'</p:txBody>')
    for child in list(frag.documentElement.childNodes):tx.appendChild(d.importNode(child,True))


def move(s,x,y,w,h):
    xf=s.getElementsByTagName('a:xfrm')[0]
    off=xf.getElementsByTagName('a:off')[0];ext=xf.getElementsByTagName('a:ext')[0]
    for key,val in [('x',x),('y',y)]:off.setAttribute(key,str(int(val*EMU)))
    for key,val in [('cx',w),('cy',h)]:ext.setAttribute(key,str(int(val*EMU)))


def addbox(d,name,x,y,w,h,paras,fill=None,center=False):
    tree=d.getElementsByTagName('p:spTree')[0]
    maxid=max(int(n.getAttribute('id')) for n in d.getElementsByTagName('p:cNvPr'))+1
    bg=f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    src=f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{maxid}" name="{escape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{int(x*EMU)}" y="{int(y*EMU)}"/><a:ext cx="{int(w*EMU)}" cy="{int(h*EMU)}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>{bg}<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
    s=d.importNode(minidom.parseString(src).documentElement,True);tree.appendChild(s)
    replace_text(s,paras,margin=.14 if fill else .02,anchor='ctr' if center else 't')
    return s


def header(d,i):
    oval=[s for s in all_shapes(d) if s.getElementsByTagName('p:cNvPr')[0].getAttribute('name').startswith('Oval')][0]
    replace_text(oval,[pxml('MINDMESH',12,INK,True,0,'ctr')],.03,'ctr')

for i in range(1,7):
    name=f'ppt/slides/slide{i}.xml';d=minidom.parseString(files[name])
    if i==1:
        replace_text(by_name(d,'Subtitle 3'),[pxml('TwinGuard Aero',28,INK,True,0,'ctr','Garamond')],.02,'ctr')
        meta=by_name(d,'TextBox 9');move(meta,.48,2.24,6.70,5.04)
        replace_text(meta,[
            pxml('Problem Statement ID - SIH26054',19,INK,True,10),
            pxml('Problem Statement Title',17,BLUE,True,4),
            pxml('AI-Enabled Real-Time Digital Twin System for Health Monitoring, Fault Prediction and Mission Reliability Enhancement of Aero Piston Engines used in MALE UAVs.',18,INK,False,12),
            pxml('Theme - Robotics and Drones',18,INK,True,10),
            pxml('PS Category - Software',18,INK,True,10),
            pxml('Team ID - CONFIRM FROM PORTAL',18,AMBER,True,10),
            pxml('Team Name - MINDMESH',18,INK,True,5),
            pxml('Synthetic prototype | Engine-specific validation planned',14,MUTED,False,0),
        ])
    else:
        header(d,i)
        body=by_name(d,'TextBox 8')
        if i==2:
            title=by_name(d,'Title 1');replace_text(title,[pxml('TwinGuard Aero',32,'000000',True,0,'ctr','Garamond')],.03,'ctr')
            move(body,.55,1.54,8.08,5.08)
            replace_text(body,[
                pxml('Proposed Solution (Describe your Idea/Solution/Prototype)',18,BLUE,True,13),
                pxml('Detailed explanation of the proposed solution',18,BLUE,True,5),
                pxml('A synchronized aero-piston twin combines a healthy reference, residual trends, Sensor Trust and explainable condition assessment.',18,INK,False,14),
                pxml('How it addresses the problem',18,BLUE,True,5),
                pxml('Inspect the evidence behind a warning; compare the same mission before and after degradation; retain observations for review.',18,INK,False,14),
                pxml('Innovation and uniqueness of the solution',18,BLUE,True,5),
                pxml('Connect measurement trust, subsystem evidence and profile consequences in one traceable operator workflow.',18,INK,False,0),
            ])
            for n,(t,b) in enumerate([('TRUST','Freshness + signal consistency'),('CONDITION','Residuals + temporal evidence'),('MISSION','State-dependent profile comparison')]):
                addbox(d,f'Twin layer {n}',9.05,1.83+n*1.29,3.62,1.05,[pxml(t,20,BLUE,True,8,'ctr'),pxml(b,16,INK,False,0,'ctr')],PALE,True)
            addbox(d,'Prototype scope',9.05,5.79,3.62,.64,[pxml('Synthetic evidence; human review',14,AMBER,True,0,'ctr')])
        elif i==3:
            move(body,.58,1.52,12.20,1.30)
            replace_text(body,[
                pxml('Technologies to be used (e.g. programming languages, frameworks, hardware)',18,BLUE,True,8),
                pxml('React / TypeScript + Three.js; Python / FastAPI + WebSockets; SQLite locally; Docker / PostgreSQL path. Optional synthetic Isolation Forest and XGBoost models.',18,INK,False,0),
            ])
            addbox(d,'Methodology pointer',.60,3.05,12.12,.75,[pxml('Methodology and process for implementation (Flow Charts/Images/ working prototype)',18,BLUE,True,0)])
            entries=[('Telemetry','Simulator / authorized adapter'),('Validate','Identity, timestamps and units'),('Hybrid twin','Reference, residuals and health'),('Review','Mission analysis + evidence')]
            for n,(t,b) in enumerate(entries):
                addbox(d,f'Pipeline {n}',.62+n*3.18,3.87,2.88,1.18,[pxml(t,21,BLUE,True,7,'ctr'),pxml(b,16,INK,False,0,'ctr')],PALE,True)
                if n<3:addbox(d,f'Arrow {n}',3.49+n*3.18,4.17,.32,.55,[pxml('>',23,BLUE,True,0,'ctr')])
            addbox(d,'Modes',.63,5.46,12.03,.87,[pxml('HOSTED: browser synthetic demonstration  |  LOCAL: authenticated backend + persistence',17,INK,True,8),pxml('Evaluation Center: baseline capture → progressive fault → comparison → source-labeled JSON export.',17,INK,False,0)])
            addbox(d,'Data hold',.65,6.51,12.02,.30,[pxml('Freshness and quality gate decisions. Insufficient live evidence produces DATA HOLD.',14,AMBER,True,0)])
        elif i==4:
            move(body,.60,1.53,12.05,1.25)
            replace_text(body,[pxml('Analysis of the feasibility of the idea',19,BLUE,True,8),pxml('Implemented software demonstrator: telemetry contract, explainable analytics, mission comparison, replay and evidence export. Modular replacement of the generic reference supports later calibration.',18,INK,False,0)])
            addbox(d,'Challenges',.62,3.09,12.03,1.54,[pxml('Potential challenges and risks',19,BLUE,True,8),pxml('No authorized real-engine labels yet. Physics and synthetic training share assumptions. RUL bands and mission scores are uncalibrated. Current runtime serves one configured engine.',18,INK,False,0)],PALE)
            addbox(d,'Strategies',.62,4.76,12.03,1.42,[pxml('Strategies for overcoming these challenges',19,BLUE,True,8),pxml('Read-only rig integration → verified channels and independent labels → engine-map calibration → held-out threshold/hybrid comparison → hardware-in-the-loop and security review.',18,INK,False,0)])
            addbox(d,'Metrics plan',.63,6.37,12.05,.36,[pxml('Planned measures: false alarms/hour, fault recall, warning lead time, RUL coverage and hardware latency.',14,AMBER,True,0)])
        elif i==5:
            move(body,.62,1.53,12.00,.47)
            replace_text(body,[pxml('Potential impact on the target audience',20,BLUE,True,0)])
            for n,(t,b) in enumerate([('UAV operators','See data readiness and the evidence behind a changing engine condition.'),('Propulsion engineers','Inspect operating-context residuals and compare modelled profiles.'),('Maintenance teams','Review recorded events, probable conditions and engineering guidance.')]):
                addbox(d,f'Audience {n}',.62+n*4.20,2.20,3.87,1.63,[pxml(t,22,BLUE,True,10),pxml(b,16,INK,False,0)],PALE)
            addbox(d,'Benefits pointer',.63,4.13,12.02,.70,[pxml('Benefits of the solution (social, economic, environmental, etc.)',20,BLUE,True,0)])
            benefits=[('Reliability research','Earlier engineering review and better use of condition history.'),('Engineering efficiency','A repeatable scenario and reusable evidence trail for diagnosis.'),('Resource stewardship','Potential for condition-led maintenance; savings require field measurement.')]
            for n,(t,b) in enumerate(benefits):
                addbox(d,f'Benefit {n}',.63+n*4.20,4.99,3.86,1.30,[pxml(t,18,BLUE,True,8),pxml(b,17,INK,False,0)])
            addbox(d,'Impact boundary',.65,6.52,12.00,.27,[pxml('Intended benefits, not measured fleet outcomes. No claimed percentage reduction in failures, cost or fuel.',14,AMBER,True,0)])
        elif i==6:
            move(body,.63,1.52,12.0,.55)
            replace_text(body,[pxml('Details / Links of the reference and research work',20,BLUE,True,0)])
            refs=[
                ('Official SIH26054 problem statement','sih.gov.in/sih2026PS','Scope and deliverables for the selected DRDO challenge.'),
                ('NIST - Digital twins','nist.gov/digital-twins','Digital-twin concepts, essential elements and validation context.'),
                ('IsolationForest - scikit-learn documentation','scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html','Anomaly-model implementation reference.'),
                ('Chen & Guestrin (2016) - XGBoost','arxiv.org/abs/1603.02754','Tree-boosting method used by the optional synthetic model pipeline.'),
                ('TwinGuard Aero - source, model card and validation','github.com/krishnatayal1410/twinguard-aero','Inspect implementation, generic-model assumptions and reproducible checks.'),
            ]
            for n,(t,u,desc) in enumerate(refs):
                shape=addbox(d,f'Reference {n}',.67,2.17+n*.82,12.0,.80,[],PALE if n%2==0 else None)
                replace_text(shape,[pxml(t,15,BLUE,True,1),pxml(u,12,BLUE,False,1),pxml(desc,12,MUTED,False,0)],margin=.04)
            addbox(d,'Validation reminder',.68,6.50,11.95,.27,[pxml('References support the approach; they do not validate this prototype on real engines.',14,AMBER,True,0)])
    files[name]=d.toxml(encoding='UTF-8')

# Remove the orphaned instruction-slide notes and stale slide count metadata, if any.
app=minidom.parseString(files['docProps/app.xml'])
for n in app.getElementsByTagName('Slides'):
    if n.firstChild:n.firstChild.nodeValue='6'
files['docProps/app.xml']=app.toxml(encoding='UTF-8')
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in files.items():z.writestr(n,b)
print(OUT)
