"""
Light gun shell - parametric CadQuery model.

Coordinates: X = forward (muzzle), Y = left (+) / right (-), Z = up.
Split plane Y = 0.  Left half (Y>0) takes the heat-set inserts, right half (Y<0) the screw heads.
All dimensions in millimetres.

build() returns (shell, left_half, right_half).  trigger(), mosfet_clip() and guard_overlay()
return the separately printed parts; components() returns placeholder solids for clearance checks.
"""
import math
import cadquery as cq

# ---------------------------------------------------------------- general
WALL = 2.4
CLR = 0.3                 # fit clearance for printed parts
W = 44.0                  # overall width of body and grip (flat sides print on the bed)
HW = W / 2
IHW = HW - WALL           # inner half width

# ---------------------------------------------------------------- body
BODY_L = 186.0            # rear face X=0 -> muzzle face
BODY_H = 42.0
ROOF_TOP = 45.5
ROOF_HALF = 6.0           # half width of the flat rail top

# ---------------------------------------------------------------- camera (SEN0158, M18)
CAM_D = 18.0
CAM_HOLE = 18.6
CAM_LEN = 32.0
CAM_Z = 21.0
CAM_PROTRUDE = 8.0        # how far the camera tip sticks out past the muzzle face
NUT_AF = 24.0             # across flats of the M18 nut (nominal)
NUT_T = 4.0               # nut thickness (nominal)
FRONT_WALL = 3.0
NUT_POCKET_T = NUT_T + 0.5
NUT_POCKET_AF = NUT_AF + 0.4
REAR_RIB = 3.0
FRONT_BLOCK_X0 = BODY_L - FRONT_WALL - NUT_POCKET_T - REAR_RIB

# ---------------------------------------------------------------- solenoid JF-1039B
SOL_L, SOL_W, SOL_H = 39.5, 26.3, 20.0   # length (X), width (Y), height (Z)
SOL_X0 = 27.0            # leaves room behind for the fired rear plunger
SOL_Z0 = 14.0
WIRE_NOTCH_Y = 11.0               # wire channel over the solenoid: notch in both cradle ribs,
WIRE_NOTCH_Z0 = 35.0              #   above the solenoid's top face (z 34), clear of its cradle
SOL_AXIS_Z = SOL_Z0 + SOL_H / 2
PLUNGER_D = 9.0
PLUNGER_FRONT = 25.0      # front sticks out 25 mm at rest
NUB_REAR = 10.0           # rear sticks out 10 mm at rest (74.5 - 39.5 - 25)
SOL_STROKE = 10.0         # rear sticks out 20 mm when fired

# ---------------------------------------------------------------- ESP32 devkit
ESP_L, ESP_W, ESP_T = 51.7, 28.3, 12.6
ESP_X0 = 99.0
ESP_PCB_Z = 33.0          # underside of the PCB
ESP_PCB_T = 1.6
ESP_SIDE_CLR = 0.2                # per side: the side guides hold the board 28.3 + 0.4 mm apart

# ---------------------------------------------------------------- 3.3 V buck converter (in the bay under the ESP32)
BUCK_L, BUCK_W = 22.5, 16.7       # long side front-to-back, short side up-and-down
BUCK_CLR = 0.2                    # per side
BUCK_RIM_H = 2.5                  # rim stands this far off the left wall: holds the PCB edge (with or without tape)
BUCK_RIM_T = 1.2
BUCK_X = 137.5                    # centre of the pocket
BUCK_Z = WALL + (BUCK_W + 2 * BUCK_CLR) / 2 + BUCK_RIM_T   # rim sits on the body floor
BUCK_GAP = 8.0                    # wire openings in the middle of both short sides

# ---------------------------------------------------------------- MOSFET (TO-220), pinned to the right wall at the rear
MOS_X = 18.5                      # behind the solenoid, between the rear boss and the rear cradle rib
MOS_ZB = 3.0                      # bottom edge of the tab, just above the floor (beside the power switch, not above it)
MOS_LEGS = 7.0                    # legs trimmed to about this after soldering (they point up)
MOS_TOP = -IHW                    # tab lies flat on the right wall
MOS_PIN_D = 3.2                   # pin through the tab hole (hole is 3.6)
MOS_NECK_D = 2.2                  # groove the clip snaps into
CLIP_T = 1.0                      # clip thickness
CLIP_PLAY = 0.15                  # axial play so the clip slides in
MOS_HEAD_L = 1.0                  # pin head above the groove
CLIP_L, CLIP_W = 12.0, 5.5        # fork clip: length (slides in along x) and width
CLIP_TIP = 3.5                    # neck seat is this far from the fork's open end
TO220_W = 10.54                   # package width, datasheet maximum (10.29-10.54)
TO220_HOLE_TO_TOP = 2.9           # tab hole centre to the top edge of the tab
MOS_Z = MOS_ZB + TO220_HOLE_TO_TOP   # tab hole centre

# ---------------------------------------------------------------- rocker power switch (KCD11 style)
SW_CUT_Y, SW_CUT_Z = 13.1, 8.5    # panel cut-out: 13.1 wide x 8.5 tall
SW_PANEL = 1.6                    # wall is thinned to this around the hole so the snap clips can grab
SW_Z = 9.8
SW_DEPTH = 18.0

