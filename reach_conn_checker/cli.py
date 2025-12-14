
import time
from .core import ConnectionManager, print_fake_log
from .yaku_rules import YakuChecker
from .score_counter import ScoreCalculator
from .cpu import CpuAgent
from .network_rules import check_protocol_readiness

def display_hand(manager):
    """ 手牌をメモリーダンプ風に表示する """
    print("\n--- SYSTEM MEMORY DUMP ---")
    line = ""
    for index, tile in enumerate(manager.get_hand()):
        # 辞書にない牌はUNKNOWNとする
        code = manager.get_code(tile) 
        # キー入力用のインデックスも目立たないように表示
        line += f"[{index}:{code}] "
    print(line)
    print("--------------------------\n")

def check_agari(manager, win_tile, is_tsumo):
    # Temporary check using protocol readiness wrapper
    # Real logic: YakuChecker
    is_menzen = (len(manager.melds) == 0) # Assuming melds not implemented in current core yet, but using attribute if exists
    # Or just len(manager.hand) == 14 waiting implies menzen if no open melds declared
    
    checker = YakuChecker(manager.hand, win_tile, is_tsumo=is_tsumo, is_menzen=is_menzen)
    res = checker.execute()
    return len(res['yaku']) > 0

def display_result(manager, win_tile, is_tsumo):
    is_menzen = (len(manager.melds) == 0)
    checker = YakuChecker(manager.hand, win_tile, is_tsumo=is_tsumo, is_menzen=is_menzen)
    res = checker.execute()
    
    calc = ScoreCalculator()
    
    # Calculate real Fu
    real_fu = res['fu'] # Default 30
    if res['structure']:
        real_fu = calc.calculate_fu(
            res['structure'],
            win_tile_str=win_tile,
            is_tsumo=is_tsumo,
            is_menzen=is_menzen,
            yaku_names=res['yaku']
        )
        
    score_data = calc.calculate_score(res['han'], real_fu, is_oya=False, is_tsumo=is_tsumo)
    
    print("\n=== CONNECTION REPORT ===")
    print(f"Status: ESTABLISHED ({res['score_name'] or 'Agari'})")
    print("Protocol Standards (Yaku):")
    for y in res['yaku']:
        print(f"  * {y}")
    
    print(f"\nComplexity Overhead: {real_fu} Fu")
    print(f"Total Latency Impact: {res['han']} Han")
    print("Traffic Load Analysis")
    print(f"  TOTAL: {score_data['total']} packets")
    print(f"  PAYLOAD: {score_data['payments']}")
    print("=========================")

def check_reach_possible(manager):
    """
    Checks if Reach is possible (14 tiles -> discard 1 to Tenpai).
    Returns True if at least one discard leads to Tenpai.
    """
    # Must be menzen
    if manager.melds: return False
    
    # Use check_discard_for_tenpai (returns list of valid discards)
    from .network_rules import check_discard_for_tenpai
    valid_discards = check_discard_for_tenpai(manager.hand)
    return len(valid_discards) > 0

def check_ron_opportunity(manager, tile):
    # Check if adding tile makes Agari
    # 13 tiles in hand
    if len(manager.hand) != 13: return False
    
    # We must construct a TEMPORARY hand list to check
    temp_hand = manager.hand + [tile]
    
    is_menzen = (len(manager.melds) == 0)
    checker = YakuChecker(temp_hand, win_tile=tile, is_tsumo=False, is_menzen=is_menzen)
    res = checker.execute()
    return len(res['yaku']) > 0

