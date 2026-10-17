# Notes

## Assumptions and decisions

- A group is created at startup with one fixed, positive weekly contribution in GHS.
- Names/IDs are trimmed and compared case-insensitively, so `Larry` and `larry` identify the same member; original spelling is retained for reports.
- Members may be added until the first successful contribution. Membership is then frozen so the pot size and payout order do not change mid-cycle.
- Contributions apply only to the current week. A member can make multiple partial payments, but each payment must be positive, no larger than the remaining balance, and exact to two decimal places.
- A week cannot close until every member has paid the full contribution. A blocked close reports each unpaid balance and leaves the week and payout history unchanged.
- The pot is the exact weekly contribution multiplied by the member count. One member receives it per successfully closed week in join order.
- The group is complete after each member has received the pot once. Further contributions and week closures are rejected.
- Closing an empty group's week is rejected.
- Amounts with more than two meaningful decimal places are rejected instead of rounded; all calculations use Python's `Decimal`.