# ---------------------------------------------------------------- printed trigger + roller microswitch + torsion spring
# The trigger pivots on pins moulded into the shell. Pulling it swings the arm above the pivot forward
# into the switch roller. The tail behind the pivot rests on the body floor (rest stop) and hits a rib
# in the right half when fully pulled (pull stop). The torsion spring pushes the tail back down.
PIV_X, PIV_Z = 98.0, 7.0          # pivot centre
TRIG_T = 6.0                      # printed trigger thickness (Y)
PIV_PIN_D = 4.0                   # pins on the shell
PIV_HOLE_D = 4.4                  # hole in the trigger
PULL_DEG = 14.3                   # tuned so full pull pushes the roller to PRESS_TO
SLOT_X0, SLOT_X1 = 89.0, 106.5    # opening in the body floor
# roller microswitch (Omron SS-5GL2 pattern: 19.8 x 10.2 x 6.4, holes 2.35 dia, 9.5 apart, 2.9 from terminal edge)
MS_L, MS_H, MS_T = 19.8, 10.2, 6.4
ARM_FRONT_X = 101.0               # front face of the trigger arm at rest
ROLLER_SLACK = 0.8                # free play between trigger arm and roller at rest
MS_Z0 = 2.6                       # bottom end of the switch
MS_HOLE_FROM_TERM = 2.9
MS_HOLE_ENDS = (5.1, 14.6)        # hole positions along the switch length
MS_PEG_D = 2.2
ROLLER_D = 6.6                    # 6.5-6.8
ROLLER_FREE = 10.5                # top of roller 10.5 mm from the switch body when free
ROLLER_FLAT = 0.4 + ROLLER_D      # roller top when the lever lies flat on the body (lever ~0.4 mm)
PRESS_TO = ROLLER_FLAT + 0.5      # full pull pushes the roller to here: past any click point, short of flat
MS_REAR_X = ARM_FRONT_X + ROLLER_SLACK + ROLLER_FREE   # lever/roller face of the switch
ROLLER_ALONG = 18.7               # roller centre from the hinge end (hinge at the bottom)
# torsion spring
SPR_X, SPR_Z = 85.0, 10.5         # set so the coil clears the solenoid
SPR_BORE = 6.4                    # inner diameter of the coil
SPR_POST_D = 6.2                  # snug in a 6.4 mm bore
SPR_POST_TIP_D = 5.4              # lead-in taper so the coil starts easily
SPR_TAPER = 1.2                   # length of that taper
SPR_Y0 = 7.0                      # post tip, set so the plunger's return spring clears (see SPR_CLEAR_D)
SPR_COIL_OD, SPR_COIL_L = 8.2, 12.0   # OD from bore plus wire; conservative for clearance checks
# anchor fins for the long leg; any one sets the return force
SPR_FIN_DEG = (40.0, 70.0, 100.0, 130.0)
SPR_FIN_R0, SPR_FIN_R1 = 7.5, 11.0   # fin reach, kept clear of the plunger
SPR_FIN_T = 2.4                   # fin thickness
STOP_X0, STOP_X1 = 82.6, 92.0     # pull stop rib
STOP_H = 3.2                      # rib height (kept low so it stays clear of the plunger)
STOP_WEB_X0, STOP_WEB_X1 = 78.0, 82.6   # gusset web tying the rib down to the floor
STOP_WEB_Y1 = -6.0                # web stops short of the centre, leaving a wire channel
SPR_FIN_Y0 = 14.6                 # fins stand 5.0 mm proud of the wall
SPR_CLEAR_D = 2 * SPR_FIN_Y0      # max diameter of anything on the front plunger
LEDGE_Y1 = 9.5                    # spring ledge spans the post, so the short leg lands on it at any angle

# ---------------------------------------------------------------- grip
RAKE = math.radians(16.0)
G0X = 58.0                # grip centreline crosses body bottom (Z=0) here
BAT_D, BAT_W, BAT_L = 42.6, 38.5, 77.8   # holder pack (front-back, side-side, length)
BAT_WIRES_D = 44.6                       # front-back including the wires and BMS on its side
CAV_D = 46.0                             # grip cavity front-back (unchanged outside size)
CAV_W = 39.5                             # grip cavity side-to-side (unchanged outside size)
BAT_HEADROOM = 2.0                       # free space between the pack and the stop tabs above it
G_OUT_D = CAV_D + 2 * WALL
SHELF_U = 76.0                       # battery rests here (grip length unchanged)
BAT_U_TOP = SHELF_U - BAT_L
U_BOT = SHELF_U + 19.5               # outer bottom of the butt
FLARE = 3.0

# ---------------------------------------------------------------- charger Z-6732
CHG_L, CHG_W, CHG_STACK = 31.0, 17.4, 4.1   # measured on the printed part: 1 mm shorter, and the
                                            # board sits 3 mm higher than first modelled
CHG_PORT_OUT = 2.0                # USB-C connector overhangs the board by this much
CHG_PORT_H = 3.3                  # height of the USB-C connector body
# the board goes in with its USB-C connector on the side facing the body (up the grip)
PORT_W, PORT_H_MM = 8.5, 2.7      # visible opening: a USB-C plug shell is 8.34 x 2.56 mm
PORT_U_ADJ = -0.1                 # offsets the opening from the connector centre
PORT_W_IN, PORT_H_IN = 9.8, 3.8   # opened out behind the face so the connector itself clears
PORT_STEP = 0.8                   # depth of the narrow section
PORT_CHAMFER = 0.6
# board position is set by the port: the connector ends just behind the narrow section,
# so its mouth is PORT_STEP below the outside face and a plug seats fully
CHG_V0 = -G_OUT_D / 2 + PORT_STEP + CHG_PORT_OUT
BOSS_OD = 9.0
BOSS_SINK = 1.0          # butt bosses sink into the floor (avoids tangent contact)
BRD_U = U_BOT - WALL - BOSS_OD + BOSS_SINK - 3.0   # underside of the charger board

