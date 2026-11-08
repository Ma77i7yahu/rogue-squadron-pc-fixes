# Rogue Squadron PC - laser convergence v5 (Rebel Strike method + menu toggle).
#
# 1) Hooked at the end of the aim-assist target finder wrapper 0x40C8FC (used by
#    the A-wing, X-wing, Y-wing turret, TIE Interceptor, Naboo starfighter,
#    Snowspeeder and V-wing; the Falcon calls 0x40C5D6 directly and keeps its
#    turret tracking). The game picks the target with its own per-craft cone,
#    range and lead, and writes the point the guns should aim at to [ebp+0xC].
#    We move that point onto the craft's nose line at the same depth:
#        P' = C + F * max((P - C) . F, MIN)
#    so the guns converge at the target's distance but shots always go where
#    the crosshair points - no pull toward the target. With convergence
#    switched off in the menu we report "no target", i.e. no aim assist.
#
# 2) The setting is GENERAL option 5 of the game's settings store (block
#    0x7035E0, saved to the pilot file). It lives in the spare padding byte at
#    +0x1C5 (0x7037A5) after the 35-slot passcode list; 0 = ON so existing
#    pilots start with it on. The store's Get/Set handlers for GENERAL only
#    knew indices 0-4 and 6; the hooks below add index 5.
.intel_syntax noprefix
.code32
.equ D, 0x7ff000 + 0x300             # data: +0 MIN, +0x40 converged count, +0x44 last depth
.equ CONV_OFF, 0x7037a5              # settings byte, 0 = convergence on

.text
entry:
    add   esp, 0x1c                  # replaced: add esp,0x1c ; pop ebp ; ret
    cmp   ax, 0xffff
    je    out
    cmp   byte ptr [CONV_OFF], 0
    jne   no_target
    mov   ecx, [ebp+8]               # craft matrix: pos +0, forward +0xC
    mov   edx, [ebp+0xc]             # aim point written by the finder
    movss xmm0, [edx]
    subss xmm0, [ecx]
    movss xmm1, [edx+4]
    subss xmm1, [ecx+4]
    movss xmm2, [edx+8]
    subss xmm2, [ecx+8]
    mulss xmm0, [ecx+0xc]
    mulss xmm1, [ecx+0x10]
    mulss xmm2, [ecx+0x14]
    addss xmm0, xmm1
    addss xmm0, xmm2                 # depth along the nose
    maxss xmm0, [D+0]
    movss [D+0x44], xmm0
    inc   dword ptr [D+0x40]
    movss xmm1, [ecx+0xc]
    mulss xmm1, xmm0
    addss xmm1, [ecx]
    movss [edx], xmm1
    movss xmm1, [ecx+0x10]
    mulss xmm1, xmm0
    addss xmm1, [ecx+4]
    movss [edx+4], xmm1
    movss xmm1, [ecx+0x14]
    mulss xmm1, xmm0
    addss xmm1, [ecx+8]
    movss [edx+8], xmm1
out:
    pop   ebp
    ret
no_target:
    mov   ax, 0xffff
    pop   ebp
    ret

# Settings store Get, GENERAL index >= 5 (replaces 0x4DCE99..0x4DCEA6).
# [ebp-0x18] = index, [ebp+0x18] = int* out.
.org 0x100
get_general:
    mov   edx, [ebp-0x18]
    cmp   edx, 6
    je    get_passcode
    cmp   edx, 5
    jne   get_done
    mov   ecx, [ebp+0x18]
    xor   eax, eax
    cmp   byte ptr [CONV_OFF], 0
    sete  al
    mov   [ecx], eax
get_done:
    push  0x4dcebe
    ret
get_passcode:
    push  0x4dcea7
    ret

# Settings store Set, GENERAL index >= 5 (replaces 0x4DCFEE..0x4DCFFB).
# [ebp+0xC] = index, [ebp+0x18] = value.
.org 0x140
set_general:
    mov   edx, [ebp+0xc]
    cmp   edx, 6
    je    set_passcode
    cmp   edx, 5
    jne   set_done
    cmp   dword ptr [ebp+0x18], 0
    sete  byte ptr [CONV_OFF]
set_done:
    push  0x4dd013
    ret
set_passcode:
    push  0x4dcffc
    ret
