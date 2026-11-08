# Rogue Squadron PC - T-16 Skyhopper as a selectable craft, with its own hangar bay.
# The T-16 (craft type 7) is complete in the game but only flown in Beggar's Canyon. Here it is
# allowed wherever the X-wing is, except on snowspeeder missions, and gets a ninth hangar bay on
# the floor between the V-wing and the Y-wing (hangar object 47, bay 8; the level environment
# object moves to 48). Bay/object tables are relocated to bigger copies (data at BASE+0x400,
# filled by build_t16.py). Lives in its own section ".t16" (0x1000 bytes) after the exe's last section;
# BASE (its VA) is passed by build_t16.py with --defsym BASE=...
        .intel_syntax noprefix
        .code32
        .text
        .equ OBJTYPE,  BASE+0x400          # [49] hangar object -> craft type (was 0x5F1A58[9])
        .equ FLAGS,    BASE+0x440          # [49] "speech played" per object (was 0x6484F7)
        .equ T16OBJ,   47                  # hangar object index of the T-16
        .equ NAME,     BASE+0x520          # "+t16#" ('#' ends the model name, no digit = not a copy)
        .equ PATH,     BASE+0x530          # "pl_crafts/t16"
        .equ T16VAR,   BASE+0x540          # receives the object index from the registrar
        .equ FAKE_OBJ, BASE+0x560          # placement record (pos +0x10, rot +0x1C, scale +0x28)
        .equ FAKE_RT,  BASE+0x5A0          # launch route record (header 0x48, then points, knots)
        .equ RT_PTS,   FAKE_RT+0x48
        .equ RT_KNOTS, RT_PTS+5*12
        .equ ONE,      BASE+0x640          # 1.0
        .equ EPS,      BASE+0x644          # 0.0001
        .equ DEFDIST,  BASE+0x648          # no-target convergence distance
        .equ TANDOWN,  BASE+0x64C          # tan(aim-down angle)
        .equ INFOPTR,  BASE+0x650          # player info (saved by t16_find)
        .equ AIMMTX,   BASE+0x660          # finder matrix: pos, forward lowered by the aim-down angle

        .macro CALLABS t
        .byte   0xE8
        .long   (\t) - (BASE + (. - start) + 4)
        .endm
        .macro JMPABS t
        .byte   0xE9
        .long   (\t) - (BASE + (. - start) + 4)
        .endm

start:
# allowed-craft mask fn 0x43CEC8(level) end, hook 0x43D043 (replaces mov eax,[ebp-4] / leave / ret)
mask_end:
        mov     eax, [ebp-4]               # mask, bit = craft type
        test    al, 1                      # X-wing allowed?
        jz      1f
        mov     ecx, [ebp+8]               # level
        cmp     ecx, 0x13
        jae     1f
        cmp     dword ptr [ecx*4+0x5F8498], 4   # level's default craft is the snowspeeder
        je      1f
        or      al, 0x80                   # T-16
1:      mov     esp, ebp
        pop     ebp
        ret

# hangar init 0x4413D5, hook 0x4413DF (mov eax,[0x704248]): clear the relocated speech flags
hangar_init:
        push    edi
        mov     edi, FLAGS
        xor     eax, eax
        mov     ecx, 49
        rep stosb
        pop     edi
        mov     eax, ds:[0x704248]         # replayed
        JMPABS  0x4413E4

# per-ship setup loops (k = 1..8), hooks 0x442977 / 0x442DFA (cmp [ebp-0x94],8 ; ja exit):
# after bay object 8 run object 47 too
ship_loop:
        cmp     dword ptr [ebp-0x94], 9
        jne     1f
        mov     dword ptr [ebp-0x94], T16OBJ
1:      cmp     dword ptr [ebp-0x94], T16OBJ
        ret

# second loop clears 0x64840C[k] (= bay floats 0x648410[k-1]); not for object 47. Hook 0x442E9C.
ship_clear:
        mov     eax, [ebp-0x94]
        cmp     eax, T16OBJ
        je      1f
        mov     dword ptr [eax*4+0x64840C], 0
1:      ret

# fmul [ecx*4+0x5F1AB4] (per-object float, ecx = object), hook 0x4454E7: T-16 uses the speeder's
obj_fmul:
        cmp     ecx, T16OBJ
        jne     1f
        fmul    dword ptr ds:[0x5F1AB8]
        ret