# ---------------------------------------------------------------- screws / inserts
INSERT_D = 4.1            # hole for M3 heat-set insert (insert OD 4.7 mm)
INSERT_DEPTH = 6.5
INSERT_LEAD_D = 4.5               # wider mouth: the insert's smooth pilot end sits in here, straight, before heating
INSERT_LEAD_L = 1.5
INSERT_CHAMFER = 0.4
SCREW_CLR = 3.3
HEAD_CB = 6.2             # counterbore for M3 socket head
SCREW_GRIP = 7.0          # length of right-half boss the screw passes through -> M3x12

# ---------------------------------------------------------------- helpers
def g2w(v, u):
    """grip-local (v forward, u down along axis) -> world (X, Z)"""
    s, c = math.sin(RAKE), math.cos(RAKE)
    return (G0X + v * c - u * s, -v * s - u * c)

def grip_box(v0, v1, u0, u1, y0, y1, ch=0.0):
    """axis-aligned box in grip-local coords, returned in world coords"""
    b = cq.Workplane("XY").box(v1 - v0, y1 - y0, u1 - u0, centered=False)
    if ch:
        b = b.edges("|Z").chamfer(ch)
    b = b.translate((v0, y0, -u1))                  # local: x=v, y=y, z=-u
    b = b.rotate((0, 0, 0), (0, 1, 0), math.degrees(RAKE))  # tilt so bottom goes back
    return b.translate((G0X, 0, 0))

def grip_cyl_v(v0, v1, u_c, y_c, d):
    """cylinder whose axis runs along the grip's v axis, in grip-local coords"""
    c = (cq.Workplane("YZ").center(y_c, -u_c).circle(d / 2)
         .extrude(v1 - v0).translate((v0, 0, 0)))
    c = c.rotate((0, 0, 0), (0, 1, 0), math.degrees(RAKE))
    return c.translate((G0X, 0, 0))


def grip_obround(v0, v1, u_c, y_c, w, h):
    """stadium-shaped hole (USB-C outline): width w, height h, fully rounded ends"""
    flat = w - h
    s = grip_box(v0, v1, u_c - h / 2, u_c + h / 2, y_c - flat / 2, y_c + flat / 2)
    s = s.union(grip_cyl_v(v0, v1, u_c, y_c - flat / 2, h))
    s = s.union(grip_cyl_v(v0, v1, u_c, y_c + flat / 2, h))
    return s


def gcyl_y(v, u, d, y0, y1):
    x, z = g2w(v, u)
    return cq.Workplane("XZ").center(x, z).circle(d / 2).extrude(-(y1 - y0)).translate((0, y0, 0))

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def cyl_y(x, z, d, y0, y1):
    return cq.Workplane("XZ").center(x, z).circle(d / 2).extrude(-(y1 - y0)).translate((0, y0, 0))

def cyl_x(y, z, d, x0, x1):
    return cq.Workplane("YZ").center(y, z).circle(d / 2).extrude(x1 - x0).translate((x0, 0, 0))

def side_extrude(pts, y0, y1):
    return cq.Workplane("XZ").polyline(pts).close().extrude(-(y1 - y0)).translate((0, y0, 0))


# ======================================================================== outer shape
GUARD_HW = 5.0                    # guard is 10 mm wide: its side faces are at y = +/-5
OVERLAY_T = 1.0                   # colour overlay thickness
OVERLAY_INSET = 0.4               # pulled in from every edge so the piece cannot overhang the guard


def guard_profiles():
    """side-view outlines of the trigger guard (outer loop and finger opening)"""
    s = math.tan(RAKE)
    gx = lambda z: 84.4 + z * s   # grip front face X at height z (z negative)
    outer = [(gx(-6) - 6, -6), (gx(-6) - 6, 2), (134, 2), (134, -28), (126, -36), (gx(-36) - 6, -36)]
    inner = [(gx(-6) - 8, 3), (128, 3), (128, -26), (122, -30), (gx(-30) - 8, -30)]
    return outer, inner


def guard_overlay(side):
    """thin decorative plate for one side face of the trigger guard (side = +1 left, -1 right)"""
    outer, inner = guard_profiles()
    t = OVERLAY_T
    ov = (cq.Workplane("XZ").polyline(outer).close().offset2D(-OVERLAY_INSET, "arc").extrude(-t))
    hole = (cq.Workplane("XZ").polyline(inner).close().offset2D(OVERLAY_INSET, "arc").extrude(-t - 2)
            .translate((0, -1, 0)))
    ov = ov.cut(hole)
    ov = ov.cut(box(-50, 300, -10, 10, -OVERLAY_INSET, 100))                     # stop short of the body's underside
    ov = ov.cut(grip_box(-G_OUT_D / 2 - 5, G_OUT_D / 2 + OVERLAY_INSET, -30, U_BOT + 5, -10, 10))   # and of the grip
    y0 = GUARD_HW if side > 0 else -GUARD_HW - t
    return ov.translate((0, y0, 0))


