"""Rebuild the six-page supporting brief; not the official SIH upload template."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'TwinGuard-Aero-Evaluator-Brief.pdf'
W, H = 960, 540
NAVY = HexColor('#10273A')
BLUE = HexColor('#2668BF')
TEAL = HexColor('#007D7B')
MUTED = HexColor('#586C7B')
PALE = HexColor('#EDF4F8')
LINE = HexColor('#D8E3EA')
AMBER = HexColor('#996416')
C = canvas.Canvas(str(OUT), pagesize=(W, H))
C.setTitle('TwinGuard Aero | SIH26054 Evaluator Brief')
C.setAuthor('TwinGuard Aero')
C.setSubject('Supporting synthetic digital-twin demonstrator brief; not an official SIH template')


def text(t, x, y, width, size=15, color=NAVY, leading=None, bold=False):
    style = ParagraphStyle('body', fontName='Helvetica-Bold' if bold else 'Helvetica', fontSize=size,
                           leading=leading or size * 1.36, textColor=color)
    p = Paragraph(t, style)
    _, height = p.wrap(width, H)
    p.drawOn(C, x, y-height)
    return height


def rect(x, y, w, h, color=PALE, radius=10):
    C.setFillColor(color)
    C.roundRect(x, y, w, h, radius, fill=1, stroke=0)


def line(x1,y1,x2,y2,color=LINE,width=1):
    C.setStrokeColor(color); C.setLineWidth(width); C.line(x1,y1,x2,y2)


def base(n, section, title, subtitle):
    C.setFillColor(white); C.rect(0,0,W,H,fill=1,stroke=0)
    C.setFillColor(TEAL); C.rect(0,H-8,W,8,fill=1,stroke=0)
    text('TWINGUARD AERO',42,505,380,11,TEAL,bold=True)
    text(section.upper(),690,505,228,10,MUTED,bold=True)
    text(title,42,469,876,31,NAVY,bold=True)
    text(subtitle,42,423,876,14,MUTED)
    line(42,40,918,40)
    text('SIH26054 | Supporting material - not the official submission template',42,28,740,9,MUTED)
    text(f'26 SEP 2026  /  {n:02d}',795,28,123,9,MUTED,bold=True)


def card(x,y,w,h,kicker,title,body,color=TEAL):
    rect(x,y,w,h)
    text(kicker.upper(),x+18,y+h-17,w-36,10,color,bold=True)
    text(title,x+18,y+h-43,w-36,20,NAVY,bold=True)
    text(body,x+18,y+h-78,w-36,13,MUTED)

# 1: A concise proposition with explicit scope.
C.setFillColor(NAVY); C.rect(0,0,W,H,fill=1,stroke=0)
C.setFillColor(TEAL); C.rect(0,H-8,W,8,fill=1,stroke=0)
text('SIH26054  /  DRDO  /  SOFTWARE',44,503,850,12,HexColor('#87D9D4'),bold=True)
text('TwinGuard Aero',44,454,860,44,white,bold=True)
text('From an engine reading<br/>to a reviewable decision.',44,386,820,31,white,bold=True)
text('An explainable digital-twin demonstrator linking measurement trust, engine condition and mission-profile consequences.',44,284,825,17,HexColor('#C5D6E0'))
for i,(k,t,b) in enumerate([
    ('01','Trust the evidence','Freshness, quality and related-signal consistency.'),
    ('02','Explain the condition','Healthy reference, residuals and temporal evidence.'),
    ('03','Compare the profile','Same mission, changed engine state, rescored alternative.')]):
    x=44+i*295
    rect(x,97,280,131,HexColor('#1A374C'))
    text(k,x+16,211,240,11,HexColor('#87D9D4'),bold=True)
    text(t,x+16,185,249,18,white,bold=True)
    text(b,x+16,154,245,12,HexColor('#C5D6E0'))
text('CURRENT SCOPE  Synthetic proof-of-concept. Generic engine model. Human engineering review.',44,75,850,11,HexColor('#A6C4D3'))
line(44,40,916,40,HexColor('#355268'))
text('Supporting material - not the official SIH submission template',44,28,725,9,HexColor('#C5D6E0'))
text('26 SEP 2026  /  01',795,28,123,9,HexColor('#C5D6E0'),bold=True)
C.showPage()

# 2: System structure and deployment distinction.
base(2,'Architecture','The analytical twin is behind the interface.','One canonical state connects data integrity, expected behavior, diagnosis and engineering review.')
nodes=[
    ('01','Telemetry contract','Identity, timestamp, units and validated channels'),
    ('02','Healthy reference','Generic operating-condition-aware aero-piston surrogate'),
    ('03','Residual evidence','Observed minus expected; trends and Sensor Trust'),
    ('04','Condition assessment','Subsystem health, probable fault and model provenance'),
    ('05','Mission comparison','Simulation RUL, profile stress and rescored alternative'),
    ('06','Reviewable record','Replay, offline evaluation and evidence export'),
]
for i,(k,t,b) in enumerate(nodes):
    col=i%3; row=i//3
    card(42+col*298,237-row*142,280,128,k,t,b)
    if col<2:
        text('>',326+col*298,312-row*142,14,20,TEAL,bold=True)
text('<b>Data gate:</b> stale or low-quality live state becomes DATA HOLD. A connected browser alone is not evidence of fresh measurements.',44,82,872,12,NAVY)
C.showPage()

# 3: New feature flow and evidence semantics.
base(3,'Demonstration','A repeatable scenario, with a record of what changed.','Hosted Evaluation Center: baseline, progressive fault, comparison and exported evidence.')
steps=[('1','Capture baseline','Start from the healthy browser simulator and preserve its complete state.'),
       ('2','Apply lubrication loss','Choose the fault and intensity. Observe the progressive synthetic change.'),
       ('3','Inspect + capture','Compare pressure residual, vibration, health and RUL with baseline.'),
       ('4','Export evidence','Download state, units, provenance, scenario inputs and a SHA-256 checksum.')]
for i,(n,t,b) in enumerate(steps):
    x=42+i*224
    rect(x,189,210,187)
    text(n,x+17,358,174,26,TEAL,bold=True)
    text(t,x+17,311,176,18,NAVY,bold=True)
    text(b,x+17,259,176,12,MUTED)
rect(42,74,876,94,HexColor('#F3F7FA'))
text('What this evidence can establish',60,153,386,14,TEAL,bold=True)
text('The recorded state and model assumptions behind this demonstrator run. It supports inspection and repeatability.',60,127,386,12,MUTED)
text('What it cannot establish',503,153,397,14,AMBER,bold=True)
text('Independent classifier accuracy or real-engine validity. A checksum detects changes; it does not authenticate the data source.',503,127,397,12,MUTED)
C.showPage()

# 4: Claims and model boundaries.
base(4,'Technical credibility','Make the model assumptions inspectable.','A confident presentation distinguishes implementation evidence from operational validation.')
rows=[
    ('Healthy reference','Generic low-order surrogate','Calibrate with authorized maps and independent rig data'),
    ('Diagnostic runtime','Engineering fallback or compatible synthetic ML','Show the active mode; do not imply an unused model ran'),
    ('Remaining useful life','Simulation-derived estimate and sensitivity band','Validate against longitudinal degradation / maintenance evidence'),
    ('Mission feasibility','Engineering index for profile comparison','Not a calibrated probability of mission success'),
    ('CAN integration','Configurable adapter and canonical schema','Needs authorized DBC, channel validation and rig testing'),
]
y=365
for i,(name,current,nextstep) in enumerate(rows):
    if i%2==0: rect(42,y-53,876,56,PALE,4)
    text(name,55,y-8,174,13,NAVY,bold=True)
    text(current,245,y-8,274,13,TEAL)
    text(nextstep,542,y-8,360,12,MUTED)
    y-=61
text('The simulator and healthy-reference model share assumptions. Synthetic agreement alone does not establish real-engine generalization.',44,65,869,12,AMBER,bold=True)
C.showPage()

# 5: Evidence first experiment design.
base(5,'Validation plan','The next strongest proof is an independent recording.','Compare methods on the same held-out runs, preserve failure cases and report the denominator.')
card(42,244,426,130,'Experiment design','Threshold baseline vs hybrid twin','Compare fixed thresholds, operating-context residuals, temporal evidence and the complete Sensor Trust workflow.')
card(490,244,428,130,'Leakage control','Hold out complete runs','Separate operating conditions and ultimately engines. Do not randomly split adjacent samples from the same fault trajectory.')
metrics=[('False alarms','Per operating hour, with normal transients included'),
         ('Fault detection','Per-fault precision / recall and missed detections'),
         ('Useful warning','Time to stable alert and lead time to labeled event'),
         ('RUL / uncertainty','Error and coverage only where reference truth exists'),
         ('Deployment cost','p50/p95 latency, CPU and memory at measured load')]
y=223
for label,body in metrics:
    text(label,54,y,178,13,TEAL,bold=True)
    text(body,257,y,644,13,MUTED)
    y-=29
text('Acceptance targets should be agreed with the target-engine partner before final testing. No unmeasured performance target is presented as an achieved result.',44,65,870,12,AMBER)
C.showPage()

# 6: Deployment modes and staged path.
base(6,'Delivery and next steps','Accessible today. Engine-specific validation next.','Two explicit execution modes keep the presentation accessible and the technical boundary honest.')
card(42,256,426,121,'Hosted demonstration','Browser synthetic runtime','An accessible evaluator workflow with controlled scenarios. It is not a live ECU connection.')
card(490,256,428,121,'Local / controlled environment','Backend integration workflow','FastAPI, authenticated APIs, WebSockets and persistence. Current scope: one configured engine and process.')
road=[('NOW','Reproducible release','Source, working flows, versioned software checks and synthetic evidence.'),
      ('NEXT','Authorized read-only rig','Confirm channels and timing; calibrate healthy behavior; collect independent labels.'),
      ('THEN','Validated deployment','Held-out diagnosis and RUL studies, HIL, recovery/security tests and domain assurance.')]
for i,(a,b,d) in enumerate(road):
    x=42+298*i
    text(a,x+3,229,271,10,TEAL,bold=True)
    text(b,x+3,205,271,18,NAVY,bold=True)
    text(d,x+3,172,271,12,MUTED)
line(42,105,918,105)
text('PS identity and high-level scope: sih.gov.in/sih2026PS',44,92,870,10,MUTED)
C.linkURL('https://sih.gov.in/sih2026PS',(44,76,500,95),relative=0,thickness=0)
text('A separate draft follows the verified SIH2026 template. Its team ID must be confirmed before portal submission.',44,68,870,11,AMBER)
C.showPage()
C.save()
print(OUT)
