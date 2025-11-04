import sqlite3
from pathlib import Path
import argparse


def init_db(db_path: str = "endowment.db") -> Path:
	"""Create (or open) an SQLite database file and return its Path.

	If the parent directory doesn't exist, it will be created.

	Args:
		db_path: File path for the SQLite database. Defaults to 'endowment.db'.

	Returns:
		Path: Absolute Path to the created/opened database file.
	"""
	p = Path(db_path)
	# Ensure the directory exists (no-op for current working directory)
	if p.parent and not p.parent.exists():
		p.parent.mkdir(parents=True, exist_ok=True)

	# Connecting to SQLite will create the file if it doesn't exist
	conn = sqlite3.connect(p)
	try:
		# No schema is required just to create the file; connection is enough.
		# You can uncomment the following line if you want to ensure a simple table exists:
		# conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
		pass
	finally:
		conn.close()

	return p.resolve()


def main() -> None:
	parser = argparse.ArgumentParser(description="Create an SQLite database file.")
	parser.add_argument(
		"db_path",
		nargs="?",
		default="endowment.db",
		help="Path to the SQLite database file to create (default: endowment.db)",
	)
	args = parser.parse_args()

	created_path = init_db(args.db_path)
	print(f"SQLite database is ready at: {created_path}")


if __name__ == "__main__":
	main()