def outer_shell():
    # body side profile
    prof = [(0, 0), (180, 0), (BODY_L, 5), (BODY_L, 37), (181, BODY_H), (4, BODY_H), (0, 38)]
    body = side_extrude(prof, -HW, HW)
    body = body.faces(">Y").edges().chamfer(1.6).faces("<Y").edges().chamfer(1.6)

    # roof / rail: trapezoid cross-section, self-supporting when printed on its side
    roof = (cq.Workplane("YZ")
            .polyline([(-HW + 0.5, 40), (HW - 0.5, 40), (ROOF_HALF, ROOF_TOP), (-ROOF_HALF, ROOF_TOP)])
            .close().extrude(160).translate((14, 0, 0)))
    # sloped ends
    roof = roof.cut(side_extrude([(8, 39), (22, 39), (8, 48)], -HW, HW))
    roof = roof.cut(side_extrude([(174, 39), (160, 39), (174, 48)], -HW, HW))
    body = body.union(roof)
    # rail slots
    for i in range(14):
        x = 36 + i * 8
        body = body.cut(box(x, x + 3, -ROOF_HALF - 2, ROOF_HALF + 2, ROOF_TOP - 1.5, ROOF_TOP + 1))

    # muzzle ring
    body = body.union(cyl_x(0, CAM_Z, 32, BODY_L, BODY_L + 1.5))

    # grip
    grip = grip_box(-G_OUT_D / 2, G_OUT_D / 2, -14, U_BOT - 7.5, -HW, HW, ch=2.8)
    butt = grip_box(-G_OUT_D / 2 - FLARE, G_OUT_D / 2 + FLARE, U_BOT - 7.5, U_BOT, -HW, HW, ch=2.8)
    grip = grip.union(butt)

    # trigger guard
    outer, inner = guard_profiles()
    guard = side_extrude(outer, -5, 5).cut(side_extrude(inner, -6, 6))
    guard = guard.edges("|Y").fillet(1.2)

    return body.union(grip).union(guard)


# ======================================================================== cavities
def cavities():
    c = box(WALL, FRONT_BLOCK_X0, -IHW, IHW, WALL, BODY_H - WALL)
    gc = grip_box(-CAV_D / 2, CAV_D / 2, -30, U_BOT - WALL, -CAV_W / 2, CAV_W / 2, ch=1.0)
    c = c.union(gc.intersect(box(-50, 300, -60, 60, -200, WALL + 0.5)))
    return c


