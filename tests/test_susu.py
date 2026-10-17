import unittest
from decimal import Decimal

from main import SusuGroup, WeekNotReadyError


class SusuGroupTests(unittest.TestCase):
    def setUp(self):
        self.group = SusuGroup("50.00")
        for name in ("Ama", "Kofi", "Esi"):
            self.group.add_member(name)

    def test_partial_payment_is_tracked_and_week_cannot_close(self):
        self.group.record_contribution("Ama", 1, "50.00")
        self.group.record_contribution("Kofi", 1, "50.00")
        remaining = self.group.record_contribution("Esi", 1, "30.00")

        self.assertEqual(remaining, Decimal("20.00"))
        with self.assertRaises(WeekNotReadyError) as error:
            self.group.close_week()
        self.assertEqual(error.exception.dues, [("Esi", Decimal("20.00"))])
        self.assertEqual(self.group.payout_history, [])
        self.assertIn("Esi: paid GHS 30.00; owes GHS 20.00", self.group.report())

    def test_full_payments_close_week_and_pay_join_order(self):
        for name in self.group.members:
            self.group.record_contribution(name, 1, "50.00")

        payout = self.group.close_week()

        self.assertEqual((payout.recipient, payout.amount), ("Ama", Decimal("150.00")))
        self.assertEqual(self.group.current_week, 2)
        self.assertIn("Next payout recipient: Kofi", self.group.report())

    def test_partial_payments_can_be_completed_before_close(self):
        self.group.record_contribution("Esi", 1, "30.00")
        self.group.record_contribution("Esi", 1, "20.00")
        for name in ("Ama", "Kofi"):
            self.group.record_contribution(name, 1, "50.00")

        self.assertEqual(self.group.close_week().recipient, "Ama")

    def test_rejects_unknown_member_and_case_insensitive_duplicate(self):
        with self.assertRaisesRegex(ValueError, "Unknown member"):
            self.group.record_contribution("Nana", 1, "10.00")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.group.add_member("ama")

    def test_rejects_zero_negative_and_fractional_pesewa_amounts(self):
        for amount in ("0", "-1.00", "1.001"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.group.record_contribution("Ama", 1, amount)

    def test_rejects_payment_above_remaining_balance(self):
        self.group.record_contribution("Ama", 1, "30.00")
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.group.record_contribution("Ama", 1, "20.01")

    def test_only_current_week_can_receive_contributions(self):
        with self.assertRaisesRegex(ValueError, "current week 1"):
            self.group.record_contribution("Ama", 2, "10.00")

    def test_membership_freezes_after_first_contribution(self):
        self.group.record_contribution("Ama", 1, "1.00")
        with self.assertRaisesRegex(ValueError, "cannot be added"):
            self.group.add_member("Nana")

    def test_money_and_pot_are_exact_to_the_pesewa(self):
        group = SusuGroup("0.10")
        group.add_member("A")
        group.add_member("B")
        group.record_contribution("A", 1, "0.10")
        group.record_contribution("B", 1, "0.10")

        payout = group.close_week()

        self.assertEqual(payout.amount, Decimal("0.20"))
        self.assertEqual(f"{payout.amount:.2f}", "0.20")

    def test_group_finishes_after_every_member_receives_once(self):
        for name in self.group.members:
            self.group.record_contribution(name, 1, "50.00")
        self.group.close_week()

        for name in self.group.members:
            self.group.record_contribution(name, 2, "50.00")
        self.group.close_week()
        for name in self.group.members:
            self.group.record_contribution(name, 3, "50.00")
        final_payout = self.group.close_week()

        self.assertEqual(final_payout.recipient, "Esi")
        self.assertTrue(self.group.is_complete)
        self.assertIn("No active week", self.group.report())
        self.assertNotIn("owes GHS", self.group.report())
        with self.assertRaisesRegex(ValueError, "completed"):
            self.group.close_week()


if __name__ == "__main__":
    unittest.main()