1:      fmul    dword ptr [ecx*4+0x5F1AB4]
        ret

# mov ecx,[eax*4+0x5F1B64] (speech list per object), hook 0x447076: T-16 has none
obj_speech:
        cmp     eax, T16OBJ
        jne     1f
        mov     ecx, 0x5F1B60              # empty list (also used by the Naboo bay)
        ret
1:      mov     ecx, [eax*4+0x5F1B64]
        ret

# registration of "-stars" (call 0x443015 at 0x441C51): register it, then "+t16#" before the
# level environment object
register:
        push    dword ptr [esp+0xC]
        push    dword ptr [esp+0xC]
        push    dword ptr [esp+0xC]
        CALLABS 0x443015
        add     esp, 0xC
        push    0x621                      # same flags as the other craft bays
        push    NAME
        push    T16VAR
        CALLABS 0x443015
        add     esp, 0xC
        ret

# model file load of imp_stuff/tieinter (call 0x46FA6C at 0x441D63): also load pl_crafts/t16
load_models:
        push    dword ptr [esp+0x10]
        push    dword ptr [esp+0x10]
        push    dword ptr [esp+0x10]
        push    dword ptr [esp+0x10]
        CALLABS 0x46FA6C
        add     esp, 0x10
        push    0
        push    0
        push    0
        push    PATH
        CALLABS 0x46FA6C
        add     esp, 0x10
        ret

# placement lookup 0x4CBA60(level, name) at 0x442030: the hangar level has no T-16 record
placement:
        cmp     dword ptr [ebp-0x94], T16OBJ
        jne     1f
        mov     eax, FAKE_OBJ
        ret
1:      JMPABS  0x4CBA60

# launch route lookup 0x4CBB36(level, out, name) at 0x44226C: out = {count, points, knots}
route:
        cmp     dword ptr [ebp-0x94], T16OBJ
        jne     1f
        mov     ecx, [esp+8]
        mov     dword ptr [ecx], 5
        mov     dword ptr [ecx+4], RT_PTS
        mov     dword ptr [ecx+8], RT_KNOTS
        mov     eax, FAKE_RT
        ret
1:      JMPABS  0x4CBB36

# --- T-16 lasers aim like the X-wing's ---------------------------------------------------------
# T-16 update 0x41CF00 ends with call 0x41EF0D (hook 0x41D09C). Run the aim-assist finder first,
# exactly as the X-wing update does (0x42553x): finder 0x40C8FC(ship mtx rec+4, out info+0x1C,
# prev target info+0x1A, range 9 (16 in cockpit view), cos 0.992, bolt speed) -> info+0x1A.
# [ebp+8] = player info, [ebp-8] = craft record, as in the X-wing update.
t16_find:
        mov     ecx, [ebp+8]
        mov     ds:[INFOPTR], ecx          # for the torpedo aim
        mov     edx, [ecx]
        imul    edx, edx, 0x12C
        mov     eax, [edx+0x705004]
        mov     edx, 0x41100000            # 9.0
        cmp     word ptr [eax+4], 3        # cockpit view
        jne     1f
        mov     edx, 0x41800000            # 16.0
1:      push    dword ptr ds:[0x41CE7F]    # the T-16's own bolt speed (FireWeapon push at 0x41CE7E)
        push    dword ptr ds:[0x425564]    # the X-wing's lock cone (cos 7.2 deg; 2.0 = none if aim assist is removed)
        push    edx
        movzx   eax, word ptr [ecx+0x1A]
        push    eax
        lea     eax, [ecx+0x1C]
        push    eax
        mov     eax, [ebp-8]
        call    aim_mtx                    # ship matrix with forward lowered onto the crosshair
        push    eax
        CALLABS 0x40C8FC
        add     esp, 0x18
        mov     ecx, [ebp+8]
        mov     [ecx+0x1A], ax             # target id or 0xFFFF
        JMPABS  0x41EF0D                   # the replaced call (its args are still on the stack)

# T-16 fire 0x41CE38: after the hardpoint matrix is read (hook 0x41CE71: add esp,0x18 / mov
# eax,[ebp-0x34]) aim the bolt. Bolt matrix at [ebp-0x30]: pos, forward, second axis, third.
t16_aim:
        pop     edx
        add     esp, 0x18
        push    edx
        push    esi
        lea     esi, [ebp-0x30]
        mov     ecx, [ebp+8]               # player info
        mov     edx, [ebp-0x34]            # craft record: pos +4, forward +0x10, down +0x1C
        call    aim_core
        pop     esi
        mov     eax, [ebp-0x34]            # replayed
        ret