# ======================================================================== internal features
def internals():
    parts = []
    # --- solenoid cradle: transverse ribs with windows
    for x0, win in ((SOL_X0 - 2.4, 12.0), (SOL_X0 + SOL_L, 16.0)):
        rib = box(x0, x0 + 2.4, -IHW, IHW, SOL_Z0 - 2, BODY_H - WALL)
        rib = rib.cut(cyl_x(0, SOL_AXIS_Z, win, x0 - 1, x0 + 4))
        rib = rib.cut(box(x0 - 1, x0 + 4, -WIRE_NOTCH_Y, WIRE_NOTCH_Y, WIRE_NOTCH_Z0, BODY_H))
        parts.append(rib)
    # side fins
    for x in (SOL_X0 + 6, SOL_X0 + SOL_L / 2 - 1, SOL_X0 + SOL_L - 8):
        for sgn in (1, -1):
            y_in = sgn * (SOL_W / 2 + CLR)
            parts.append(box(x, x + 2, min(y_in, sgn * IHW), max(y_in, sgn * IHW), SOL_Z0, SOL_Z0 + SOL_H))
    # shelves under and over the solenoid (leave centre free for wires)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * IHW, sgn * 8.0))
        parts.append(box(SOL_X0, SOL_X0 + SOL_L, y0, y1, SOL_Z0 - 1.6, SOL_Z0))
        parts.append(box(SOL_X0, SOL_X0 + SOL_L, y0, y1, SOL_Z0 + SOL_H + CLR, SOL_Z0 + SOL_H + CLR + 1.6))

    # --- ESP32 ledges at both PCB ends
    for x0 in (ESP_X0 - 1.5, ESP_X0 + ESP_L - 3.5):
        parts.append(box(x0, x0 + 5, -IHW, IHW, ESP_PCB_Z - 6, ESP_PCB_Z))
    # side guides at both ends of the board, clear of the header pins that run along the middle
    for xa, xb in ((ESP_X0, ESP_X0 + 5.0), (ESP_X0 + ESP_L - 5.0, ESP_X0 + ESP_L)):
        for sgn in (1, -1):
            y0, y1 = sorted((sgn * (ESP_W / 2 + ESP_SIDE_CLR), sgn * IHW))
            parts.append(box(xa, xb, y0, y1, ESP_PCB_Z - 1.0, ESP_PCB_Z + ESP_PCB_T + 1.5))
    parts.extend(buck_pocket())
    # MOSFET pin: shaft through the tab hole, groove for the clip, head above it
    ya = MOS_TOP + 1.3 + 0.05                 # top of the tab
    yb = ya + CLIP_T + CLIP_PLAY               # top of the groove
    parts.append(cyl_y(MOS_X, MOS_Z, MOS_PIN_D, -IHW - 0.2, ya))
    parts.append(cyl_y(MOS_X, MOS_Z, MOS_NECK_D, ya - 0.1, yb + 0.1))
    parts.append(cyl_y(MOS_X, MOS_Z, MOS_PIN_D, yb, yb + MOS_HEAD_L))
    for sgn in (1, -1):   # rails along both edges of the body, well away from the pin
        x0, x1 = sorted((MOS_X + sgn * (TO220_W / 2 + 0.2), MOS_X + sgn * (TO220_W / 2 + 1.5)))
        parts.append(box(x0, x1, -IHW - 0.2, MOS_TOP + 3.0, MOS_ZB + 7.0, MOS_ZB + 15.0))
    # end stops so the board can't slide
    parts.append(box(ESP_X0 - 3.5, ESP_X0 - 1.5, -IHW, IHW, ESP_PCB_Z - 6, ESP_PCB_Z + ESP_PCB_T))
    parts.append(box(ESP_X0 + ESP_L + 1.5, ESP_X0 + ESP_L + 3.5, -IHW, IHW, ESP_PCB_Z - 6, ESP_PCB_Z + ESP_PCB_T + 1.0))

    # --- camera front block with bore and captured nut pocket
    fb = box(FRONT_BLOCK_X0, BODY_L - 1, -IHW, IHW, WALL, BODY_H - WALL)
    fb = fb.cut(cyl_x(0, CAM_Z, CAM_HOLE, FRONT_BLOCK_X0 - 1, BODY_L + 5))
    hexp = (cq.Workplane("YZ").center(0, CAM_Z).polygon(6, NUT_POCKET_AF / math.cos(math.pi / 6))
            .extrude(NUT_POCKET_T).translate((BODY_L - FRONT_WALL - NUT_POCKET_T, 0, 0)))
    fb = fb.cut(hexp)
    parts.append(fb)

    # --- trigger pivot bosses + pins (pins meet at the split plane, so each half gets a stub)
    ty = TRIG_T / 2 + 0.2
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * IHW, sgn * ty))
        parts.append(cyl_y(PIV_X, PIV_Z, 9.0, y0, y1))
    parts.append(cyl_y(PIV_X, PIV_Z, PIV_PIN_D, -ty, ty))
    # --- microswitch standoffs + pegs (switch stands upright in the trigger plane)
    msy = MS_T / 2 + 0.1
    hx = MS_REAR_X + MS_H - MS_HOLE_FROM_TERM
    for a in MS_HOLE_ENDS:
        hz = MS_Z0 + a
        for sgn in (1, -1):
            y0, y1 = sorted((sgn * IHW, sgn * msy))
            parts.append(cyl_y(hx, hz, 5.0, y0, y1))
        parts.append(cyl_y(hx, hz, MS_PEG_D, -msy, msy))
    # --- pull stop rib (right half) above the trigger tail
    stop_z = _tail_top_at_pull() + 0.05
    parts.append(box(STOP_X0, STOP_X1, -IHW, 0.0, stop_z, stop_z + STOP_H))
    parts.append(box(STOP_WEB_X0, STOP_WEB_X1, -IHW, STOP_WEB_Y1, WALL, stop_z + STOP_H))
    # --- torsion spring post (left half) and shelf for its rear leg
    parts.append(cyl_y(SPR_X, SPR_Z, SPR_POST_D, SPR_Y0 + SPR_TAPER, IHW))
    parts.append(cq.Workplane("XZ").center(SPR_X, SPR_Z).circle(SPR_POST_TIP_D / 2)
                 .workplane(offset=-SPR_TAPER).circle(SPR_POST_D / 2).loft()
                 .translate((0, SPR_Y0 + SPR_TAPER, 0)))
    for th in SPR_FIN_DEG:
        parts.append(spring_fin(th))

    # --- battery shelves and charger support rib in the butt
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * CAV_W / 2, sgn * 14.0))
        parts.append(grip_box(-CAV_D / 2, CAV_D / 2, SHELF_U, SHELF_U + 1.6, y0, y1))
    # stop tabs above the battery pack (keeps it from sliding up into the body)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (CAV_W / 2 + 0.3), sgn * 15.0))
        parts.append(grip_box(-12, 12, BAT_U_TOP - BAT_HEADROOM - 2.6, BAT_U_TOP - BAT_HEADROOM, y0, y1))
    # charger cradle: side rails capture the board's width, a front stop and a top tab hold it down
    brd_u = BRD_U
    cv0 = CHG_V0                               # rear edge of the board (USB-C end)
    cv1 = cv0 + CHG_L                          # front edge
    for sgn in (1, -1):                        # side rails
        y0, y1 = sorted((sgn * (CHG_W / 2 + 0.4), sgn * (CHG_W / 2 + 2.4)))
        parts.append(grip_box(cv0 - 1, cv1 + 2, brd_u - CHG_STACK - 0.5, U_BOT - WALL, y0, y1))
    # front stop
    parts.append(grip_box(cv1 + 0.5, cv1 + 2.5, brd_u - CHG_STACK - 0.5, U_BOT - WALL, -CHG_W / 2 - 2.4, CHG_W / 2 + 2.4))
    # ledges UNDER the board along both edges, so it rests on something its whole length
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (CHG_W / 2 - 1.8), sgn * (CHG_W / 2 + 2.4)))
        parts.append(grip_box(cv0, cv1 + 2, brd_u, brd_u + 1.8, y0, y1))
    # two hold-down tabs at the middle of the board (the ends fouled the electrolytic capacitor)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (CHG_W / 2 - 1.2), sgn * (CHG_W / 2 + 2.4)))
        parts.append(grip_box(cv0 + CHG_L / 2 - 2.5, cv0 + CHG_L / 2 + 2.5,
                              brd_u - CHG_STACK - 2.0, brd_u - CHG_STACK - 0.5, y0, y1))
    return parts


