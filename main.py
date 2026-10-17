"""Command-line tracker for one rotating susu savings group."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext


CENT = Decimal("0.01")


def parse_money(value: str | Decimal) -> Decimal:
    """Parse a positive GHS amount with no fractional pesewas."""
    try:
        amount = value if isinstance(value, Decimal) else Decimal(value.strip())
    except (InvalidOperation, ValueError, AttributeError):
        raise ValueError("Enter a valid amount, such as 50.00.") from None

    if not amount.is_finite():
        raise ValueError("Amount must be a finite number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    try:
        with localcontext() as context:
            context.prec = max(context.prec, len(amount.as_tuple().digits) + max(amount.adjusted(), 0) + 3)
            normalized = amount.quantize(CENT)
    except InvalidOperation:
        raise ValueError("Amount is outside the supported numeric range.") from None
    if amount != normalized:
        raise ValueError("Amounts must not have more than two decimal places.")
    return normalized


def _to_cents(amount: Decimal) -> int:
    sign, digits, exponent = amount.as_tuple()
    if exponent != -2:
        raise ValueError("Internal money values must be normalized to cents.")
    cents = int("".join(str(digit) for digit in digits))
    return -cents if sign else cents


def _from_cents(cents: int) -> Decimal:
    digits = tuple(int(digit) for digit in str(abs(cents))) or (0,)
    return Decimal((1 if cents < 0 else 0, digits, -2))


@dataclass(frozen=True)
class Payout:
    week: int
    recipient: str
    amount: Decimal


class WeekNotReadyError(ValueError):
    def __init__(self, dues: list[tuple[str, Decimal]]):
        self.dues = dues
        details = ", ".join(f"{name} owes GHS {amount:.2f}" for name, amount in dues)
        super().__init__(f"Week cannot close. {details}")


class SusuGroup:
    def __init__(self, weekly_contribution: str | Decimal):
        self.weekly_contribution = parse_money(weekly_contribution)
        self._weekly_cents = _to_cents(self.weekly_contribution)
        self.members: list[str] = []
        self._member_keys: dict[str, str] = {}
        self._paid: dict[str, int] = {}
        self.payout_history: list[Payout] = []
        self.current_week = 1
        self._has_started = False

    @property
    def is_complete(self) -> bool:
        return len(self.payout_history) == len(self.members) and bool(self.members)

    def add_member(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Member name or ID cannot be blank.")
        name = name.strip()
        key = name.casefold()
        if key in self._member_keys:
            raise ValueError(f"Member '{name}' already exists.")
        if self._has_started:
            raise ValueError("Members cannot be added after the first contribution.")

        self.members.append(name)
        self._member_keys[key] = name
        self._paid[key] = 0

    def record_contribution(self, member: str, week: int, amount: str | Decimal) -> Decimal:
        key = member.strip().casefold() if isinstance(member, str) else ""
        if key not in self._member_keys:
            raise ValueError(f"Unknown member '{member}'.")
        if type(week) is not int or week != self.current_week:
            raise ValueError(f"Contributions can only be recorded for current week {self.current_week}.")
        if self.is_complete:
            raise ValueError("This susu group has completed its payout cycle.")

        payment = parse_money(amount)
        payment_cents = _to_cents(payment)
        owed_cents = self._weekly_cents - self._paid[key]
        if payment_cents > owed_cents:
            raise ValueError(f"Payment exceeds the amount owed (GHS {_from_cents(owed_cents):.2f}).")

        self._paid[key] += payment_cents
        self._has_started = True
        return _from_cents(self._weekly_cents - self._paid[key])

    def close_week(self) -> Payout:
        if self.is_complete:
            raise ValueError("This susu group has completed its payout cycle.")
        if not self.members:
            raise ValueError("Add at least one member before closing a week.")

        dues = [
            (name, _from_cents(self._weekly_cents - self._paid[name.casefold()]))
            for name in self.members
            if self._paid[name.casefold()] < self._weekly_cents
        ]
        if dues:
            raise WeekNotReadyError(dues)

        recipient = self.members[len(self.payout_history)]
        payout = Payout(
            week=self.current_week,
            recipient=recipient,
            amount=_from_cents(self._weekly_cents * len(self.members)),
        )
        self.payout_history.append(payout)
        self.current_week += 1
        for key in self._paid:
            self._paid[key] = 0
        return payout

    def report(self) -> str:
        status = "Complete" if self.is_complete else "Active"
        lines = [
            f"Group status: {status}",
            f"Weekly contribution: GHS {self.weekly_contribution:.2f}",
            (
                f"Current week: none (payout cycle completed after week {self.current_week - 1})"
                if self.is_complete
                else f"Current week: {self.current_week}"
            ),
            "Members and current-week payments:",
        ]
        if self.is_complete:
            lines.append("  No active week; all contributions for the payout cycle were settled.")
        elif not self.members:
            lines.append("  No members yet.")
        else:
            for name in self.members:
                paid = self._paid[name.casefold()]
                if paid == self._weekly_cents:
                    lines.append(f"  {name}: paid in full (GHS {_from_cents(paid):.2f})")
                else:
                    owed = self._weekly_cents - paid
                    lines.append(
                        f"  {name}: paid GHS {_from_cents(paid):.2f}; "
                        f"owes GHS {_from_cents(owed):.2f}"
                    )

        if not self.is_complete:
            next_recipient = self.members[len(self.payout_history)] if self.members else "Not determined"
            lines.append(f"Next payout recipient: {next_recipient}")
        lines.append("Payout history:")
        if not self.payout_history:
            lines.append("  No payouts yet.")
        else:
            for payout in self.payout_history:
                lines.append(
                    f"  Week {payout.week}: {payout.recipient} received GHS {payout.amount:.2f}"
                )
        return "\n".join(lines)


def run_cli() -> None:
    print("Susu Group Tracker")
    while True:
        try:
            weekly_amount = input("Fixed weekly contribution in GHS: ")
            group = SusuGroup(weekly_amount)
            break
        except ValueError as error:
            print(f"Invalid contribution: {error}")

    while True:
        print(
            "\n1. Add member\n"
            "2. Record contribution\n"
            "3. Close current week\n"
            "4. Show report\n"
            "5. Exit"
        )
        try:
            choice = input("Choose an option: ").strip()
            if choice == "1":
                group.add_member(input("Member name or ID: "))
                print("Member added.")
            elif choice == "2":
                member = input("Member name or ID: ")
                week = int(input("Week number: ").strip())
                amount = input("Payment in GHS: ")
                remaining = group.record_contribution(member, week, amount)
                print(f"Contribution recorded. This member still owes GHS {remaining:.2f}.")
            elif choice == "3":
                payout = group.close_week()
                print(
                    f"Week {payout.week} closed. {payout.recipient} receives "
                    f"GHS {payout.amount:.2f}."
                )
            elif choice == "4":
                print(group.report())
            elif choice == "5":
                print("Goodbye.")
                return
            else:
                print("Choose an option from 1 to 5.")
        except WeekNotReadyError as error:
            print(error)
        except ValueError as error:
            print(f"Error: {error}")
        except EOFError:
            print("\nGoodbye.")
            return
        except KeyboardInterrupt:
            print("\nGoodbye.")
            return


if __name__ == "__main__":
    run_cli()
