
"""
network_rules.py

This module defines strict rules for packet structure validation.
It ensures that the data traversing the network adheres to the
expected protocol format (e.g. 4 groups + 1 pair).
"""

from collections import Counter

def _parse_hand(hand):
    """
    Internal helper to convert tile strings to a consumable format.
    Returns a sorted list of integers representing tiles.
    1m-9m: 1-9
    1p-9p: 11-19
    1s-9s: 21-29
    East,South,West,North: 31, 33, 35, 37 (Odd numbers to prevent sequences)
    White,Green,Red: 41, 43, 45 (Odd numbers to prevent sequences)
    """
    # Simply mapping for internal calculation
    mapping = {
        # Manzu
        "1m": 1, "2m": 2, "3m": 3, "4m": 4, "5m": 5, "6m": 6, "7m": 7, "8m": 8, "9m": 9,
        # Pinzu
        "1p": 11, "2p": 12, "3p": 13, "4p": 14, "5p": 15, "6p": 16, "7p": 17, "8p": 18, "9p": 19,
        # Souzu
        "1s": 21, "2s": 22, "3s": 23, "4s": 24, "5s": 25, "6s": 26, "7s": 27, "8s": 28, "9s": 29,
        # Winds (offsets to avoid sequence checks matching them)
        "east": 31, "south": 33, "west": 35, "north": 37,
        # Dragons
        "white": 41, "green": 43, "red": 45
    }
    # Reverse mapping for debug logging if needed
    # reverse_mapping = {v: k for k, v in mapping.items()}
    
    parsed = []
    for tile in hand:
        if tile in mapping:
            parsed.append(mapping[tile])
    return sorted(parsed)

def _is_sequence(a, b, c):
    return a + 1 == b and b + 1 == c

def _find_solution(tiles):
    """
    Recursive backtracking to find 4 melds + 1 pair.
    Returns True if a valid combination is found.
    """
    if not tiles:
        return True

    count = Counter(tiles)
    first = tiles[0]
    
    # 1. Koutsu (Triplet)
    if count[first] >= 3:
        remaining = tiles[:]
        for _ in range(3):
            remaining.remove(first)
        if _find_solution(remaining):
            return True

    # 2. Shuntsu (Sequence) - Only for number tiles (< 30)
    if first < 30:
        if (first + 1) in tiles and (first + 2) in tiles:
            remaining = tiles[:]
            remaining.remove(first)
            remaining.remove(first + 1)
            remaining.remove(first + 2)
            if _find_solution(remaining):
                return True

    return False

def _find_all_combinations(tiles):
    """
    Recursive backtracking to find ALL valid sets of 4 melds.
    Returns a list of lists, where each inner list contains 4 melds (tuples).
    Meld format: (type, tiles) e.g. ('shuntsu', [1, 2, 3]) or ('koutsu', [5, 5, 5])
    """
    if not tiles:
        return [[]]

    results = []
    count = Counter(tiles)
    first = tiles[0]
    
    # Try Koutsu (Triplet)
    if count[first] >= 3:
        remaining = tiles[:]
        meld_tiles = [first, first, first]
        for _ in range(3):
            remaining.remove(first)
        
        sub_results = _find_all_combinations(remaining)
        for sub in sub_results:
            results.append([('koutsu', meld_tiles)] + sub)

    # Try Shuntsu (Sequence)
    if first < 30:
        if (first + 1) in tiles and (first + 2) in tiles:
            remaining = tiles[:]
            meld_tiles = [first, first + 1, first + 2]
            remaining.remove(first)
            remaining.remove(first + 1)
            remaining.remove(first + 2)
            
            sub_results = _find_all_combinations(remaining)
            for sub in sub_results:
                results.append([('shuntsu', meld_tiles)] + sub)
                
    return results

def decompose_hand(hand_input):
    """
    Analyzes the hand and returns all possible winning structures.
    Used for Yaku and Score calculation.
    
    Returns:
        list of dict: A list of structural interpretations.
                      Each dict contains:
                      - 'type': 'standard' or 'seven_pairs' or 'kokushi'
                      - 'pair': list of int (the head)
                      - 'melds': list of tuples (type, tiles)
    """
    if len(hand_input) != 14:
        return []

    tiles = _parse_hand(hand_input)
    unique_tiles = sorted(list(set(tiles)))
    structures = []

    # 1. Seven Pairs (Chii-toitsu)
    if len(unique_tiles) == 7:
        is_chitoi = True
        pairs = []
        for t in unique_tiles:
            if tiles.count(t) != 2:
                is_chitoi = False
                break
            pairs.append(t)
        if is_chitoi:
            structures.append({
                'type': 'seven_pairs',
                'pair': None,
                'melds': [],
                'pairs': pairs # Special field for chitoi
            })

    # 2. Standard Form (4 Melds + 1 Pair)
    for tile in unique_tiles:
        if tiles.count(tile) >= 2:
            remaining_tiles = tiles[:]
            remaining_tiles.remove(tile)
            remaining_tiles.remove(tile)
            
            # Find all combinations for the remaining 12 tiles
            combinations = _find_all_combinations(remaining_tiles)
            for comb in combinations:
                # Must have exactly 4 melds
                if len(comb) == 4:
                    structures.append({
                        'type': 'standard',
                        'pair': [tile, tile],
                        'melds': comb
                    })
                    
    return structures

