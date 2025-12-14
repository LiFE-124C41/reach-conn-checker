import random
from .network_rules import check_protocol_readiness, _parse_hand

class CpuAgent:
    def __init__(self, tiles=None):
        self.hand = tiles if tiles else []
        self.latest_discard = None
        self.is_reach = False

    def initialize_hand(self, all_tiles):
        """Draws 13 tiles from the deck."""
        self.hand = []
        for _ in range(13):
            if not all_tiles: break
            self.hand.append(all_tiles.pop())
        self.sort_hand()

    def draw(self, tile):
        self.hand.append(tile)
        self.sort_hand()
        # Auto-Reach Check? Could be added here.

    def discard(self):
        """
        Selects a tile to discard.
        Strategy:
        1. If Reach, discard drawn tile (unless Agari).
        2. Else, simple strategy: discard isolated terminals or honors, then random.
        For now: Random or just index -1? 
        Let's do simple random for now to ensure flow works.
        """
        if not self.hand: return None
        
        # If Reach, usually just tsumogiri (but we handle logic outside or here?)
        # Let's assume logic calls discard, and if reach, we must discard the last drawn one? 
        # But we sort hand... we need to track drawn tile.
        # For simplicity in this version, let's just pick one randomly.
        
        discard_index = random.randint(0, len(self.hand) - 1)
        discard_tile = self.hand.pop(discard_index)
        self.latest_discard = discard_tile
        self.sort_hand()
        return discard_tile

    def can_ron(self, tile_str):
        """Checks if the CPU can Ron on the given tile."""
        # Check if adding this tile makes a complete hand
        temp_hand = self.hand + [tile_str]
        
        # We need a strict Agari check, not just Tenpai.
        # "check_protocol_readiness" returns (is_tenpai, wait_tiles).
        # Agari means: check_protocol_readiness on 14 tiles returns... wait?
        # No, check_protocol_readiness is for 13 tiles checking if Tenpai.
        # For 14 tiles (Agari), we can use "decompose_hand" logic from yaku_rules 
        # but that handles decomposition.
        # Or simpler:
        # If we have 13 tiles, adding 'tile_str' makes 14.
        # If we treat it as 14 tiles, does it decompose into 4 melds + 1 pair?
        # Let's use `yaku_rules` decompose if possible, or re-use `check_protocol_readiness`.
        
        # `check_protocol_readiness` checks if 13 tiles are waiting for something.
        # If "tile_str" is in the wait list of the current 13-tile hand, then it's Agari!
        
        is_tenpai, wait_tiles = check_protocol_readiness(self.hand)
        if is_tenpai and tile_str in wait_tiles:
            return True
            
        return False

    def check_tsumo(self):
        """Checks if the current 14-tile hand is Agari (Tsumo)."""
        from .network_rules import validate_packet_structure
        if len(self.hand) != 14: return False
        return validate_packet_structure(self.hand)

    def sort_hand(self):
        # Sort based on internal int value
        # This helps CPU logic later
        try:
            self.hand.sort(key=lambda x: _parse_hand([x])[0])
        except:
            pass # Fallback if parsing fails
