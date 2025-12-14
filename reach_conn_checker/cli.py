
import time
import sys
from .core import ConnectionManager
from .yaku_rules import YakuChecker
from .score_counter import ScoreCalculator
from .cpu import CpuAgent
from .network_rules import check_protocol_readiness

# Global interface reference for helper functions
# In a cleaner architecture, we'd pass this around, but for minimal refactor of functions:
# We will pass 'interface' as an argument to functions that need to print.

def get_user_input(interface):
    """Wait for user input while refreshing UI."""
    while True:
        cmd = interface.get_command()
        if cmd:
            return cmd
        interface.refresh()
        time.sleep(0.05)

def check_agari(manager, win_tile, is_tsumo):
    # Temporary check using protocol readiness wrapper
    is_menzen = (len(manager.melds) == 0)
    checker = YakuChecker(manager.hand, win_tile, is_tsumo=is_tsumo, is_menzen=is_menzen)
    res = checker.execute()
    return len(res['yaku']) > 0

def display_result(interface, manager, win_tile, is_tsumo):
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
    
    interface.log("\n=== CONNECTION REPORT ===", 2)
    interface.log(f"Status: ESTABLISHED ({res['score_name'] or 'Agari'})", 2)
    interface.log("Protocol Standards (Yaku):")
    for y in res['yaku']:
        interface.log(f"  * {y}")
    
    interface.log(f"\nComplexity Overhead: {real_fu} Fu")
    interface.log(f"Total Latency Impact: {res['han']} Han")
    interface.log("Traffic Load Analysis")
    interface.log(f"  TOTAL: {score_data['total']} packets")
    interface.log(f"  PAYLOAD: {score_data['payments']}")
    interface.log("=========================", 2)
    
    interface.refresh()
    # Wait for user acknowledgment
    interface.log("Press Enter to exit...")
    get_user_input(interface)

def check_reach_possible(manager):
    if manager.melds: return False
    from .network_rules import check_discard_for_tenpai
    valid_discards = check_discard_for_tenpai(manager.hand)
    return len(valid_discards) > 0

def check_ron_opportunity(manager, tile):
    if len(manager.hand) != 13: return False
    temp_hand = manager.hand + [tile]
    is_menzen = (len(manager.melds) == 0)
    checker = YakuChecker(temp_hand, win_tile=tile, is_tsumo=False, is_menzen=is_menzen)
    res = checker.execute()
    return len(res['yaku']) > 0