# ======================================================================== internal feature builders
def buck_pocket():
    """raised rim on the inside of the left wall that the buck converter drops into"""
    iw, ih = BUCK_L + 2 * BUCK_CLR, BUCK_W + 2 * BUCK_CLR      # inner opening
    ow, oh = iw + 2 * BUCK_RIM_T, ih + 2 * BUCK_RIM_T          # outer size
    y0, y1 = IHW - BUCK_RIM_H, IHW + 0.2
    rim = box(BUCK_X - ow / 2, BUCK_X + ow / 2, y0, y1, BUCK_Z - oh / 2, BUCK_Z + oh / 2)
    rim = rim.cut(box(BUCK_X - iw / 2, BUCK_X + iw / 2, y0 - 1, y1 + 1, BUCK_Z - ih / 2, BUCK_Z + ih / 2))
    # wire openings at the middle of both short ends
    for xe in (BUCK_X - ow / 2, BUCK_X + ow / 2):
        rim = rim.cut(box(xe - 2, xe + 2, y0 - 1, y1 + 1, BUCK_Z - BUCK_GAP / 2, BUCK_Z + BUCK_GAP / 2))
    return [rim]


def mosfet_clip():
    """fork clip, in place: slides on sideways (from the rear) and snaps into the pin's groove"""
    ya = MOS_TOP + 1.3 + 0.05
    y0, y1 = ya, ya + CLIP_T
    xt = MOS_X + CLIP_TIP                        # open end of the fork
    r = 0.8
    c = box(xt - CLIP_L, xt, y0, y1, MOS_Z - CLIP_W / 2, MOS_Z + CLIP_W / 2)
    c = c.edges("|Y").fillet(r)
    c = c.cut(box(MOS_X, xt + 1, y0 - 1, y1 + 1, MOS_Z - 0.9, MOS_Z + 0.9))        # 1.8 mm entrance
    c = c.cut(cyl_y(MOS_X, MOS_Z, 2.3, y0 - 1, y1 + 1))                            # seat for the 2.2 neck
    c = c.cut(box(xt - 9.0, MOS_X, y0 - 1, y1 + 1, MOS_Z - 0.6, MOS_Z + 0.6))       # relief slot: long, springy prongs
    c = c.cut(side_extrude([(xt - 1.2, MOS_Z - 0.9), (xt + 0.1, MOS_Z - 1.5),
                            (xt + 0.1, MOS_Z + 1.5), (xt - 1.2, MOS_Z + 0.9)], y0 - 1, y1 + 1))   # lead-in
    return c


def spring_fin(theta_deg):
    """radial fin near the spring post; the long leg leans on its clockwise face"""
    bar = box(-SPR_FIN_T / 2, SPR_FIN_T / 2, SPR_FIN_Y0, IHW, SPR_FIN_R0, SPR_FIN_R1)
    bar = bar.rotate((0, 0, 0), (0, 1, 0), 90.0 - theta_deg)
    return bar.translate((SPR_X, 0, SPR_Z))


def _catmull(pts, n=8):
    import numpy as np
    P = np.array(pts, float); out = []
    P = np.vstack([P[0], P, P[-1]])
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return [tuple(map(float, q)) for q in out]

# ======================================================================== printed trigger
def trigger(angle=0.0):
    """printed trigger in world coordinates; angle = degrees of pull (0 = rest)"""
    blade_back = _catmull([(91.6, 2.4), (92.4, -4.0), (93.0, -12.0), (94.6, -20.0), (96.4, -24.4)])
    tip = _catmull([(96.4, -24.4), (99.0, -26.0), (102.6, -25.8), (105.2, -24.2)], 6)
    blade_front = _catmull([(105.2, -24.2), (102.4, -19.5), (100.6, -12.0), (101.6, -4.0), (104.2, 1.5), (104.6, 5.0)])
    arm = [(103.2, 10.5), (ARM_FRONT_X, 14.0), (ARM_FRONT_X, 25.0), (95.0, 25.0), (95.0, 13.0), (92.0, 10.2), (84.0, 8.0), (84.0, 2.4)]
    prof = blade_back + tip[1:] + blade_front[1:] + arm
    t = side_extrude(prof, -TRIG_T / 2, TRIG_T / 2)
    t = t.union(cyl_y(PIV_X, PIV_Z, 12.0, -TRIG_T / 2, TRIG_T / 2))
    # ledge for the spring's front leg (sticks out on the left side)
    t = t.union(box(90.0, 93.2, TRIG_T / 2 - 0.5, LEDGE_Y1, 3.2, 5.6))
    t = t.union(box(92.4, 93.2, TRIG_T / 2 - 0.5, LEDGE_Y1, 5.6, 6.8))
    t = t.cut(cyl_y(PIV_X, PIV_Z, PIV_HOLE_D, -10, 20))
    if angle:
        t = t.rotate((PIV_X, 0, PIV_Z), (PIV_X, 1, PIV_Z), angle)
    return t

def _tail_top_at_pull():
    """highest point of the trigger tail under the stop rib when fully pulled"""
    t = trigger(PULL_DEG).intersect(box(STOP_X0, STOP_X1, -10, 0, -5, 30))
    return t.val().BoundingBox().zmax

