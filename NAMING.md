# The Naming of RecogCore

*Not linked from PLAN.md or anywhere else in this repo — this document exists purely to honor
the effort that went into picking a name before a single line of code was written.*

---

## The Trials

Every great system deserves a name earned through trial, not assigned by convenience. Before
`recog_core` ever imported a single `cv2` frame, the project survived six rounds of naming,
roughly **85 candidate names**, two dismissed rounds of clarifying questions, and a live
trademark/GitHub due-diligence sweep — before finally being crowned **RecogCore**.

### Round 1 — The Placeholder Era
The project began life quietly as **"Foyer"** — a working name chosen for its literal fit (an
entryway is where a host recognizes and greets guests) and nothing more. It served its purpose
as scaffolding across eleven phase-planning documents, patiently waiting to be replaced.

### Round 2 — The Hospitality Pass
Asked to root the name in Indian culture, four candidates were offered first —
**Atithi, Dwarpal, Sakha, Vishwas** — each carrying real philosophical weight (guest-as-god,
temple gatekeepers, sacred friendship, trust itself). The offer was dismissed outright. A
follow-up asking *what specifically* was wrong was dismissed a second time. The lesson: stop
asking, start delivering.

### Round 3 — The Flood
Thirty names followed — organized into Hospitality, Guardian, Companion, Vision, and Light &
Warmth — spanning Sanskrit, Hindi, and Urdu, complete with etymology and mythological color
(temple guardians, Diwali lamps, Rajasthani welcome invocations). Verdict: still all Hindi
despite being told otherwise wasn't required, and far too "dramatic" for a professional
open-source project. A hard reset was called for.

### Round 4 — The Professional Pivot
Twenty-five plain-English, HashiCorp-style names followed — *Threshold, Sentinel, Vestibule,
Concierge, Herald,* and others — with **Envoy** and **Sentry** flagged and set aside as already
claimed by major existing projects. This register finally landed.

### Round 5 — The Mashup Detour
Asked for something blending "Foyer" and "Recognet," four literal portmanteaus were produced —
**Foynet, Foynition, Foynize, Recoyer**. Rejected: not a letter-mashup, a *philosophy* mashup.
Twelve names followed instead — **Vantage, Threshold, Vestibule, Aperture, Overture, Advent,
Cognate, Reception, Frontdesk, Attendant, Registrar, Herald** — each built from the idea of a
threshold that recognizes, not the syllables of two words stitched together.

### Round 6 — Going Technical
A final pivot requested an engineering-style name. Twelve infra/ML-flavored candidates were
drafted — **VisionGate, PresenceCore, EdgeSense, RecogCore, KinFace, GateVision, PerceiveIO,
SenseHub, PresenceEngine, EdgeGreet, GreetOS, VisionDaemon** — following the naming conventions
of real ML libraries (`OpenFace`, `FaceNet`) and infra tools (`systemd`-style daemons,
`-core`/`-engine` suffixes).

## The Reckoning

Twelve finalists went to trial by live web search. The casualties were substantial:

| Name | Fate |
|---|---|
| VisionGate | Claimed — a lung-cancer diagnostics biotech company |
| PresenceCore | Claimed — a component inside an existing ESP32 open-source project |
| EdgeSense | Claimed — a registered retail shelf-system trademark (EdgeSense™) |
| GateVision | Claimed — a registered port-terminal trademark (GateVision®) |
| PerceiveIO | Claimed — collides with DeepMind's Perceiver IO architecture |
| SenseHub | Claimed — an existing open-source sensory-analysis web app |
| PresenceEngine | Claimed — a named component inside an existing macOS app |
| KinFace | Compromised — an established academic kinship-recognition term |
| GreetOS | Survived — but read as implying an entire operating system |
| VisionDaemon | Survived — but read as an internal systems component, not a product |
| EdgeGreet | Survived — clean, but weaker fit than the winner |
| **RecogCore** | **Survived. Crowned.** |

## The Verdict

**RecogCore** — the recognition engine at the center of the system — emerged as the one name
across all six rounds and ~85 candidates that was simultaneously: engineering-flavored,
unclaimed by any biotech company, port-terminal system, retail trademark, ML architecture, or
Linux daemon, and an honest, literal description of what `recog_core` actually does.

Long may it run.
