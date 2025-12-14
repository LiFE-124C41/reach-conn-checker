"""
score_counter.py

This module calculates the Score (Traffic Impact Analysis) based on the Han and Fu.
It provides the total points and the breakdown of payment (Ko/Oya).
"""

import math
from .network_rules import _parse_hand

class ScoreCalculator:
    def __init__(self):
        # Point Tables
        # Key: Han, Value: Base Score for limit hands
        self.LIMIT_SCORES = {
            5: 2000, # Mangan
            6: 3000, # Haneman
            7: 3000,
            8: 4000, # Baiman
            9: 4000,
            10: 4000,
            11: 6000, # Sanbaiman
            12: 6000,
            13: 8000  # Yakuman
        }

    def calculate_fu(self, structure, win_tile_str, is_tsumo, is_menzen, 
                     bakaze_str='east', jikaze_str='east', yaku_names=None):
        """
        Calculates the Fu (Complexity Overhead).
        """
        if not structure:
            return 0
            
        # Seven Pairs is fixed 25 Fu
        if structure['type'] == 'seven_pairs':
            return 25
            
        # Pinfu Tsumo = 20, Pinfu Ron = 30
        is_pinfu = 'Pinfu (Flat Network)' in (yaku_names or [])
        if is_pinfu:
            return 20 if is_tsumo else 30

        # Base Fu
        fu = 20
        
        # Menzen Ron bonus
        if is_menzen and not is_tsumo:
            fu += 10
            
        # Tsumo bonus (only if not Pinfu, which is handled above)
        if is_tsumo:
            fu += 2
            
        # Parse context tiles
        try:
            win_tile = _parse_hand([win_tile_str])[0]
        except:
            win_tile = 0 # Should not happen
            
        # Winds mapping
        wind_map = {'east': 31, 'south': 33, 'west': 35, 'north': 37}
        bakaze = wind_map.get(bakaze_str, 0)
        jikaze = wind_map.get(jikaze_str, 0)

        # 1. Melds
        # Simple/Open check requires knowing if meld was open.
        # Current implementation assumes all CLOSED for simplicity (Stealth Mode default).
        # TODO: Pass 'open_melds' list to support open hands properly.
        # For now, if is_menzen=True, all are Ankou (Closed).
        # If is_menzen=False, we treat ALL triplets as Minkou (Open) for conservative estimate?
        # A proper fix requires structure to track open status per meld.
        
        for m_type, m_tiles in structure['melds']:
            if m_type == 'koutsu':
                tile = m_tiles[0]
                is_terminal = (tile in [1, 9, 11, 19, 21, 29] or tile >= 30)
                
                base_val = 2 # Minkou Middle
                if is_terminal: base_val *= 2 # Minkou Terminal -> 4
                
                # If Menzen, Ankou (x2)
                # If Ron and this meld was the winning tile... it counts as Minkou? 
                # (Only if Shanpon wait and we won by Ron on this triplet -> Minkou)
                # We simply check: is_menzen -> Ankou.
                # Exception: winning tile forms this triplet by Ron -> treated as Minkou.
                
                is_ankou = is_menzen # Default assumption
                
                if not is_tsumo and win_tile == tile:
                    # Ron on this triplet -> Minkou
                    is_ankou = False
                
                if is_ankou:
                    base_val *= 2
                    
                fu += base_val
                
            elif m_type == 'kan':
                # Kan not supported yet
                pass

        # 2. Head (Pair)
        head = structure['pair'][0]
        if head >= 41: # Dragons
            fu += 2
        if head == bakaze: # Round Wind
            fu += 2
        if head == jikaze: # Seat Wind
            fu += 2

        # 3. Wait
        # Ryanmen/Shanpon = 0
        # Kanchan/Penchan/Tanki = 2
        
        add_wait_fu = 0
        
        # Tanki check
        if win_tile == head:
            add_wait_fu = 2
        
        # Kanchan/Penchan check
        # Only check sequences
        # Only apply if we haven't already applied Tanki (Wait is unique)
        if add_wait_fu == 0:
            for m_type, m_tiles in structure['melds']:
                if m_type == 'shuntsu':
                    # m_tiles is sorted [a, a+1, a+2]
                    if win_tile in m_tiles:
                        # Check Kanchan (Middle)
                        if win_tile == m_tiles[1]:
                            add_wait_fu = 2
                            break
                        # Check Penchan (Edge 3 or 7)
                        # 12[3] case
                        if m_tiles[0] == 1 and win_tile == 3: # 1,2,3 win 3
                             add_wait_fu = 2
                             break
                        # [7]89 case
                        if m_tiles[2] == 9 and win_tile == 7: # 7,8,9 win 7
                             add_wait_fu = 2
                             break
                             
        fu += add_wait_fu
        
        # Round up to nearest 10
        if fu == 25: return 25 # Chi-toitsu exception
        return math.ceil(fu / 10) * 10

    def calculate_score(self, han, fu, is_oya=False, is_tsumo=False):
        """
        Calculates the final score points.
        Returns dict with keys: 'total', 'payments' (list/str)
        """
        if han == 0:
            return {'total': 0, 'payments': '0'}
            
        base_points = 0
        
        # 1. Determine Basic Points (Base)
        if han >= 5 or (han >= 4 and fu >= 40) or (han >= 3 and fu >= 70):
             # Limit Hand (Mangan+)
             if han >= 13: base_points = 8000
             elif han >= 11: base_points = 6000
             elif han >= 8: base_points = 4000
             elif han >= 6: base_points = 3000
             else: base_points = 2000
        else:
             # Normal Hand
             base_points = fu * (2 ** (2 + han))
             # Cap at Mangan
             if base_points > 2000:
                 base_points = 2000

        # 2. Calculate Payments
        # Rounded up to nearest 100
        def round100(val):
            return math.ceil(val / 100) * 100
            
        info = {}
        
        if is_tsumo:
            if is_oya:
                # Oya Tsumo: All pay 1/3 of (Base * 6) -> Base * 2
                pay = round100(base_points * 2)
                info['total'] = pay * 3
                info['payments'] = f"ALL: {pay}"
            else:
                # Ko Tsumo: Oya pays 1/2 (Base * 2), Ko pays 1/4 (Base * 1)
                pay_oya = round100(base_points * 2)
                pay_ko = round100(base_points)
                info['total'] = pay_oya + (pay_ko * 2)
                info['payments'] = f"Oya: {pay_oya}, Ko: {pay_ko}"
        else:
            # Ron
            multiplier = 6 if is_oya else 4
            pay = round100(base_points * multiplier)
            info['total'] = pay
            info['payments'] = f"Target: {pay}"
            
        return info