def microswitch(pressed=False):
    """placeholder switch with roller lever (for checks and renders)"""
    body = box(MS_REAR_X, MS_REAR_X + MS_H, -MS_T / 2, MS_T / 2, MS_Z0, MS_Z0 + MS_L)
    out = ROLLER_FREE if not pressed else PRESS_TO
    rc_x = MS_REAR_X - out + ROLLER_D / 2
    rc_z = MS_Z0 + ROLLER_ALONG
    roller = cyl_y(rc_x, rc_z, ROLLER_D, -1.6, 1.6)
    hinge = (MS_REAR_X, MS_Z0 + 2.0)
    lever = side_extrude([hinge, (hinge[0], hinge[1] + 0.3), (rc_x + 0.2, rc_z + 0.3), (rc_x, rc_z)], -1.6, 1.6)
    return body.union(roller).union(lever)


# ======================================================================== screw bosses
BODY_BOSSES = [(8.0, 35.0), (74.0, 7.0), (157.0, 35.0), (157.0, 7.0)]
GRIP_BOSSES_LOCAL = [(16.5, U_BOT - WALL - BOSS_OD / 2 + BOSS_SINK), (-16.5, U_BOT - WALL - BOSS_OD / 2 + BOSS_SINK)]

def boss_positions():
    return BODY_BOSSES + [g2w(v, u) for v, u in GRIP_BOSSES_LOCAL]

def bosses():
    return [cyl_y(x, z, BOSS_OD, -HW + 0.5, HW - 0.5) for x, z in boss_positions()]


# ======================================================================== openings
def openings():
    cuts = []
    # camera bore through muzzle ring
    cuts.append(cyl_x(0, CAM_Z, CAM_HOLE, FRONT_BLOCK_X0 - 1, BODY_L + 5))
    # captured nut pocket
    cuts.append(cq.Workplane("YZ").center(0, CAM_Z).polygon(6, NUT_POCKET_AF / math.cos(math.pi / 6))
                .extrude(NUT_POCKET_T).translate((BODY_L - FRONT_WALL - NUT_POCKET_T, 0, 0)))
    # trigger opening in the body floor
    cuts.append(box(SLOT_X0, SLOT_X1, -(TRIG_T / 2 + 0.7), TRIG_T / 2 + 0.7, -1, WALL + 0.5))
    # rocker switch cut-out in the rear face
    cuts.append(box(-1, WALL + 1, -SW_CUT_Y / 2, SW_CUT_Y / 2, SW_Z - SW_CUT_Z / 2, SW_Z + SW_CUT_Z / 2))
    # thin the rear wall from the inside around the switch hole
    cuts.append(box(SW_PANEL, WALL + 0.5, -SW_CUT_Y / 2 - 2.5, SW_CUT_Y / 2 + 2.5, SW_Z - SW_CUT_Z / 2 - 2.5, SW_Z + SW_CUT_Z / 2 + 2.5))
    # USB-C opening in the rear of the butt, sized for a cable's moulded plug, with an outside lead-in
    port_u = BRD_U - CHG_STACK + CHG_PORT_H / 2 + PORT_U_ADJ   # centred on the connector, not the board
    cuts.append(grip_obround(-G_OUT_D / 2 - 2, -G_OUT_D / 2 + PORT_STEP, port_u, 0.0, PORT_W, PORT_H_MM))
    cuts.append(grip_obround(-G_OUT_D / 2 + PORT_STEP, CHG_V0 + 0.5, port_u, 0.0, PORT_W_IN, PORT_H_IN))
    lead = PORT_CHAMFER
    cuts.append(grip_obround(-G_OUT_D / 2 - 1.5, -G_OUT_D / 2 + lead, port_u, 0.0,
                             PORT_W + 2 * lead, PORT_H_MM + 2 * lead))
    return cuts


def surface_details(solid):
    d = 0.8
    for sgn in (1, -1):
        yo = sgn * HW
        y0, y1 = sorted((yo, yo - sgn * d))
        # panel line on the body
        outer = box(26, 146, y0, y1, 12, 32)
        inner = box(27.2, 144.8, y0 - 1, y1 + 1, 13.2, 30.8)
        solid = solid.cut(outer.cut(inner))
        # angled vents near the front
        for i in range(4):
            x = 152 + i * 5.5
            vent = box(-1.25, 1.25, y0, y1, -8, 8).rotate((0, 0, 0), (0, 1, 0), -25).translate((x + 3, 0, CAM_Z))
            solid = solid.cut(vent)
        # grip grooves
        for i in range(7):
            u = 22 + i * 7
            solid = solid.cut(grip_box(-17, 17, u, u + 1.2, y0, y1))
    return solid


# ======================================================================== assemble + split
def build():
    shell = outer_shell().cut(cavities())
    for p in internals() + bosses():
        shell = shell.union(p)
    for c in openings():
        shell = shell.cut(c)
    shell = surface_details(shell)

    left = shell.intersect(box(-50, 300, 0, 60, -200, 100))
    right = shell.intersect(box(-50, 300, -60, 0, -200, 100))

    for x, z in boss_positions():
        left = left.cut(cyl_y(x, z, INSERT_D, 0, INSERT_DEPTH))
        left = left.cut(cyl_y(x, z, INSERT_LEAD_D, 0, INSERT_LEAD_L))
        left = left.cut(cq.Workplane().add(cq.Solid.makeCone(INSERT_LEAD_D / 2 + INSERT_CHAMFER, INSERT_LEAD_D / 2,
                                                              INSERT_CHAMFER, cq.Vector(x, -0.01, z), cq.Vector(0, 1, 0))))
        right = right.cut(cyl_y(x, z, SCREW_CLR, -SCREW_GRIP - 1, 0.1))
        right = right.cut(cyl_y(x, z, HEAD_CB, -HW - 5, -SCREW_GRIP))
    return shell, left, right


