
import unittest
from reach_conn_checker.score_counter import ScoreCalculator
from reach_conn_checker.network_rules import decompose_hand

class TestScoreCalculator(unittest.TestCase):
    
    def setUp(self):
        self.calc = ScoreCalculator()
        
    def test_pinfu_tsumo(self):
        # 20 Fu, 2 Han (Pinfu + Menzen Tsumo)
        # Oya: 700 all? No, Ko: 400, Oya: 700.
        # Calc logic: 20 * 2^(2+2) = 320.
        # Ko Payment: ceil(320/100)*100 = 400.
        # Oya Payment: ceil(640/100)*100 = 700.
        
        # Pinfu hand structure (mock or real)
        hand = ["2m", "3m", "4m", "5p", "6p", "7p", "2s", "3s", "4s", "5s", "6s", "7s", "9m", "9m"]
        # Decompose
        structures = decompose_hand(hand)
        # Assume first structure matches Pinfu
        struct = structures[0]
        
        fu = self.calc.calculate_fu(struct, win_tile_str="4m", is_tsumo=True, is_menzen=True, yaku_names=['Pinfu (Flat Network)'])
        self.assertEqual(fu, 20)
        
        score = self.calc.calculate_score(han=2, fu=fu, is_oya=False, is_tsumo=True)
        self.assertEqual(score['total'], 1500)
        self.assertEqual(score['payments'], "Oya: 700, Ko: 400")

    def test_tanyao_ron_30fu(self):
        # Tanyao only (1 Han), Ron
        # 30 Fu (Base 20 + Ron 10)
        # 30 * 2^(2+1) = 240.
        # Ko Ron: 240 * 4 = 960 -> 1000.
        
        hand = ["2m", "3m", "4m", "4p", "5p", "6p", "6s", "7s", "8s", "3m", "4m", "5m", "2s", "2s"]
        structures = decompose_hand(hand)
        struct = structures[0]
        
        fu = self.calc.calculate_fu(struct, win_tile_str="2m", is_tsumo=False, is_menzen=True, yaku_names=['Tanyao'])
        self.assertEqual(fu, 30)
        
        score = self.calc.calculate_score(han=1, fu=fu, is_oya=False, is_tsumo=False)
        self.assertEqual(score['total'], 1000)

    def test_chi_toitsu(self):
        # Chi-toitsu (2 Han, 25 Fu)
        # Ron: 25 * 2^(2+2) = 400.
        # Ko Ron: 400 * 4 = 1600.
        
        # Hand structure for Chi-toitsu
        # Just mock the structure type since decompose_hand needs a real chitoi hand
        struct = {'type': 'seven_pairs', 'pair': None, 'melds': []}
        
        fu = self.calc.calculate_fu(struct, win_tile_str="1m", is_tsumo=False, is_menzen=True)
        self.assertEqual(fu, 25)
        
        score = self.calc.calculate_score(han=2, fu=fu, is_oya=False, is_tsumo=False)
        self.assertEqual(score['total'], 1600)

if __name__ == '__main__':
    unittest.main()