# hangar launch state 5 (0x444F0A): the fire/select button skips the fly-out. The T-16 has no
# launch route in the hangar level and crashes at the end of it, so it always skips.
# Hook 0x444F19 (and eax,0x9000 / test eax,eax), followed by je.
t16_skip:
        and     eax, 0x9000
        cmp     byte ptr ds:[0x648164], T16OBJ
        jne     1f
        or      eax, 0x9000
1:      test    eax, eax
        ret

# xmm3 = |[eax]| (3 floats); uses xmm4 only
vlen:
        movss   xmm3, [eax]
        mulss   xmm3, xmm3
        movss   xmm4, [eax+4]
        mulss   xmm4, xmm4
        addss   xmm3, xmm4
        movss   xmm4, [eax+8]
        mulss   xmm4, xmm4
        addss   xmm3, xmm4
        sqrtss  xmm3, xmm3
        ret

# --- page 2 of the cave (BASE+0x700, after the data) ---------------------------------------------
        .org    0x700
# Aim the projectile matrix at esi (pos +0, forward +0xC, second axis +0x18) for the T-16:
# straight at the finder's aim point (ecx = player info, target +0x1A, aim point +0x1C; the finder
# already searched around the crosshair line) or, with no target, the nose line at DEFDIST lowered
# by DEFDIST*TANDOWN along the ship's down axis (edx = craft record).
aim_core:
        cmp     word ptr [ecx+0x1A], 0xFFFF
        je      2f
        movss   xmm0, [ecx+0x1C]           # target: aim point as is
        movss   xmm1, [ecx+0x20]
        movss   xmm2, [ecx+0x24]
        jmp     4f
2:      movss   xmm5, ds:[DEFDIST]         # no target: base = nose line at DEFDIST
        movss   xmm0, [edx+0x10]
        mulss   xmm0, xmm5
        addss   xmm0, [edx+4]
        movss   xmm1, [edx+0x14]
        mulss   xmm1, xmm5
        addss   xmm1, [edx+8]
        movss   xmm2, [edx+0x18]
        mulss   xmm2, xmm5
        addss   xmm2, [edx+0xC]
3:      mulss   xmm5, ds:[TANDOWN]         # lower by z*tan(angle): the T-16 crosshair sits low
        movss   xmm6, [edx+0x1C]
        mulss   xmm6, xmm5
        addss   xmm0, xmm6
        movss   xmm6, [edx+0x20]
        mulss   xmm6, xmm5
        addss   xmm1, xmm6
        movss   xmm6, [edx+0x24]
        mulss   xmm6, xmm5
        addss   xmm2, xmm6
4:      subss   xmm0, [esi]           # v = aim point - muzzle
        subss   xmm1, [esi+4]
        subss   xmm2, [esi+8]
        movss   xmm3, xmm0
        mulss   xmm3, xmm0
        movss   xmm4, xmm1
        mulss   xmm4, xmm1
        addss   xmm3, xmm4
        movss   xmm4, xmm2
        mulss   xmm4, xmm2
        addss   xmm3, xmm4
        sqrtss  xmm3, xmm3
        comiss  xmm3, ds:[EPS]
        jbe     9f
        movss   xmm4, ds:[ONE]
        divss   xmm4, xmm3
        mulss   xmm0, xmm4                 # v^
        mulss   xmm1, xmm4
        mulss   xmm2, xmm4
        # forward axis = v^ * |forward|
        lea     eax, [esi+0xC]
        call    vlen
        movss   xmm4, xmm0
        mulss   xmm4, xmm3
        movss   [esi+0xC], xmm4
        movss   xmm4, xmm1
        mulss   xmm4, xmm3
        movss   [esi+0x10], xmm4
        movss   xmm4, xmm2
        mulss   xmm4, xmm3
        movss   [esi+0x14], xmm4
        # second axis: remove its v^ component, keep its length
        lea     eax, [esi+0x18]
        call    vlen
        movss   xmm7, xmm3                 # |second|
        movss   xmm5, [esi+0x18]           # d = second . v^
        mulss   xmm5, xmm0
        movss   xmm6, [esi+0x1C]
        mulss   xmm6, xmm1
        addss   xmm5, xmm6
        movss   xmm6, [esi+0x20]
        mulss   xmm6, xmm2
        addss   xmm5, xmm6
        movss   xmm4, xmm0
        mulss   xmm4, xmm5
        movss   xmm6, [esi+0x18]
        subss   xmm6, xmm4
        movss   [esi+0x18], xmm6
        movss   xmm4, xmm1
        mulss   xmm4, xmm5
        movss   xmm6, [esi+0x1C]
        subss   xmm6, xmm4
        movss   [esi+0x1C], xmm6
        movss   xmm4, xmm2
        mulss   xmm4, xmm5
        movss   xmm6, [esi+0x20]
        subss   xmm6, xmm4
        movss   [esi+0x20], xmm6
        lea     eax, [esi+0x18]
        call    vlen
        comiss  xmm3, ds:[EPS]
        jbe     9f
        divss   xmm7, xmm3                 # rescale to the old length
        movss   xmm4, [esi+0x18]
        mulss   xmm4, xmm7
        movss   [esi+0x18], xmm4
        movss   xmm4, [esi+0x1C]
        mulss   xmm4, xmm7
        movss   [esi+0x1C], xmm4
        movss   xmm4, [esi+0x20]
        mulss   xmm4, xmm7
        movss   [esi+0x20], xmm4
