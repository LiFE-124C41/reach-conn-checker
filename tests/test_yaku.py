
import unittest
from reach_conn_checker.yaku_rules import YakuChecker

class TestYakuChecker(unittest.TestCase):
    
    def test_tanyao_pinfu(self):
        # Tanyao + Pinfu Hand
        # 234m, 456p, 678s, 22s (Pair), 345m
        hand = ["2m", "3m", "4m", "4p", "5p", "6p", "6s", "7s", "8s", "3m", "4m", "5m", "2s", "2s"]
        checker = YakuChecker(hand, win_tile="2m", is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Tanyao (Simple Routing)", yaku_names)
        self.assertIn("Pinfu (Flat Network)", yaku_names)
        self.assertEqual(result['han'], 2)

    def test_yakuhai_white(self):
        # White Dragon Triplet + misc
        # White, White, White, 123m, 456p, 789s, 99p
        hand = ["white", "white", "white", "1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="white")
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Yakuhai: White (Null Packet)", yaku_names)
        # Should not be Tanyao because of terminals (1m, 9s) and Honors
        self.assertNotIn("Tanyao (Simple Routing)", yaku_names)

    def test_reach(self):
        # Reach declaration
        hand = ["2m", "3m", "4m", "5m", "6m", "7m", "2p", "2p", "2p", "5s", "5s", "5s", "8s", "8s"]
        checker = YakuChecker(hand, win_tile="8s", is_reach=True, is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Reach (Continuous Ping)", yaku_names)

    def test_running_flush(self):
        # Chinitsu (Full Flush) + Ippeiko + Pinfu
        # 112233m, 456m, 789m, 99m
        hand = ["1m", "1m", "2m", "2m", "3m", "3m", "4m", "5m", "6m", "7m", "8m", "9m", "9m", "9m"]
        checker = YakuChecker(hand, win_tile="9m", is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Chinitsu (Dedicated Line)", yaku_names)
        self.assertIn("Ippeiko (Redundant Mirroring)", yaku_names)
        # Pinfu check might fail if pair is not generic or wait is weird, but structure allows it.
        # But wait... 99m is triplet or pair? 
        # 11,22,33 -> Ippeiko. 456, 789 -> Seqs. 99 -> Pair.
        # So structure: [123, 123, 456, 789] + 99.
        # Pinfu ok.
        self.assertIn("Pinfu (Flat Network)", yaku_names)
        # Also Itsu (123, 456, 789) is present!
        # [123, 123, 456, 789] matches 123, 456, 789.
        self.assertIn("Itsu (Full Spectrum Scan)", yaku_names)
        
        # Total Han: Chinitsu(6) + Itsu(2) + Ippeiko(1) + Pinfu(1) = 10 (Baiman -> Sanbaiman near)
        self.assertEqual(result['han'], 10)

    def test_sanshoku(self):
        # Sanshoku Doujun (123m, 123p, 123s)
        # 123m, 123p, 123s, east, east, east, 99p
        hand = ["1m", "2m", "3m", "1p", "2p", "3p", "1s", "2s", "3s", "east", "east", "east", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="1m", is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Sanshoku (Cross-Subnet Sync)", yaku_names)

    def test_itsu(self):
        # Itsu (1-9 same suit)
        # 123s, 456s, 789s, 11m, 99p
        # Need 4 melds + pair. 
        # 123s, 456s, 789s, 111m (Triplet), 99p (Pair)
        hand = ["1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "1m", "1m", "1m", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="1s", is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Itsu (Full Spectrum Scan)", yaku_names)

    def test_honitsu(self):
        # Honitsu (Mixed Flush)
        # 123m, 456m, east, east, east, west, west
        # Wait.. 123m, 456m, east3, west2 ? 
        # 123, 456, [east,east,east], [west,west,west], pair?
        # Let's do: 123m, 456m, 789m, east, east, east, west, west
        hand = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m", "east", "east", "east", "west", "west"]
        checker = YakuChecker(hand, win_tile="west", is_menzen=True)
        result = checker.execute()
        
        yaku_names = [y for y in result['yaku']]
        self.assertIn("Honitsu (Port Isolation)", yaku_names)
        # Also Itsu
        self.assertIn("Itsu (Full Spectrum Scan)", yaku_names)

    def test_ryanpeiko(self):
        # Ryanpeiko (112233m 556677m 99p)
        hand = ["1m", "1m", "2m", "2m", "3m", "3m", "5m", "5m", "6m", "6m", "7m", "7m", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="1m", is_menzen=True)
        result = checker.execute()
        self.assertIn("Ryanpeiko (Full Mirror Redundancy)", result['yaku'])
        # Also Chinitsu if 9p was 9m, but here it's mixed.
        # It's at least Mangan (Ryanpeiko 3 + MenzenTsumo 1 + etc?)
        # Let's verify Han count is >= 3.

    def test_junchan_and_sanshoku(self):
        # Junchan (123, 123, 123, 123) + Sanshoku
        # 123m, 123p, 123s, 999m, 99p(Pair) -> Wait, 99p is pair. 999m is triplet terminal.
        # Melds: 123m (Term), 123p (Term), 123s (Term), 999m (Term). Pair: 99p (Term).
        # Should be Junchan (3) + Sanshoku (2) = 5 (Mangan). (If Menzen).
        hand = ["1m", "2m", "3m", "1p", "2p", "3p", "1s", "2s", "3s", "9m", "9m", "9m", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="1m", is_menzen=True)
        result = checker.execute()
        self.assertIn("Junchan (Strict Edge Routing)", result['yaku'])
        self.assertIn("Sanshoku (Cross-Subnet Sync)", result['yaku'])
        self.assertEqual(result['han'], 5) # Junchan(3)+Sanshoku(2)
        # Wait, Pinfu? Head is 9p (non-yakuhai). Melds are 123, 123, 123... and 999m(Triplet). 
        # Triplet ruins Pinfu.
        # So Han should be 3+2 = 5?
        # Ah, we check "Is Tsumo" or "Is Ron"? result['yaku'] doesn't say.
        # Default is_menzen=True, is_tsumo=False (Ron).
        # Result: Junchan(3) + Sanshoku(2) = 5. Maybe Tsumo(1) if is_tsumo=True.
        # Wait, SanShokuDouJun.
        # 123m, 123p, 123s are seqs. 999m is Triplet.
        # If Menzen Ron: 5 Han.

    def test_honroutou_toitoi(self):
        # Honroutou is almost always ToiToi or ChiToi.
        # 111m, 999m, 111p, 999p, 11s
        hand = ["1m", "1m", "1m", "9m", "9m", "9m", "1p", "1p", "1p", "9p", "9p", "9p", "1s", "1s"]
        checker = YakuChecker(hand, win_tile="1s", is_menzen=True)
        result = checker.execute()
        self.assertIn("Honroutou (Backbone Nodes Only)", result['yaku'])
        self.assertIn("Toi-Toi (All Triplets)", result['yaku'])
        self.assertIn("San Ankou (Three Concealed Triplets)", result['yaku']) 
        # Actually it's Su Ankou (Four Concealed) if Tsumo, but here Ron. 
        # So San Ankou.
        
    def test_shosangen(self):
        # White, White, Green, Green, Green, Red, Red, Red, 123m
        # Pair: White. Triplets: Green, Red.
        hand = ["white", "white", "green", "green", "green", "red", "red", "red", "1m", "2m", "3m", "9p", "9p", "9p"]
        checker = YakuChecker(hand, win_tile="white")
        result = checker.execute()
        self.assertIn("Shosangen (Sub-Controller Cluster)", result['yaku'])
        self.assertIn("Yakuhai: Green (Green OF)", result['yaku'])
        self.assertIn("Yakuhai: Red (Red Hat)", result['yaku'])
        # Also White is pair, no Yakuhai for pair (unless... no).
        
    def test_sanshoku_douko(self):
        # 222m, 222p, 222s, ...
        hand = ["2m", "2m", "2m", "2p", "2p", "2p", "2s", "2s", "2s", "5m", "6m", "7m", "east", "east"]
        checker = YakuChecker(hand, win_tile="2m")
        result = checker.execute()
        self.assertIn("Sanshoku Douko (Cross-Platform Triplets)", result['yaku'])

if __name__ == '__main__':
    unittest.main()
