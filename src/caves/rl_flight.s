# Rogue Squadron PC - Rogue Leader style flight (as in the user's modded Rogue Leader).
#  - heading turns at WN*|X| deg/s (linear stick), regardless of bank
#  - tight-turn button (joystick button 8 by default, read directly; the game's own bindings are
#    untouched): blends (ramp in/out) to Rogue Squadron's OWN flight - stock yaw, roll and its
#    automatic tight-turn pull. Optional extra multipliers turn x (1 + TK*|X|), pitch x (1 + PK*|Y|)
#    (default 0); speed is not touched
#  - while the tow cable is out (fired / hooked to an AT-AT), the same blend goes fully to stock
#  - bank follows the stick: target BANK*X*|X| deg (squared curve), levels out when centred;
#    stock rolling when the craft is near vertical or inverted (up.y < UPMIN)
# Lives in the .conv section at VA 0x7FFB00 (code) / 0x7FFF00 (data).
        .intel_syntax noprefix
        .code32
        .text
        .equ D,        0x7FFF00
        .equ G_RAMP,   D+0x00
        .equ G_BC,     D+0x04      # per-frame pull applied in hook B
        .equ G_MTX,    D+0x08      # ship matrix pointer captured in hook A
        .equ G_T0,     D+0x0C
        .equ G_T1,     D+0x10
        .equ C_UP,     D+0x14      # ramp-in rate (1/s)
        .equ C_DN,     D+0x18      # ramp-out rate (1/s)
        .equ C_WN,     D+0x1C      # normal full-stick turn (deg/s)
        .equ C_TK,     D+0x20      # tight turn factor (yaw x 1+TK*|X|)
        .equ C_PK,     D+0x24      # tight pitch factor (pitch x 1+PK*|Y|)
        .equ C_BANK,   D+0x28      # full-stick bank (deg)
        .equ C_KR,     D+0x2C      # bank follow rate (1/s)
        .equ C_RMAX,   D+0x30      # max roll rate (deg/s)
        .equ C_UPMIN,  D+0x34      # min up.y for bank control
        .equ C_R2D,    D+0x38      # 57.29578
        .equ C_ZERO,   D+0x3C
        .equ M_ABS,    D+0x40      # 4 x 0x7fffffff
        .equ M_SIGN,   D+0x50      # 4 x 0x80000000
        .equ C_ONE,    D+0x60
        .equ M_NEG1,   D+0x64
        .equ C_MASK,   D+0x68      # joystick button bit for tight turn
        .equ G_MIX,    D+0x70      # 0 = Rogue Leader style, 1 = stock (button / vertical / inverted)
        .equ C_VA,     D+0x74      # |fwd.y| where the blend to stock starts (sin 35)
        .equ C_VINV,   D+0x78      # 1 / (end - start)
        .equ C_UA,     D+0x7C      # up.y below which the blend to stock starts
        .equ C_UINV,   D+0xA0      # 1 / (start - end)
        .equ G_DBG,    D+0x80      # +0 omega, +4 bank, +8 target, +C btn, +10 count A, +14 count C, +18 tow state
        .equ TOW_STATE, 0x708100   # towcable.c state byte: 0/4 free, 1 fired, 2 hooked, 3 AT-AT tripping

# ---- A: at 40F530 (after the game's yaw/roll command calc) ----------------------------
hookA:
        xor     eax, eax                     # tight-turn button: a raw joystick button
        cmp     byte ptr ds:[0x5F7FC8], 0    # joystick enabled? (same gate as the game's action check)
        je      3f
        push    dword ptr ds:[C_MASK]        # button bit (button 8 = 0x80)
        mov     eax, [ebp+8]
        push    dword ptr [eax+0xB8]         # player slot
        mov     eax, 0x4688EC                # game's joystick-button test (slot, mask)
        call    eax
        add     esp, 8
3:      mov     dword ptr ds:[G_DBG+0x0C], eax
        movzx   ecx, byte ptr ds:[TOW_STATE] # tow cable fired / hooked / AT-AT tripping (1-3):
        mov     dword ptr ds:[G_DBG+0x18], ecx
        dec     ecx                          # stock flight, as before the tight-turn button
        cmp     ecx, 2
        ja      4f
        or      eax, 1