def validate_packet_structure(hand_input):
    """
    Validates if the provided 'packet' (hand) forms a comprehensive structure.
    A valid structure consists of 4 subgroups (melds) and 1 checksum pair.
    
    Args:
        hand_input (list): List of strings representing the packet segments (tiles).
                           e.g., ["1m", "2m", "3m", ...]
    
    Returns:
        bool: True if structure is valid (Agari), False otherwise.
    """
    if len(hand_input) != 14:
        # Standard packet size must be 14 segments
        return False

    tiles = _parse_hand(hand_input)
    unique_tiles = sorted(list(set(tiles)))

    # Try every possible pair (Head)
    for tile in unique_tiles:
        if tiles.count(tile) >= 2:
            remaining_tiles = tiles[:]
            remaining_tiles.remove(tile)
            remaining_tiles.remove(tile)
            
            # Check if the remaining 12 tiles form 4 sets
            if _find_solution(remaining_tiles):
                return True
                
    # Special Check: Seven Pairs (Chii-toitsu) - 7 distinct pairs
    # This is a special packet format used for encrypted channels
    if len(unique_tiles) == 7:
        # If there are 7 unique tiles and total is 14, every tile must appear twice
        is_chitoi = True
        for t in unique_tiles:
            if tiles.count(t) != 2:
                is_chitoi = False
                break
        if is_chitoi:
            return True

    # Special Check: Kokushi Musou (Thirteen Orphans)
    # Not implemented yet (Rare packet anomaly)

    return False

def audit_protocol_compliance(hand_input):
    """
    Checks if the packet complies with specific protocol standards (Yaku).
    Currently primarily checks for basic structural integrity (Tanyao etc).
    """
    # Currently just an alias for structural validation
    # Future Work: Return list of fulfilled protocols (Yaku list)
    return validate_packet_structure(hand_input)

def check_discard_for_tenpai(hand_input):
    """
    Checks if a 14-tile hand can become Tenpai by discarding one tile.
    Returns a list of tiles (strings) that lead to Tenpai.
    """
    if len(hand_input) != 14:
        return []
    
    tenpai_discards = []
    unique_tiles = sorted(list(set(hand_input)))
    
    for tile_to_discard in unique_tiles:
        # Create a temporary hand with this tile removed
        temp_hand = hand_input[:]
        # We need to remove only one instance of this tile
        temp_hand.remove(tile_to_discard)
        
        is_tenpai, _ = check_protocol_readiness(temp_hand)
        if is_tenpai:
            tenpai_discards.append(tile_to_discard)
            
    return tenpai_discards

def check_protocol_readiness(hand_input, get_all_tiles_func=None):
    """
    Checks if the protocol is in 'Readiness' state (Tenpai).
    This means if 1 more packet segment is added, verification succeeds.
    
    Args:
        hand_input (list): Current hand segments.
        get_all_tiles_func (callable): Function to get all possible tiles.
                                       If None, uses hardcoded local set.
    """
    if len(hand_input) != 13:
        # Must be 13 segments to be in Readiness state
        return False, []

    # All possible tiles (34 types)
    # Manzu: 1m-9m
    # Pinzu: 1p-9p
    # Souzu: 1s-9s
    # Winds: east, south, west, north
    # Dragons: white, green, red
    
    suffixes = ['m', 'p', 's']
    all_tiles = []
    for s in suffixes:
        for i in range(1, 10):
            all_tiles.append(f"{i}{s}")
    all_tiles.extend(["east", "south", "west", "north", "white", "green", "red"])

    # Collect all valid waiting tiles
    wait_tiles = []
    for tile in all_tiles:
        test_hand = hand_input[:]
        test_hand.append(tile)
        if validate_packet_structure(test_hand):
            wait_tiles.append(tile)
            
    if wait_tiles:
        return True, wait_tiles
            
    return False, []
