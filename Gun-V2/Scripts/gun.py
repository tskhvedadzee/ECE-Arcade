"""
Light gun shell v1  -  parametric CadQuery model
Coordinates: X = forward (muzzle), Y = left (+) / right (-), Z = up.
Split plane Y = 0.  Left half (Y>0) gets heat-set inserts, right half (Y<0) gets screw heads.
All units mm.
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
NUT_AF = 24.0             # ASSUMED across flats of the M18 nut
NUT_T = 4.0               # ASSUMED nut thickness
FRONT_WALL = 3.0
NUT_POCKET_T = NUT_T + 0.5
NUT_POCKET_AF = NUT_AF + 0.4
REAR_RIB = 3.0
FRONT_BLOCK_X0 = BODY_L - FRONT_WALL - NUT_POCKET_T - REAR_RIB

# ---------------------------------------------------------------- solenoid JF-1039B
SOL_L, SOL_W, SOL_H = 39.5, 26.3, 20.0   # length (X), width (Y), height (Z)
SOL_X0 = 23.0
SOL_Z0 = 14.0
SOL_AXIS_Z = SOL_Z0 + SOL_H / 2
PLUNGER_D = 9.0
PLUNGER_FRONT = 30.0      # front protrusion at rest
NUB_REAR = 5.0            # rear protrusion at rest (+10 mm stroke when fired)

# ---------------------------------------------------------------- ESP32 devkit
ESP_L, ESP_W, ESP_T = 51.7, 28.3, 12.6
ESP_X0 = 99.0
ESP_PCB_Z = 33.0          # underside of the PCB
ESP_PCB_T = 1.6

# ---------------------------------------------------------------- rocker power switch (ASSUMED KCD11 style)
SW_CUT_Y, SW_CUT_Z = 13.1, 8.5    # user's switch: 13.1 wide x 8.5 tall
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
ROLLER_D = 6.6                    # measured 6.5-6.8
ROLLER_FREE = 10.5                # measured: top of roller 10.5 mm from the switch body when free
ROLLER_FLAT = 0.4 + ROLLER_D      # roller top when the lever lies flat on the body (lever ~0.4 mm)
PRESS_TO = ROLLER_FLAT + 0.5      # full pull pushes the roller to here: past any click point, short of flat
MS_REAR_X = ARM_FRONT_X + ROLLER_SLACK + ROLLER_FREE   # lever/roller face of the switch
ROLLER_ALONG = 18.7               # roller centre from the hinge end (hinge at the bottom), from the kit photo
# torsion spring (kit spring, size ASSUMED until measured)
SPR_X, SPR_Z = 85.0, 13.5         # spring post position
SPR_POST_D = 2.6                  # fits any coil with inside diameter >= 3 mm
SPR_Y0 = 3.5                      # coil sits between here and the left wall
SPR_COIL_OD, SPR_COIL_L = 6.8, 8.0

# ---------------------------------------------------------------- grip
RAKE = math.radians(16.0)
G0X = 58.0                # grip centreline crosses body bottom (Z=0) here
BAT_D, BAT_W, BAT_L = 43.0, 38.3, 77.5
CAV_D = BAT_D + 3.0
CAV_W = BAT_W + 1.2
G_OUT_D = CAV_D + 2 * WALL
BAT_U_TOP = -1.5
SHELF_U = BAT_U_TOP + BAT_L          # battery rests here
U_BOT = SHELF_U + 19.5               # outer bottom of the butt
FLARE = 3.0

# ---------------------------------------------------------------- charger Z-6732
CHG_L, CHG_W, CHG_STACK = 32.0, 18.0, 7.1
BOSS_OD = 9.0
BOSS_SINK = 1.0          # butt bosses sink into the floor (avoids tangent contact)
BRD_U = U_BOT - WALL - BOSS_OD + BOSS_SINK   # underside of the charger board (rests on the rear boss)

# ---------------------------------------------------------------- screws / inserts
INSERT_D = 4.1            # hole for M3 heat-set insert (user insert OD 4.7 mm)
INSERT_DEPTH = 6.5
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
    s = math.tan(RAKE)
    gx = lambda z: 84.4 + z * s   # grip front face X at height z (z negative)
    outer = [(gx(-6) - 6, -6), (gx(-6) - 6, 2), (134, 2), (134, -28), (126, -36), (gx(-36) - 6, -36)]
    inner = [(gx(-6) - 8, 3), (128, 3), (128, -26), (122, -30), (gx(-30) - 8, -30)]
    guard = side_extrude(outer, -5, 5).cut(side_extrude(inner, -6, 6))
    guard = guard.edges("|Y").fillet(1.2)

    return body.union(grip).union(guard)


# ======================================================================== cavities
def cavities():
    c = box(WALL, FRONT_BLOCK_X0, -IHW, IHW, WALL, BODY_H - WALL)
    gc = grip_box(-CAV_D / 2, CAV_D / 2, -30, U_BOT - WALL, -CAV_W / 2, CAV_W / 2, ch=1.5)
    c = c.union(gc.intersect(box(-50, 300, -60, 60, -200, WALL + 0.5)))
    return c


# ======================================================================== internal features
def internals():
    parts = []
    # --- solenoid cradle: transverse ribs with windows
    for x0, win in ((SOL_X0 - 2.4, 12.0), (SOL_X0 + SOL_L, 16.0)):
        rib = box(x0, x0 + 2.4, -IHW, IHW, SOL_Z0 - 2, BODY_H - WALL)
        rib = rib.cut(cyl_x(0, SOL_AXIS_Z, win, x0 - 1, x0 + 4))
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
    parts.append(box(82.0, 86.8, -IHW, 0.0, stop_z, stop_z + 3.0))
    # --- torsion spring post (left half) and shelf for its rear leg
    parts.append(cyl_y(SPR_X, SPR_Z, SPR_POST_D, SPR_Y0, IHW))
    parts.append(box(72.0, 81.0, SPR_Y0, IHW, 9.5, 11.0))

    # --- battery shelves and charger support rib in the butt
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * CAV_W / 2, sgn * 14.0))
        parts.append(grip_box(-CAV_D / 2, CAV_D / 2, SHELF_U, SHELF_U + 1.6, y0, y1))
    # stop tabs above the battery pack (keeps it from sliding up into the body)
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * (CAV_W / 2 + 0.3), sgn * 15.0))
        parts.append(grip_box(-12, 12, BAT_U_TOP - 3.0, BAT_U_TOP - 0.4, y0, y1))
    # support rib under the front end of the charger board
    brd_u = BRD_U
    parts.append(grip_box(-CAV_D / 2 + 1 + CHG_L - 5, -CAV_D / 2 + 1 + CHG_L - 3, brd_u, U_BOT - WALL + 0.5, -8, 8))
    return parts


# ======================================================================== printed trigger
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
    t = t.union(box(88.0, 92.0, TRIG_T / 2 - 0.5, 14.0, 5.0, 8.0))
    t = t.cut(cyl_y(PIV_X, PIV_Z, PIV_HOLE_D, -10, 20))
    if angle:
        t = t.rotate((PIV_X, 0, PIV_Z), (PIV_X, 1, PIV_Z), angle)
    return t

def _tail_top_at_pull():
    """highest point of the trigger tail under the stop rib when fully pulled"""
    t = trigger(PULL_DEG).intersect(box(82.0, 86.8, -10, 0, -5, 30))
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
    # USB-C opening in the rear of the butt (plug overmould clearance)
    port_u = BRD_U - 1.6 - 1.6
    cuts.append(grip_box(-G_OUT_D / 2 - FLARE - 1, -CAV_D / 2 + 0.5, port_u - 3.5, port_u + 3.5, -6.3, 6.3))
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
        right = right.cut(cyl_y(x, z, SCREW_CLR, -SCREW_GRIP - 1, 0.1))
        right = right.cut(cyl_y(x, z, HEAD_CB, -HW - 5, -SCREW_GRIP))
    return shell, left, right


# ======================================================================== component placeholders (for checks / renders)
def components():
    comp = {}
    comp["solenoid"] = box(SOL_X0, SOL_X0 + SOL_L, -SOL_W / 2, SOL_W / 2, SOL_Z0, SOL_Z0 + SOL_H)
    comp["plunger"] = cyl_x(0, SOL_AXIS_Z, PLUNGER_D, SOL_X0 - NUB_REAR - 10, SOL_X0 + SOL_L + PLUNGER_FRONT)
    comp["esp32"] = box(ESP_X0, ESP_X0 + ESP_L, -ESP_W / 2, ESP_W / 2, ESP_PCB_Z, ESP_PCB_Z + ESP_PCB_T + 3.2)
    comp["esp32_pins"] = box(ESP_X0 + 6, ESP_X0 + ESP_L - 7, -ESP_W / 2 + 0.3, ESP_W / 2 - 0.3, ESP_PCB_Z - 8.5, ESP_PCB_Z)
    comp["camera"] = cyl_x(0, CAM_Z, CAM_D, BODY_L + CAM_PROTRUDE - CAM_LEN, BODY_L + CAM_PROTRUDE)
    nut = lambda x0: (cq.Workplane("YZ").center(0, CAM_Z).polygon(6, NUT_AF / math.cos(math.pi / 6))
                      .extrude(NUT_T).translate((x0, 0, 0)).cut(cyl_x(0, CAM_Z, CAM_D, x0 - 1, x0 + 6)))
    comp["nut_captured"] = nut(BODY_L - FRONT_WALL - NUT_POCKET_T + 0.25)
    comp["nut_lock"] = nut(BODY_L + 1.5)
    comp["battery"] = grip_box(-BAT_D / 2, BAT_D / 2, BAT_U_TOP, SHELF_U, -BAT_W / 2, BAT_W / 2)
    brd_u = BRD_U
    comp["charger"] = grip_box(-CAV_D / 2 + 1, -CAV_D / 2 + 1 + CHG_L, brd_u - CHG_STACK, brd_u, -CHG_W / 2, CHG_W / 2)
    comp["rocker"] = box(WALL, WALL + SW_DEPTH, -SW_CUT_Y / 2 + 0.5, SW_CUT_Y / 2 - 0.5, SW_Z - SW_CUT_Z / 2 + 0.5, SW_Z + SW_CUT_Z / 2 - 0.5)
    comp["microswitch"] = microswitch(pressed=False)
    comp["trigger"] = trigger()
    comp["spring"] = cyl_y(SPR_X, SPR_Z, SPR_COIL_OD, SPR_Y0 + 0.5, SPR_Y0 + 0.5 + SPR_COIL_L).cut(
        cyl_y(SPR_X, SPR_Z, SPR_COIL_OD - 1.6, SPR_Y0, SPR_Y0 + 1 + SPR_COIL_L))
    return comp


if __name__ == "__main__":
    import sys
    shell, left, right = build()
    print("left valid", left.val().isValid(), "vol", round(left.val().Volume()))
    print("right valid", right.val().isValid(), "vol", round(right.val().Volume()))
