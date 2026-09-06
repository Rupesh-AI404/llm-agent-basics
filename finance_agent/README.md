Personal Finance CLI Agent

Usage examples:

# Add income
python -m finance_agent.cli add income 3000 -c salary -d 2026-09-01 -n "September salary"

# Add expense
python -m finance_agent.cli add expense 45.50 -c groceries -n "Weekly groceries"

# Set monthly budget
python -m finance_agent.cli set-budget 2000

# Show summary for current month
python -m finance_agent.cli summary

# Export transactions to CSV
python -m finance_agent.cli export transactions.csv

Data is stored in a JSON file at ~/.finance_agent_data.json