def interactive_mode():
    print("Initializing connection checker...")
    time.sleep(1)
    
    manager = ConnectionManager()
    cpu = CpuAgent()
    
    # Initialize CPU Hand by drawing from manager's deck
    # Note: Manager.draw_tile() is distinct from manager.draw() depending on core.py version?
    # core.py usually has `draw`. Let's assume `draw` returns a tile string.
    # Note: ConnectionManager in core.py probably has `draw`.
    
    for _ in range(13):
        # We need a method to draw from deck without adding to player hand.
        # If manager.draw() adds to self.hand, we are in trouble.
        # Let's inspect core.py if possible, but assuming manager has a method to just return a tile 
        # or we pop from manager.deck if accessible.
        # Safe bet: manager.deck is a list.
        if manager.deck:
            t = manager.deck.pop()
            cpu.draw(t)
            
    print("Target system: 192.168.1.1 (ESTABLISHED)")
    print("Monitoring traffic... (Type 'help' for commands)")

    while True:
        # --- PLAYER TURN ---
        print("\n--- [ YOU ] ---")
        
        # 1. Check Player Ron on CPU's last discard
        if cpu.latest_discard:
            if check_ron_opportunity(manager, cpu.latest_discard):
                print(f"!!! OPPORTUNITY: Remote packet {cpu.latest_discard} matches signature! !!!")
                print("Type 'sudo' to capture (Ron) or Enter to ignore.")
                
                # We need a non-blocking check or just blocking? Blocking is fine for turn based.
                user_in = input(">> ").strip()
                if user_in == "sudo":
                    # RON!
                    # Temporarily add tile to hand for result display
                    manager.hand.append(cpu.latest_discard)
                    display_result(manager, cpu.latest_discard, is_tsumo=False)
                    return
                else:
                    print("Packet ignored.")
        
        # 2. Draw Tile
        drawn = None
        if len(manager.hand) < 14:
            if not manager.deck:
                print("Connection timed out (No more packets).")
                break
            drawn = manager.deck.pop() # Direct access to avoid side effects of draw() logic
            manager.hand.append(drawn)
            print(f"Incoming packet: {drawn}")
            
            # Check Tsumo (Agari)
            # If Reach, we might auto-check.
            if manager.is_reach:
                 time.sleep(1)
                 if check_agari(manager, drawn, is_tsumo=True):
                     print("!!! DETECTED PROTOCOL COMPLIANCE (TSUMO) !!!")
                     display_result(manager, drawn, is_tsumo=True)
                     return
                 else:
                     print(f"Auto-forwarding packet: {drawn}")
                     # Discard the drawn tile
                     manager.hand.pop() # Remove last
                     # End Turn immediately
                     # goto CPU turn
        
        if not manager.is_reach:
            display_hand(manager)
            
            # 3. Input Loop
            player_discarded_tile = None
            turn_end = False
            
            while not turn_end:
                cmd = input(">> ").strip().split()
                if not cmd: continue
                op = cmd[0]
                
                if op in ["exit", "quit"]:
                    return
                elif op == "help":
                    print("Commands: ping <idx> (discard), sudo (agari), reach (declare pending), exit")
                elif op == "sudo":
                    if check_agari(manager, manager.hand[-1], is_tsumo=True):
                        display_result(manager, manager.hand[-1], is_tsumo=True)
                        return
                    else:
                        print("Error: Hand not compliant (No Agari).")
                elif op == "ping":
                    if len(cmd) > 1 and cmd[1] == "-t":
                        if check_reach_possible(manager):
                           print(f"Warning: Continuous ping initiated. Latency check started.")
                           manager.is_reach = True
                           # Must discard now.
                           print("Select packet to drop to start continuous ping:")
                           continue
                        else:
                           print("Error: Cannot start continuous ping (Not Tenpai or already Reach).")
                    elif len(cmd) > 1 and cmd[1].isdigit():
                        idx = int(cmd[1])
                        if 0 <= idx < len(manager.hand):
                           player_discarded_tile = manager.discard(idx)
                           if player_discarded_tile:
                               print(f"Packet forwarded: {player_discarded_tile}")
                               turn_end = True
                           else:
                               print("Invalid packet index.")
                        else:
                           print("Invalid index.")
                    else:
                        print("Usage: ping <index>")
                else:
                    print("Unknown command.")
        
        # --- CPU TURN ---
        print("\n--- [ CPU ] ---")
        time.sleep(0.5)
        
        # 1. Check CPU Ron on Player's discard
        player_discard = player_discarded_tile if 'player_discarded_tile' in locals() and player_discarded_tile else None
        
        # Note: If player in Reach auto-discarded, player_discarded_tile logic above might be skipped 
        # because I handled "manager.hand.pop()" directly.
        # I should catch that variable.
        if manager.is_reach and drawn and len(manager.hand) == 13: 
             # It means we popped the drawn tile.
             player_discard = drawn

        if player_discard:
            if cpu.can_ron(player_discard):
                 print(f"!!! CPU DETECTED VULNERABILITY (RON) on {player_discard} !!!")
                 print("CPU Wins! (Connection Terminated by Remote Host)")
                 return

        # 2. CPU Draw
        if not manager.deck:
             print("Connection timed out (No more packets).")
             return
        cpu_drawn = manager.deck.pop()
        cpu.draw(cpu_drawn)
        
        # 3. CPU Tsumo Check
        # Use check_tsumo() because hand is now 14 tiles
        if cpu.check_tsumo():
             print(f"!!! CPU SELF-HOSTED COMPLETE (TSUMO) on {cpu_drawn} !!!")
             print("CPU Wins!")
             return
             
        # 4. CPU Discard
        cpu_discard = cpu.discard()
        print(f"Remote host forwarded: {cpu_discard}")
        time.sleep(0.5)

def main():
    interactive_mode()