def game_loop(stdscr):
    from .tui import CursesInterface # Lazy import to avoid top-level issues
    interface = CursesInterface(stdscr)
    
    interface.log("Initializing connection checker...", 1)
    
    manager = ConnectionManager()
    cpu = CpuAgent()
    
    # Initialize CPU Hand
    for _ in range(13):
        if manager.deck:
            t = manager.deck.pop()
            cpu.draw(t)
            
    interface.log("Target system: 192.168.1.1 (ESTABLISHED)", 1)
    interface.log("Monitoring traffic... (Type 'help' for commands)", 1)
    
    interface.update_status(manager, cpu)
    interface.refresh()

    while True:
        # --- PLAYER TURN ---
        
        # 1. Check Player Ron on CPU's last discard
        if cpu.latest_discard:
            if check_ron_opportunity(manager, cpu.latest_discard):
                interface.log(f"!!! OPPORTUNITY: Remote packet {cpu.latest_discard} matches signature! !!!", 3)
                interface.log("Type 'sudo' to capture (Ron) or Enter to ignore.", 3)
                
                user_in = get_user_input(interface)
                if user_in == "sudo":
                    manager.hand.append(cpu.latest_discard)
                    display_result(interface, manager, cpu.latest_discard, is_tsumo=False)
                    return
                else:
                    interface.log("Packet ignored.")
        
        # 2. Draw Tile
        drawn = None
        if len(manager.hand) < 14:
            if not manager.deck:
                interface.log("Connection timed out (No more packets).", 4)
                get_user_input(interface)
                break
            drawn = manager.deck.pop() 
            manager.hand.append(drawn)
            interface.update_status(manager, cpu) # Update HUD
            interface.log(f"Incoming packet: {drawn}")
            
            # Check Tsumo (Agari)
            if manager.is_reach:
                 time.sleep(1)
                 interface.refresh() # Ensure sleep doesn't freeze UI updates if we had async (here it just blocks which is fine for effect)
                 if check_agari(manager, drawn, is_tsumo=True):
                     interface.log("!!! DETECTED PROTOCOL COMPLIANCE (TSUMO) !!!", 2)
                     display_result(interface, manager, drawn, is_tsumo=True)
                     return
                 else:
                     interface.log(f"Auto-forwarding packet: {drawn}")
                     manager.hand.pop() 
                     interface.update_status(manager, cpu)
                     # End Turn handled by loop continuation (skiplayer input)
        
        if not manager.is_reach and (drawn or len(manager.hand) == 14):
            interface.update_status(manager, cpu)
            
            # 3. Input Loop
            player_discarded_tile = None
            turn_end = False
            
            while not turn_end:
                cmd_str = get_user_input(interface)
                if not cmd_str: continue
                
                cmd = cmd_str.split()
                op = cmd[0]
                
                if op in ["exit", "quit"]:
                    return
                elif op == "help":
                    interface.log("Commands: ping <idx> (discard), sudo (agari), reach (declare pending), exit")
                elif op == "sudo":
                    if check_agari(manager, manager.hand[-1], is_tsumo=True):
                        display_result(interface, manager, manager.hand[-1], is_tsumo=True)
                        return
                    else:
                        interface.log("Error: Hand not compliant (No Agari).", 4)
                elif op == "ping": # Discard
                    if len(cmd) > 1 and cmd[1] == "-t":
                        if check_reach_possible(manager):
                           interface.log(f"Warning: Continuous ping initiated. Latency check started.", 3)
                           manager.is_reach = True
                           interface.update_status(manager, cpu)
                           interface.log("Select packet to drop to start continuous ping:")
                           continue
                        else:
                           interface.log("Error: Cannot start continuous ping (Not Tenpai or already Reach).", 4)
                    elif len(cmd) > 1 and cmd[1].isdigit():
                        idx = int(cmd[1])
                        if 0 <= idx < len(manager.hand):
                           player_discarded_tile = manager.discard(idx)
                           if player_discarded_tile:
                               interface.log(f"Packet forwarded: {player_discarded_tile}")
                               turn_end = True
                           else:
                               interface.log("Invalid packet index.", 4)
                        else:
                           interface.log("Invalid index.", 4)
                    else:
                        interface.log("Usage: ping <index>")
                else:
                    interface.log("Unknown command.")
            
            interface.update_status(manager, cpu)

        # Draw logic handled above puts drawn tile in hand. If reach, we pop it.
        # If normal play and we discarded, len is 13.
        # Check transition to CPU
        if manager.is_reach and drawn and len(manager.hand) == 13:
             player_discarded_tile = drawn # Auto discard

        # --- CPU TURN ---
        interface.log("--- [ REMOTE HOST ACTIONS ] ---", 5)
        interface.refresh()
        time.sleep(0.5)
        
        # 1. Check CPU Ron
        player_discard = player_discarded_tile if 'player_discarded_tile' in locals() and player_discarded_tile else None
        
        if player_discard:
            if cpu.can_ron(player_discard):
                 interface.log(f"!!! CPU DETECTED VULNERABILITY (RON) on {player_discard} !!!", 4)
                 interface.log("CPU Wins! (Connection Terminated by Remote Host)", 4)
                 interface.log("Press Enter to exit...")
                 get_user_input(interface)
                 return

        # 2. CPU Draw
        if not manager.deck:
             interface.log("Connection timed out (No more packets).", 4)
             get_user_input(interface)
             return
        cpu_drawn = manager.deck.pop()
        cpu.draw(cpu_drawn)
        
        # 3. CPU Tsumo
        if cpu.check_tsumo():
             interface.log(f"!!! CPU SELF-HOSTED COMPLETE (TSUMO) on {cpu_drawn} !!!", 4)
             interface.log("CPU Wins!", 4)
             interface.log("Press Enter to exit...")
             get_user_input(interface)
             return
             
        # 4. CPU Discard
        cpu_discard = cpu.discard()
        interface.log(f"Remote host forwarded: {cpu_discard}")
        interface.refresh()
        # time.sleep(0.5)

def main():
    try:
        import curses
    except ImportError:
        # This handles the case where _curses is missing (common on Windows without windows-curses)
        if sys.platform.startswith('win'):
            sys.stderr.write("Error: 'windows-curses' is required to run this application on Windows.\n")
            sys.stderr.write("Please run: pip install windows-curses\n")
        else:
            sys.stderr.write("Error: 'curses' module not found.\n")
        sys.exit(1)
        
    try:
        curses.wrapper(game_loop)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Fallback to stderr printing if curses fails badly
        sys.stderr.write(f"Critical UI Error: {e}")

