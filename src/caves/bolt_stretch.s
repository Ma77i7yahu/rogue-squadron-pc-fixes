# Rogue Squadron PC - stretch the player's laser bolt model (test).
# Hooked in the laser create handler at 0x4C43BE, after the bolt's velocity (+0xC0) has been
# computed from its forward axis. The bolt's matrix is at laser+0x9C: pos +0x9C, forward +0xA8,
# second axis +0xB4. Scaling the axes the model is drawn with makes it longer / thicker without
# changing how it moves (movement uses the stored velocity).
# Lives in the .conv section at 0x7FF900 (free gap after the help-text table).
        .intel_syntax noprefix
        .code32
        .text
        .equ K_LEN, 0x7FF9F0               # first axis (+0xA8) scale = bolt LENGTH (along travel)
        .equ K_WID, 0x7FF9F4               # second axis (+0xB4) scale = bolt THICKNESS (x4 gave big diamonds)
entry:
        mov     eax, [ebp-0x70]            # create info
        movzx   ecx, word ptr [eax+0x18]   # owner id
        movzx   edx, word ptr [ebp-0x6c]   # player id
        cmp     ecx, edx
        jne     done
        mov     ecx, [ebp-0x54]            # laser
        movss   xmm1, dword ptr ds:[K_LEN]
        movss   xmm0, dword ptr [ecx+0xA8]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xA8], xmm0
        movss   xmm0, dword ptr [ecx+0xAC]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xAC], xmm0
        movss   xmm0, dword ptr [ecx+0xB0]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xB0], xmm0
        movss   xmm1, dword ptr ds:[K_WID]
        movss   xmm0, dword ptr [ecx+0xB4]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xB4], xmm0
        movss   xmm0, dword ptr [ecx+0xB8]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xB8], xmm0
        movss   xmm0, dword ptr [ecx+0xBC]
        mulss   xmm0, xmm1
        movss   dword ptr [ecx+0xBC], xmm0
done:
        mov     ecx, [ebp-0x54]            # replayed: mov ecx,[ebp-0x54] ; add ecx,0x9C
        add     ecx, 0x9C
        push    0x4C43C7
        ret
