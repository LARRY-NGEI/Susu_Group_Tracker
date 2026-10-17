## Susu Group Tracker

A small Python command-line program for tracking one rotating susu group. Members contribute the same fixed KHS amount each week. Once everyone has paid in full, the whole pot goes to the next member in join order.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Run

From this directory, start the interactive menu:

```powershell
py main.py
```

If Python is available as `python` on your system, use `python main.py` instead. Enter the fixed contribution when prompted, then use the menu to add members, record contributions, close a week, and view the report. A contribution must include the week number shown in the report.

## Run tests

```powershell
py -m unittest discover -s tests -v
```

The automated tests cover partial payments, blocked week closure and outstanding dues, full payouts and payout order, invalid/unknown members and amounts, exact money handling, week validation, membership changes, and completion of a payout cycle.

## Example

For three members paying KHS 50.00 each, the weekly pot is KHS 150.00. If Esi pays KHS 30.00, closing the week reports that Esi owes KHS 20.00 and does not pay out. After that balance is recorded, closing the week pays KHS 150.00 to Ama, the first member added.