4:      movss   xmm0, dword ptr ds:[G_RAMP]
        movss   xmm1, dword ptr [ebp+0xC]    # dt
        test    eax, eax
        jz      1f
        mulss   xmm1, dword ptr ds:[C_UP]
        addss   xmm0, xmm1
        jmp     2f
1:      mulss   xmm1, dword ptr ds:[C_DN]
        subss   xmm0, xmm1
2:      maxss   xmm0, dword ptr ds:[C_ZERO]
        minss   xmm0, dword ptr ds:[C_ONE]
        movss   dword ptr ds:[G_RAMP], xmm0
        # stick X for this slot, clamped
        mov     eax, [ebp+8]
        mov     eax, [eax+0xB8]
        imul    eax, eax, 0x14
        movss   xmm1, dword ptr [eax+0x706924]
        maxss   xmm1, dword ptr ds:[M_NEG1]
        minss   xmm1, dword ptr ds:[C_ONE]
        movaps  xmm2, xmm1
        andps   xmm2, xmmword ptr ds:[M_ABS] # |X|
        movaps  xmm5, xmm1
        andps   xmm5, xmmword ptr ds:[M_SIGN]# sign(X)
        # omega = WN*|X|*(1 + TK*|X|*ramp)
        mulss   xmm0, xmm2
        mulss   xmm0, dword ptr ds:[C_TK]
        addss   xmm0, dword ptr ds:[C_ONE]
        mulss   xmm0, dword ptr ds:[C_WN]
        mulss   xmm0, xmm2
        movss   dword ptr ds:[G_DBG+0x00], xmm0
        mov     edx, [ebp-0x18]              # ship matrix
        mov     dword ptr ds:[G_MTX], edx
        # how much of the game's own flight to use: button ramp, steep climb/dive, heavy roll/inverted
        movss   xmm1, dword ptr [edx+0x14]   # fwd.y = sin(pitch)
        andps   xmm1, xmmword ptr ds:[M_ABS]
        subss   xmm1, dword ptr ds:[C_VA]
        mulss   xmm1, dword ptr ds:[C_VINV]
        movss   xmm2, dword ptr ds:[C_UA]
        subss   xmm2, dword ptr [edx+0x10]   # up.y
        mulss   xmm2, dword ptr ds:[C_UINV]
        maxss   xmm1, xmm2
        maxss   xmm1, dword ptr ds:[G_RAMP]
        maxss   xmm1, dword ptr ds:[C_ZERO]
        minss   xmm1, dword ptr ds:[C_ONE]
        movss   dword ptr ds:[G_MIX], xmm1
        movss   xmm3, dword ptr [edx+0x0C]   # right.y = sin(bank), +ve banked right
        movss   xmm4, dword ptr [edx+0x10]   # up.y
        xorps   xmm3, xmm5                   # sign(X)*right.y
        movaps  xmm6, xmm0
        mulss   xmm6, xmm4
        xorps   xmm6, xmm5
        xorps   xmm6, xmmword ptr ds:[M_SIGN]# body yaw = -sign(X)*omega*up.y (game sign)
        movss   xmm7, dword ptr [ebp-4]      # blend toward the game's own yaw by ramp
        subss   xmm7, xmm6
        mulss   xmm7, dword ptr ds:[G_MIX]
        addss   xmm6, xmm7
        movss   dword ptr [ebp-4], xmm6
        mulss   xmm0, xmm3
        mulss   xmm0, dword ptr [ebp+0xC]    # body pitch share of the turn, per frame
        movss   dword ptr ds:[G_BC], xmm0
        inc     dword ptr ds:[G_DBG+0x10]
        mov     edx, [ebp+8]                 # replayed
        mov     eax, [edx+0xB8]
        push    0x40F539
        ret

# ---- B: at 40FB7D (replaces "pitch -= stock auto tight-turn pull") -----------------------
        .org 0x200