# ======================================================================== component placeholders (for checks / renders)
def components():
    comp = {}
    comp["solenoid"] = box(SOL_X0, SOL_X0 + SOL_L, -SOL_W / 2, SOL_W / 2, SOL_Z0, SOL_Z0 + SOL_H)
    comp["plunger"] = cyl_x(0, SOL_AXIS_Z, PLUNGER_D, SOL_X0 - NUB_REAR - SOL_STROKE, SOL_X0 + SOL_L + PLUNGER_FRONT)
    comp["esp32"] = box(ESP_X0, ESP_X0 + ESP_L, -ESP_W / 2, ESP_W / 2, ESP_PCB_Z, ESP_PCB_Z + ESP_PCB_T + 3.2)
    comp["esp32_pins"] = box(ESP_X0 + 6, ESP_X0 + ESP_L - 7, -ESP_W / 2 + 0.3, ESP_W / 2 - 0.3, ESP_PCB_Z - 8.5, ESP_PCB_Z)
    comp["camera"] = cyl_x(0, CAM_Z, CAM_D, BODY_L + CAM_PROTRUDE - CAM_LEN, BODY_L + CAM_PROTRUDE)
    nut = lambda x0: (cq.Workplane("YZ").center(0, CAM_Z).polygon(6, NUT_AF / math.cos(math.pi / 6))
                      .extrude(NUT_T).translate((x0, 0, 0)).cut(cyl_x(0, CAM_Z, CAM_D, x0 - 1, x0 + 6)))
    comp["nut_captured"] = nut(BODY_L - FRONT_WALL - NUT_POCKET_T + 0.25)
    comp["nut_lock"] = nut(BODY_L + 1.5)
    comp["battery"] = grip_box(-BAT_D / 2, BAT_D / 2, BAT_U_TOP, SHELF_U, -BAT_W / 2, BAT_W / 2)
    brd_u = BRD_U
    comp["charger"] = grip_box(CHG_V0, CHG_V0 + CHG_L, brd_u - CHG_STACK, brd_u, -CHG_W / 2, CHG_W / 2)
    comp["usb_c"] = grip_obround(CHG_V0 - CHG_PORT_OUT, CHG_V0, brd_u - CHG_STACK + CHG_PORT_H / 2, 0.0, 9.0, CHG_PORT_H)
    comp["rocker"] = box(WALL, WALL + SW_DEPTH, -SW_CUT_Y / 2 + 0.5, SW_CUT_Y / 2 - 0.5, SW_Z - SW_CUT_Z / 2 + 0.5, SW_Z + SW_CUT_Z / 2 - 0.5)
    comp["buck_pcb"] = box(BUCK_X - BUCK_L / 2, BUCK_X + BUCK_L / 2, IHW - 1.6, IHW,
                           BUCK_Z - BUCK_W / 2, BUCK_Z + BUCK_W / 2)
    comp["buck_parts"] = box(BUCK_X - BUCK_L / 2 + 2, BUCK_X + BUCK_L / 2 - 2, IHW - 1.6 - 5.0, IHW - 1.6,
                             BUCK_Z - BUCK_W / 2 + 1.5, BUCK_Z + BUCK_W / 2 - 1.5)
    t0 = MOS_TOP                  # standing upright, tab at the bottom, legs up
    back = box(MOS_X - TO220_W / 2, MOS_X + TO220_W / 2, t0, t0 + 1.3, MOS_ZB, MOS_ZB + 15.9)
    back = back.cut(cyl_y(MOS_X, MOS_Z, 3.6, t0 - 1, t0 + 2))
    body = box(MOS_X - TO220_W / 2, MOS_X + TO220_W / 2, t0, t0 + 4.69, MOS_ZB + 6.4, MOS_ZB + 15.9)
    legs = None
    for dx in (-2.54, 0.0, 2.54):
        leg = box(MOS_X + dx - 0.4, MOS_X + dx + 0.4, t0 + 1.4, t0 + 2.2, MOS_ZB + 15.9, MOS_ZB + 15.9 + MOS_LEGS)
        legs = leg if legs is None else legs.union(leg)
    comp["mosfet"] = back.union(body).union(legs)
    comp["mosfet_clip"] = mosfet_clip()
    comp["microswitch"] = microswitch(pressed=False)
    comp["trigger"] = trigger()
    comp["spring"] = cyl_y(SPR_X, SPR_Z, SPR_COIL_OD, SPR_Y0, SPR_Y0 + SPR_COIL_L).cut(
        cyl_y(SPR_X, SPR_Z, SPR_POST_D - 0.2, SPR_Y0 - 1, SPR_Y0 + 1 + SPR_COIL_L))
    return comp


if __name__ == "__main__":
    import sys
    shell, left, right = build()
    print("left valid", left.val().isValid(), "vol", round(left.val().Volume()))
    print("right valid", right.val().isValid(), "vol", round(right.val().Volume()))
