
import unittest
from reach_conn_checker.network_rules import validate_packet_structure

class TestNetworkRules(unittest.TestCase):
    def test_agari_sequence_only(self):
        # 123m, 456p, 789s, 123s, 11m (Pair)
        hand = ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s", "1s", "2s", "3s", "1m", "1m"]
        self.assertTrue(validate_packet_structure(hand))

    def test_agari_triplet_only(self):
        # 111m, 222p, 333s, 444s, 55m (Pair)
        hand = ["1m", "1m", "1m", "2p", "2p", "2p", "3s", "3s", "3s", "4s", "4s", "4s", "5m", "5m"]
        self.assertTrue(validate_packet_structure(hand))

    def test_agari_mixed(self):
        # 123m, 555p, 789s, east, east, east, white, white (Pair)
        hand = ["1m", "2m", "3m", "5p", "5p", "5p", "7s", "8s", "9s", "east", "east", "east", "white", "white"]
        self.assertTrue(validate_packet_structure(hand))

    def test_not_agari(self):
        # Random tiles
        hand = ["1m", "2m", "5m", "8p", "9p", "1s", "2s", "5s", "8s", "east", "south", "west", "north", "white"]
        self.assertFalse(validate_packet_structure(hand))
    
    def test_chitoitsu(self):
        # 7 pairs
        hand = ["1m", "1m", "2m", "2m", "1p", "1p", "9s", "9s", "east", "east", "south", "south", "white", "white"]
        self.assertTrue(validate_packet_structure(hand))

    def test_tenpai_check(self):
        from reach_conn_checker.network_rules import check_protocol_readiness
        
        # Tenpai hand: 123m 456p 789s 23s (Wait 1s/4s) 11z (Head)
        # Total 13 tiles
        hand = ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s", "2s", "3s", "east", "east"]
        # Should be ready (waiting for 1s or 4s)
        self.assertTrue(check_protocol_readiness(hand))

    def test_not_tenpai(self):
        from reach_conn_checker.network_rules import check_protocol_readiness
        
        # Random tiles, not ready
        hand = ["1m", "5m", "9m", "1p", "5p", "9p", "1s", "5s", "9s", "east", "south", "white", "red"]
        self.assertFalse(check_protocol_readiness(hand))

    def test_reachability_14_tiles(self):
        from reach_conn_checker.network_rules import check_discard_for_tenpai
        
        # Hand: 123m 456p 789s 23s (Tenpai part) + 9m (Extra)
        # Total 14 tiles
        hand = ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s", "2s", "3s", "9m", "east", "east"]
        # Discarding 9m should make it Tenpai (waiting for 1s/4s)
        
        candidates = check_discard_for_tenpai(hand)
        self.assertIn("9m", candidates)


if __name__ == '__main__':
    unittest.main()