hookB:
        mov     eax, [ebp+8]
        mov     ecx, [eax+0xB8]
        imul    ecx, ecx, 0x14
        movss   xmm1, dword ptr [ecx+0x706920]   # stick Y
        andps   xmm1, xmmword ptr ds:[M_ABS]
        minss   xmm1, dword ptr ds:[C_ONE]
        mulss   xmm1, dword ptr ds:[G_RAMP]
        mulss   xmm1, dword ptr ds:[C_PK]
        addss   xmm1, dword ptr ds:[C_ONE]       # 1 + PK*|Y|*ramp
        movss   xmm2, dword ptr [ebp-0xBC]       # game's own auto tight-turn pull
        subss   xmm2, dword ptr ds:[G_BC]
        mulss   xmm2, dword ptr ds:[G_MIX]
        addss   xmm2, dword ptr ds:[G_BC]        # blend ours -> game's by ramp
        movss   xmm0, dword ptr [eax+0xDC]
        mulss   xmm0, xmm1
        subss   xmm0, xmm2
        movss   dword ptr [eax+0xDC], xmm0
        push    0x40FB95
        ret

# ---- C: at 41052E (all per-frame rates final, before the small-rate cut-off) -------------
        .org 0x280
hookC:
        mov     ecx, [ebp+8]
        mov     edx, dword ptr ds:[G_MTX]
        test    edx, edx
        jz      9f
        movss   xmm0, dword ptr [edx+0x10]       # up.y
        comiss  xmm0, dword ptr ds:[C_UPMIN]
        jb      9f
        # bank (deg) = asin(right.y)
        movss   xmm3, dword ptr [edx+0x0C]
        movss   dword ptr ds:[G_T0], xmm3
        mulss   xmm3, xmm3
        movss   xmm4, dword ptr ds:[C_ONE]
        subss   xmm4, xmm3
        maxss   xmm4, dword ptr ds:[C_ZERO]
        sqrtss  xmm4, xmm4
        movss   dword ptr ds:[G_T1], xmm4
        fld     dword ptr ds:[G_T0]
        fld     dword ptr ds:[G_T1]
        fpatan                                   # atan(s / sqrt(1-s^2))
        fmul    dword ptr ds:[C_R2D]
        fstp    dword ptr ds:[G_T0]
        # target = BANK * X*|X|
        mov     eax, [ecx+0xB8]
        imul    eax, eax, 0x14
        movss   xmm1, dword ptr [eax+0x706924]
        maxss   xmm1, dword ptr ds:[M_NEG1]
        minss   xmm1, dword ptr ds:[C_ONE]
        movaps  xmm2, xmm1
        andps   xmm2, xmmword ptr ds:[M_ABS]
        mulss   xmm1, xmm2
        mulss   xmm1, dword ptr ds:[C_BANK]
        movss   dword ptr ds:[G_DBG+0x08], xmm1
        movss   xmm0, dword ptr ds:[G_T0]
        movss   dword ptr ds:[G_DBG+0x04], xmm0
        subss   xmm1, xmm0                       # error (deg)
        mulss   xmm1, dword ptr ds:[C_KR]        # roll rate (deg/s), +ve = toward right bank
        movss   xmm2, dword ptr ds:[C_RMAX]
        minss   xmm1, xmm2
        xorps   xmm2, xmmword ptr ds:[M_SIGN]
        maxss   xmm1, xmm2
        mulss   xmm1, dword ptr [ebp+0xC]
        xorps   xmm1, xmmword ptr ds:[M_SIGN]    # game roll sign: negative rolls right
        movss   xmm2, dword ptr [ecx+0xE0]       # blend toward the game's own roll by ramp
        subss   xmm2, xmm1
        mulss   xmm2, dword ptr ds:[G_MIX]
        addss   xmm1, xmm2
        movss   dword ptr [ecx+0xE0], xmm1
        inc     dword ptr ds:[G_DBG+0x14]
9:      mov     dword ptr ds:[G_MTX], 0          # only trust a matrix captured this frame
        fld     dword ptr [ecx+0xD8]             # replayed
        push    0x410537
        ret
