# Notes

## Assumptions and decisions

- A group is created at startup with one fixed, positive weekly contribution in KHS.
- Names/IDs are trimmed and compared case-insensitively, so `Larry` and `larry` identify the same member; original spelling is retained for reports.
- Members may be added until the first successful contribution. Membership is then frozen so the pot size and payout order do not change mid-cycle.
- Contributions apply only to the current week. A member can make multiple partial payments, but each payment must be positive, no larger than the remaining balance, and exact to two decimal places.
- A week cannot close until every member has paid the full contribution. A blocked close reports each unpaid balance and leaves the week and payout history unchanged.
- If a week is unfinished, it remains the current week: payments already recorded stay credited, members can pay their remaining balances, and no payout is made until everyone is paid in full.
- The group is stored only in memory. Exiting the program before the cycle finishes loses its members, payments, and payout history; the group must be entered again next time.
- The pot is the exact weekly contribution multiplied by the member count. One member receives it per successfully closed week in join order.
- The group is complete after each member has received the pot once. Further contributions and week closures are rejected.
- Closing an empty group's week is rejected.
- Amounts with more than two meaningful decimal places are rejected instead of rounded; all calculations use Python's `Decimal`.

## What I would improve with more time

- Save group membership, contributions, and payout history to durable storage so an unfinished cycle can resume after the program exits.
- Add an individual payment ledger with timestamps and a way to correct mistakes while preserving an audit trail.
- Expand tests for invalid startup amounts, blank member names, empty-group week closure, and reports listing multiple outstanding balances.
- Add clearer input prompts and a more convenient way to select the current week without manually entering its number.
