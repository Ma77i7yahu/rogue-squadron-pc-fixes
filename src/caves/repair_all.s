# Every craft repairs itself - replaces the game's repair fn 40EBE8(rec, dt) in place
# (40EBE8..40ECCD, 0xE6 bytes incl. its old jump/byte tables). Called from the shared craft
# update 40ECCE, so every craft runs it.
#
# Stock: +max/180 per second ([rec+0xC0] up to [rec+0xC4]) for craft types X 0, Y 1,
# Falcon 5 and Naboo 8 only, while health > 0, [705508] != 3 and the R2 flag byte 5E9384 is
# set. The X/Y/Naboo damage cases clear that flag (with "R2 hit" speech) once health drops
# under 25%, which stops the repair for the rest of the life.
#
# Here: every craft repairs. The craft without a droid or crew (A 2, V 3, speeder 4, TIE 6,
# T-16 7) silently clear the same flag once health is under 25%, so they lose their repair the
# same way. The flag only drives droid chatter for types 0/1/8, so nothing else changes.
        .intel_syntax noprefix
        .set NODROID, (1<<2)|(1<<3)|(1<<4)|(1<<6)|(1<<7)
        .set R2FLAG, 0x5E9384
        .set QUARTER, 0x5BF4E8          # 0.25
        .set SECS, 0x5BF468             # 180.0
        .text
repair:
        push ebp
        mov ebp, esp
        mov ecx, [ebp+8]
        cmp dword ptr [ecx+0xC0], 0     # health > 0 (positive float as int)
        jle done
        cmp dword ptr [0x705508], 3
        je done
        cmp byte ptr [R2FLAG], 0
        je done
        movzx edx, word ptr [ecx+0xB4]  # craft type
        fld dword ptr [ecx+0xC0]
        fcomp dword ptr [ecx+0xC4]
        fnstsw ax
        test ah, 0x40                   # already full
        jnz done
        mov eax, NODROID
        bt eax, edx
        jnc heal
        fld dword ptr [ecx+0xC0]
        fdiv dword ptr [ecx+0xC4]
        fcomp dword ptr [QUARTER]
        fnstsw ax
        test ah, 1
        jz heal
        mov byte ptr [R2FLAG], 0        # "droid lost": no more repair
        jmp done
heal:
        fld dword ptr [ecx+0xC4]
        fdiv dword ptr [SECS]
        fmul dword ptr [ebp+0xC]
        fadd dword ptr [ecx+0xC0]
        fst dword ptr [ecx+0xC0]
        fcomp dword ptr [ecx+0xC4]
        fnstsw ax
        test ah, 0x41
        jnz done
        mov eax, [ecx+0xC4]
        mov [ecx+0xC0], eax
done:
        mov esp, ebp
        pop ebp
        ret
