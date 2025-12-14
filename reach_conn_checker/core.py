
import random
import time

# 麻雀牌をシステムログ風のコードに変換する辞書
# ここでは例として数牌の一部のみ定義しています
TILE_MAP = {
    # Manzu (1m - 9m)
    "1m": "ADDR_10", "2m": "ADDR_11", "3m": "ADDR_12",
    "4m": "ADDR_13", "5m": "ADDR_14", "6m": "ADDR_15",
    "7m": "ADDR_16", "8m": "ADDR_17", "9m": "ADDR_18",
    
    # Pinzu (1p - 9p)
    "1p": "PROC_20", "2p": "PROC_21", "3p": "PROC_22",
    "4p": "PROC_23", "5p": "PROC_24", "6p": "PROC_25",
    "7p": "PROC_26", "8p": "PROC_27", "9p": "PROC_28",
    
    # Souzu (1s - 9s)
    "1s": "THRD_30", "2s": "THRD_31", "3s": "THRD_32",
    "4s": "THRD_33", "5s": "THRD_34", "6s": "THRD_35",
    "7s": "THRD_36", "8s": "THRD_37", "9s": "THRD_38",
    
    # Honors
    "east": "HOST_E", "south": "HOST_S", "west": "HOST_W", "north": "HOST_N",
    "white": "[NULL]", "green": "[G_O_F]", "red": "[R_E_D]"
}

class ConnectionManager:
    """
    Manages the 'connection' (Game State).
    """
    """
    Manages the 'connection' (Game State).
    """
    def __init__(self):
        self.melds = [] # Open melds (e.g. ['koutsu', [1,1,1]])
        self.is_reach = False # Reach flag
        self.is_continuous = False # Auto mode flag
        
        # Initialize Full Deck
        # 4 of each tile in TILE_MAP (except EAST/SOUTH... we need all 34 types * 4)
        # TILE_MAP is incomplete in the snippet? 
        # Actually TILE_MAP is just for display.
        # We need a proper full deck generator.
        # 1-9 m,p,s + 7 honors.
        self.deck = []
        suffixes = ['m', 'p', 's']
        honors = ['east', 'south', 'west', 'north', 'white', 'green', 'red']
        
        for s in suffixes:
            for n in range(1, 10):
                 self.deck.extend([f"{n}{s}"] * 4)
        for h in honors:
            self.deck.extend([h] * 4)
            
        random.shuffle(self.deck)
        
        # Deal initial hand (13 tiles)
        self.hand = []
        for _ in range(13):
             if self.deck: self.hand.append(self.deck.pop())
    
    
    def _sort_key(self, tile):
        """
        Sort key for proper 'Riipai' (sorting).
        Order: Manzu -> Pinzu -> Souzu -> Winds -> Dragons
        """
        if tile == "unknown": return 999
        
        # Suffix priority: m=0, p=1, s=2
        if tile[-1] in 'mps':
            suit_order = {'m': 0, 'p': 100, 's': 200}
            suit = tile[-1]
            num = int(tile[:-1])
            return suit_order[suit] + num
            
        # Honors
        honor_order = {
            "east": 301, "south": 302, "west": 303, "north": 304,
            "white": 401, "green": 402, "red": 403
        }
        return honor_order.get(tile, 900)

    def get_hand(self):
        return sorted(self.hand, key=self._sort_key)

    def discard(self, display_index):
        """
        Discards a tile based on the displayed (sorted) index.
        """
        sorted_hand = self.get_hand()
        if 0 <= display_index < len(sorted_hand):
            tile_to_discard = sorted_hand[display_index]
            
            # Remove from internal hand
            # Use strict remove. If fails, it means inconsistency.
            try:
                self.hand.remove(tile_to_discard)
                return tile_to_discard
            except ValueError:
                # Should be impossible if sorted_hand comes from self.hand
                # But adding debug print just in case
                print(f"DEBUG_ERROR: Failed to remove {tile_to_discard} from hand {self.hand}")
                return None
                
        return None

    def draw_tile(self):
        """Draws a tile from the shared deck."""
        if not self.deck: return None
        return self.deck.pop()

    def draw(self):
        # Legacy Wrapper for old calls (adds to hand)
        # 14枚以上にならないようにするガード
        if len(self.hand) >= 14:
            return None
        
        tile = self.draw_tile()
        if tile:
             self.hand.append(tile)
        return tile

    def check_connection_stability(self):
        """
        Runs a deep packet inspection to verify connection stability.
        (Checks if the hand is a winning hand)
        """
        from .network_rules import validate_packet_structure
        return validate_packet_structure(self.hand)

    def check_readiness(self):
        """
        Checks if connection is ready for continuous monitoring (Reach/Tenpai).
        """
        from .network_rules import check_protocol_readiness
        return check_protocol_readiness(self.hand)

    def check_reachability(self):
        """
        For 14-tile hand: Checks which discard leads to Tenpai.
        Returns list of valid discards for Reach.
        """
        from .network_rules import check_discard_for_tenpai
        return check_discard_for_tenpai(self.hand)

    def get_code(self, tile):
        return TILE_MAP.get(tile, "UNKNOWN")

def print_fake_log(message):
    """ 現在時刻付きのログメッセージを表示する """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # 'INFO' というそれっぽいプレフィックスをつける
    print(f"[{timestamp}] [INFO] {message}")
    time.sleep(0.1) # 処理してる感を出すためのウェイト