9:      ret

# torpedo / missile fire 0x423F08 (shared by all craft): after the "scnd" hardpoint matrix is read
# (hook 0x423F24: add esp,0x18 / mov edx,[0x704DFC]) aim it like the T-16's lasers when the
# player flies the T-16. Matrix at [ebp-0x6C], owner id [ebp+0xC].
t16_torp:
        pop     eax
        add     esp, 0x18
        push    eax
        cmp     byte ptr ds:[0x704221], 7  # player craft = T-16
        jne     1f
        mov     ax, [ebp+0xC]
        cmp     ax, word ptr ds:[0x704D44+0xB6]   # fired by the player
        jne     1f
        mov     ecx, ds:[INFOPTR]
        test    ecx, ecx
        jz      1f
        push    esi
        lea     esi, [ebp-0x6C]
        mov     edx, 0x704D44              # player craft record
        call    aim_core
        pop     esi
1:      mov     edx, ds:[0x704DFC]         # replayed
        ret

# eax = craft record (pos +4, forward +0x10, down +0x1C) -> eax = AIMMTX: pos, then the forward
# axis turned down by the aim-down angle (the T-16 crosshair sits below the nose line), so the
# finder's cone (and convergence, which hooks the finder) centre on the crosshair. The finder
# (wrapper mode 0) reads only pos +0 and forward +0xC.
aim_mtx:
        movss   xmm0, [eax+4]
        movss   ds:[AIMMTX], xmm0
        movss   xmm0, [eax+8]
        movss   ds:[AIMMTX+4], xmm0
        movss   xmm0, [eax+0xC]
        movss   ds:[AIMMTX+8], xmm0
        movss   xmm0, [eax+0x1C]           # forward + down*tan
        mulss   xmm0, ds:[TANDOWN]
        addss   xmm0, [eax+0x10]
        movss   xmm1, [eax+0x20]
        mulss   xmm1, ds:[TANDOWN]
        addss   xmm1, [eax+0x14]
        movss   xmm2, [eax+0x24]
        mulss   xmm2, ds:[TANDOWN]
        addss   xmm2, [eax+0x18]
        movss   ds:[AIMMTX+0xC], xmm0
        movss   ds:[AIMMTX+0x10], xmm1
        movss   ds:[AIMMTX+0x14], xmm2
        mov     eax, AIMMTX+0xC
        call    vlen                       # back to unit length
        movss   xmm4, ds:[ONE]
        divss   xmm4, xmm3
        mulss   xmm0, xmm4
        mulss   xmm1, xmm4
        mulss   xmm2, xmm4
        movss   ds:[AIMMTX+0xC], xmm0
        movss   ds:[AIMMTX+0x10], xmm1
        movss   ds:[AIMMTX+0x14], xmm2
        mov     eax, AIMMTX
        ret

# cutscenes put the player's craft model in (0x4312AE, craft read at 0x42A178): the T-16 crashed
# the end cutscene, so cutscenes show an X-wing instead
cut_craft:
        mov     dl, byte ptr ds:[0x704221]
        cmp     dl, 7
        jne     1f
        xor     dl, dl
1:      ret
