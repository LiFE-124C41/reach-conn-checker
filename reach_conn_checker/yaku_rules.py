"""
yaku_rules.py

This module implements the logic for verifying specific Mahjong Yaku (Protocol Standards).
It utilizes the structural analysis from `network_rules.py` to determine which 
compliance standards (Yaku) the current packet (hand) satisfies.
"""

from collections import Counter
from .network_rules import decompose_hand, _parse_hand

class YakuChecker:
    """
    Checks for various Yaku based on the hand structure.
    """
    def __init__(self, hand_input, win_tile=None, is_tsumo=False, is_reach=False, 
                 bakaze='east', jikaze='east', is_menzen=True):
        """
        Args:
            hand_input (list): List of tile strings (e.g. ['1m', '2m'...])
            win_tile (str): The tile used to win (Agari-hai).
            is_tsumo (bool): True if won by self-draw.
            is_reach (bool): True if Reach is declared.
            bakaze (str): Prevailing wind (e.g. 'east').
            jikaze (str): Seat wind (e.g. 'south').
            is_menzen (bool): True if hand is closed (no open melds).
        """
        self.hand_input = hand_input
        self.win_tile = win_tile
        self.is_tsumo = is_tsumo
        self.is_reach = is_reach
        self.bakaze = bakaze
        self.jikaze = jikaze
        self.is_menzen = is_menzen
        
        # Parse hand to integers for easier processing
        self.tiles_int = _parse_hand(hand_input)
        
        # Yaku names mapping (Japanese)
        self.YAKU_NAMES = {
            'reach': 'Reach (Continuous Ping)',
            'tanyao': 'Tanyao (Simple Routing)',
            'pinfu': 'Pinfu (Flat Network)',
            'ippatsu': 'Ippatsu (Instant Ack)',
            'menzen_tsumo': 'Menzen Tsumo (Self-Host)',
            'yakuhai_haku': 'Yakuhai: White (Null Packet)',
            'yakuhai_hatsu': 'Yakuhai: Green (Green OF)',
            'yakuhai_chun': 'Yakuhai: Red (Red Hat)',
            'yakuhai_bakaze': 'Yakuhai: Round Wind',
            'yakuhai_jikaze': 'Yakuhai: Seat Wind',
            'chitoitsu': 'Chi-toitsu (Seven Pairs)',
            'toitoi': 'Toi-Toi (All Triplets)',
            'sanankou': 'San Ankou (Three Concealed Triplets)',
            'ippeiko': 'Ippeiko (Redundant Mirroring)',
            'sanshoku': 'Sanshoku (Cross-Subnet Sync)',
            'itsu': 'Itsu (Full Spectrum Scan)',
            'honitsu': 'Honitsu (Port Isolation)',
            'chinitsu': 'Chinitsu (Dedicated Line)',
            'ryanpeiko': 'Ryanpeiko (Full Mirror Redundancy)',
            'chanta': 'Chanta (Edge Routing)',
            'junchan': 'Junchan (Strict Edge Routing)',
            'shosangen': 'Shosangen (Sub-Controller Cluster)',
            'sanshoku_douko': 'Sanshoku Douko (Cross-Platform Triplets)',
            'honroutou': 'Honroutou (Backbone Nodes Only)',
        }
        
    def execute(self):
        """
        Performs the Yaku check.
        Returns a dictionary containing:
            - 'yaku': List of yaku names (list of tuples: (name, han))
            - 'han': Total Han count
            - 'fu': Fu count (placeholder for now)
            - 'score_name': Display name for score (e.g. Mangan)
        """
        structures = decompose_hand(self.hand_input)
        if not structures:
            return {'yaku': [], 'han': 0, 'fu': 0, 'score_name': '', 'structure': None}
            
        best_result = {'han': -1}
        
        for struct in structures:
            current_yaku = []
            
            # --- 1. Universal Yaku (Based on Flags) ---
            if self.is_reach and self.is_menzen:
                current_yaku.append(('reach', 1))
            
            if self.is_tsumo and self.is_menzen:
                current_yaku.append(('menzen_tsumo', 1))
            
            # Flush Checks (Honitsu / Chinitsu)
            yaku_flush = self._check_flush_yaku(self.tiles_int)
            current_yaku.extend(yaku_flush)
            
            # --- 2. Structural Yaku ---
            
            # Seven Pairs
            if struct['type'] == 'seven_pairs':
                current_yaku.append(('chitoitsu', 2))
                
                # Tanyao
                if self._check_tanyao(self.tiles_int):
                    current_yaku.append(('tanyao', 1))
                    
                # Honroutou (Seven Pairs form)
                if self._check_honroutou(self.tiles_int):
                    current_yaku.append(('honroutou', 2))
            
            # Standard Form (4 Melds + 1 Pair)
            elif struct['type'] == 'standard':
                melds = struct['melds']
                pair = struct['pair']
                
                # Tanyao
                if self._check_tanyao(self.tiles_int):
                    current_yaku.append(('tanyao', 1))
                    
                # Yakuhai (Dragons & Winds)
                yaku_yakuhai = self._check_yakuhai(melds)
                current_yaku.extend(yaku_yakuhai)
                
                # Pinfu
                if self.is_menzen and self._check_pinfu_structure(struct):
                    current_yaku.append(('pinfu', 1))
                    
                # Toi-Toi (All Triplets)
                if self._check_toitoi(struct):
                    current_yaku.append(('toitoi', 2))
                    
                # San Ankou (Three Concealed Triplets)
                if self._check_sanankou(melds, self.win_tile, self.is_tsumo):
                    current_yaku.append(('sanankou', 2))
                    
                # Sanshoku Doujun
                if self._check_sanshoku(melds):
                    # Menzen=2, Open=1
                    current_yaku.append(('sanshoku', 2 if self.is_menzen else 1))
                    
                # Sanshoku Douko
                if self._check_sanshoku_douko(melds):
                    current_yaku.append(('sanshoku_douko', 2))
                    
                # Itsu (Ikkitsuukan)
                if self._check_itsu(melds):
                    # Menzen=2, Open=1
                    current_yaku.append(('itsu', 2 if self.is_menzen else 1))

                # Ryanpeiko > Ippeiko (Menzen only)
                is_ryanpeiko = False
                if self.is_menzen:
                    if self._check_ryanpeiko(melds):
                        current_yaku.append(('ryanpeiko', 3))
                        is_ryanpeiko = True
                    elif self._check_ippeiko(melds):
                        current_yaku.append(('ippeiko', 1))
                        
                # Chanta / Junchan / Honroutou
                # Honroutou implies ALL elements are Terminal/Honor (Pairs/Triplets).
                # Junchan allows Sequences (123, 789).
                # Chanta allows Honor + Seq.
                
                is_honroutou = self._check_honroutou(self.tiles_int)
                if is_honroutou:
                    current_yaku.append(('honroutou', 2))
                else: 
                    # If not Honroutou, check Junchan/Chanta
                    if self._check_junchan(melds, pair):
                         current_yaku.append(('junchan', 3 if self.is_menzen else 2))
                    elif self._check_chanta(melds, pair):
                         current_yaku.append(('chanta', 2 if self.is_menzen else 1))

                # Shosangen (Little Three Dragons)
                if self._check_shosangen(melds, pair):
                    current_yaku.append(('shosangen', 2))

            # Calculate Total Han
            total_han = sum(h for name, h in current_yaku)
            
            if total_han > best_result['han']:
                best_result = {
                    'yaku': [self.YAKU_NAMES.get(n, n) for n, h in current_yaku],
                    'han': total_han,
                    'fu': 30, # Default placeholder
                    'score_name': self._get_score_name(total_han),
                    'structure': struct
                }
                
        if best_result['han'] == -1:
             return {'yaku': [], 'han': 0, 'fu': 0, 'score_name': '', 'structure': None}
             
        return best_result

    def _check_tanyao(self, tiles):
        # Tanyao: No Terminals (1, 9) or Honors (>= 30)
        terminals = [1, 9, 11, 19, 21, 29]
        for t in tiles:
            if t >= 30 or t in terminals:
                return False
        return True

    def _check_yakuhai(self, melds):
        # Check for Triplets of Dragons or Winds
        founded_yaku = []
        
        # Mapping for generic check
        # White: 41, Green: 43, Red: 45
        # East: 31, South: 33, West: 35, North: 37
        
        wind_map = {'east': 31, 'south': 33, 'west': 35, 'north': 37}
        
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                tile = m_tiles[0]
                if tile == 41: founded_yaku.append(('yakuhai_haku', 1))
                if tile == 43: founded_yaku.append(('yakuhai_hatsu', 1))
                if tile == 45: founded_yaku.append(('yakuhai_chun', 1))
                
                if tile == wind_map.get(self.bakaze):
                    founded_yaku.append(('yakuhai_bakaze', 1))
                if tile == wind_map.get(self.jikaze):
                    founded_yaku.append(('yakuhai_jikaze', 1))
                    
        return founded_yaku

    def _check_pinfu_structure(self, struct):
        # Pinfu: 4 Sequences, Head is NOT Yakuhai
        
        # 1. Check Melds are all sequences
        for m_type, m_tiles in struct['melds']:
            if m_type != 'shuntsu':
                return False
        
        # 2. Check Head is not Yakuhai
        head = struct['pair'][0]
        if head in [41, 43, 45]: # Dragons
            return False
        
        wind_map = {'east': 31, 'south': 33, 'west': 35, 'north': 37}
        bakaze_tile = wind_map.get(self.bakaze)
        jikaze_tile = wind_map.get(self.jikaze)
        
        if head == bakaze_tile or head == jikaze_tile:
            return False
            
        return True

    def _check_toitoi(self, struct):
        # All 4 melds must be Koutsu
        for m_type, m_tiles in struct['melds']:
            if m_type != 'koutsu':
                return False
        return True

    def _check_ippeiko(self, melds):
        # Two identical sequences
        # e.g. [1,2,3] and [1,2,3] (same suit)
        seqs = []
        for m_type, m_tiles in melds:
            if m_type == 'shuntsu':
                # m_tiles is tuple/list of ints, e.g. [1,2,3]
                seqs.append(tuple(m_tiles))
        
        # Check for duplicates
        seen = set()
        for s in seqs:
            if s in seen:
                return True
            seen.add(s)
        return False

    def _check_ryanpeiko(self, melds):
        # Two SETS of identical sequences
        # e.g. [1,2,3], [1,2,3], [5,6,7], [5,6,7]
        seqs = []
        for m_type, m_tiles in melds:
            if m_type == 'shuntsu':
                seqs.append(tuple(m_tiles))
        
        if len(seqs) < 4:
            return False
        
        # Count frequency of each sequence
        counts = Counter(seqs)
        pairs_found = 0
        for s, c in counts.items():
            if c >= 2:
                pairs_found += (c // 2)
        
        return pairs_found >= 2

    def _check_sanshoku(self, melds):
        # Same sequence numbers in Man (0-9), Pin (10-19), Sou (20-29)
        # Sequence starts: 
        # Man: 1..7 (represented as 1..7)
        # Pin: 11..17
        # Sou: 21..27
        
        # 1. Gather all sequence start numbers
        seq_starts = []
        for m_type, m_tiles in melds:
            if m_type == 'shuntsu':
                seq_starts.append(m_tiles[0])
        
        # 2. Check for x, x+10, x+20
        # Need to find if any 'base' (1-7) exists in all 3 offsets
        # Bases are < 10.
        
        bases_m = [x for x in seq_starts if 1 <= x <= 7]
        bases_p = [x-10 for x in seq_starts if 11 <= x <= 17]
        bases_s = [x-20 for x in seq_starts if 21 <= x <= 27]
        
        # Find common in all 3
        # Note: A hand could theoretically have multiple sanshoku? No, only one set of 3.
        for b in bases_m:
            if b in bases_p and b in bases_s:
                return True
        return False

    def _check_sanshoku_douko(self, melds):
        # Three Colour Triplets
        triplet_starts = []
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                triplet_starts.append(m_tiles[0])
                
        bases_m = [x for x in triplet_starts if 1 <= x <= 9]
        bases_p = [x-10 for x in triplet_starts if 11 <= x <= 19]
        bases_s = [x-20 for x in triplet_starts if 21 <= x <= 29]
        
        for b in bases_m:
            if b in bases_p and b in bases_s:
                return True
        return False

    def _check_itsu(self, melds):
        # 123, 456, 789 in SAME suit
        # Check per suit
        
        # Gather sequence starts
        seq_starts = []
        for m_type, m_tiles in melds:
            if m_type == 'shuntsu':
                seq_starts.append(m_tiles[0])
                
        # Check Manzu (Starts 1, 4, 7)
        if 1 in seq_starts and 4 in seq_starts and 7 in seq_starts: return True
        # Check Pinzu (Starts 11, 14, 17)
        if 11 in seq_starts and 14 in seq_starts and 17 in seq_starts: return True
        # Check Souzu (Starts 21, 24, 27)
        if 21 in seq_starts and 24 in seq_starts and 27 in seq_starts: return True
        
        return False
        
    def _check_honroutou(self, tiles):
        # All tiles must be Terminals or Honors
        # 1, 9, 11, 19, 21, 29, >=30
        valid_terminals = [1, 9, 11, 19, 21, 29]
        for t in tiles:
            if t < 30 and t not in valid_terminals:
                return False
        return True

    def _check_chanta(self, melds, pair):
        # All melds and pair must CONTAIN a Terminal or Honor
        # Melds:
        #  Koutsu (Triplet): Must be triplet of Term/Hon.
        #  Shuntsu (Seq): Must contain Term/Hon (1,2,3 or 7,8,9).
        
        # Check Pair
        pair_tile = pair[0]
        if not self._is_terminal_or_honor(pair_tile):
            return False
            
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                if not self._is_terminal_or_honor(m_tiles[0]):
                    return False
            elif m_type == 'shuntsu':
                # Check if it contains 1,9 or honors (shuntsu won't have honors generally)
                has_term_or_honor = False
                for t in m_tiles:
                    if self._is_terminal_or_honor(t):
                        has_term_or_honor = True
                        break
                if not has_term_or_honor:
                    return False
        return True

    def _check_junchan(self, melds, pair):
        # All melds and pair must CONTAIN a Terminal (NO Honors)
        
        # Check Pair
        pair_tile = pair[0]
        if not self._is_terminal(pair_tile):
            return False
            
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                if not self._is_terminal(m_tiles[0]):
                    return False
            elif m_type == 'shuntsu':
                has_terminal = False
                for t in m_tiles:
                    if self._is_terminal(t):
                        has_terminal = True
                        break
                if not has_terminal:
                    return False
            
            # Additional check: No Honors allowed anywhere in Junchan
            for t in m_tiles:
                if t >= 30: return False
                
        return True

    def _check_shosangen(self, melds, pair):
        # 2 Dragon Triplets + 1 Dragon Pair
        dragons = [41, 43, 45]
        
        # Check Pair is Dragon
        if pair[0] not in dragons:
            return False
            
        # Check for 2 Dragon Triplets
        dragon_triplets = 0
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                if m_tiles[0] in dragons:
                    dragon_triplets += 1
        
        return dragon_triplets >= 2

    def _check_sanankou(self, melds, win_tile_str, is_tsumo):
        # 3 Concealed Triplets.
        # Note: If Ron on a triplet, that triplet is Open (Minkou).
        # win_tile needs to be int for comparison
        win_tile = _parse_hand([win_tile_str])[0]
        
        ankou_count = 0
        for m_type, m_tiles in melds:
            if m_type == 'koutsu':
                # Is it Ankou?
                # If Tsumo: All menzen triplets are Ankou.
                # If Ron: The triplet matching win_tile is Minkou. Others Ankou.
                
                # We assume self.is_menzen is True for now (since we don't track open status yet).
                # If not menzen, we can't easily tell which are open unless we track it properly.
                # But task requirement is usually Menzen logic for simplicity or "Is Menzen" flag.
                
                tile = m_tiles[0]
                is_ankou = True # Assume closed if Menzen
                
                if not is_tsumo:
                    if tile == win_tile:
                        is_ankou = False
                
                if is_ankou:
                    ankou_count += 1
                    
        return ankou_count >= 3

    def _is_terminal(self, tile):
        return tile in [1, 9, 11, 19, 21, 29]

    def _is_terminal_or_honor(self, tile):
        return tile >= 30 or tile in [1, 9, 11, 19, 21, 29]

    def _check_flush_yaku(self, tiles):
        # Honitsu (Half Flush) and Chinitsu (Full Flush)
        # Man: 1-9, Pin: 11-19, Sou: 21-29, Honor: >=30
        
        has_man = False
        has_pin = False
        has_sou = False
        has_honor = False
        
        for t in tiles:
            if 1 <= t <= 9: has_man = True
            elif 11 <= t <= 19: has_pin = True
            elif 21 <= t <= 29: has_sou = True
            elif t >= 30: has_honor = True
            
        suits_count = sum([has_man, has_pin, has_sou])
        
        result = []
        if suits_count == 1:
            if not has_honor:
                # Chinitsu (One suit, no honors)
                # Menzen=6, Open=5
                result.append(('chinitsu', 6 if self.is_menzen else 5))
            else:
                # Honitsu (One suit + honors)
                # Menzen=3, Open=2
                result.append(('honitsu', 3 if self.is_menzen else 2))
                
        return result

    def _get_score_name(self, han):
        if han >= 13: return "Yakuman (Critical Failure)"
        if han >= 11: return "Sanbaiman (Severe Overload)"
        if han >= 8:  return "Baiman (High Latency)"
        if han >= 6:  return "Haneman (Packet Loss)"
        if han >= 5:  return "Mangan (Congestion)"
        return "Normal Traffic"
