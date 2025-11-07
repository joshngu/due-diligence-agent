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
	import datetime as dt
	import calendar
	from random import Random
	from typing import Dict, Tuple, Iterable

	SCHEMA_VERSION = 1

	def _connect(db_path: Path) -> sqlite3.Connection:
		conn = sqlite3.connect(db_path)
		conn.execute("PRAGMA foreign_keys = ON;")
		return conn

	def ensure_schema(conn: sqlite3.Connection) -> None:
		"""Create the endowment schema if it doesn't exist and set schema version."""
		cur = conn.cursor()
		# meta first (used to store schema_version)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS meta (
				key TEXT PRIMARY KEY,
				value TEXT NOT NULL
			);
			"""
		)
		# core reference tables
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS asset_classes (
				asset_class_id INTEGER PRIMARY KEY,
				name TEXT NOT NULL UNIQUE
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS benchmarks (
				benchmark_id INTEGER PRIMARY KEY,
				name TEXT NOT NULL UNIQUE,
				ticker TEXT
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS funds (
				fund_id INTEGER PRIMARY KEY,
				name TEXT NOT NULL UNIQUE,
				asset_class_id INTEGER NOT NULL,
				benchmark_id INTEGER,
				FOREIGN KEY(asset_class_id) REFERENCES asset_classes(asset_class_id),
				FOREIGN KEY(benchmark_id) REFERENCES benchmarks(benchmark_id)
			);
			"""
		)
		# time series and policy tables
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS returns (
				asof TEXT NOT NULL,           -- YYYY-MM-DD month-end
				fund_id INTEGER NOT NULL,
				monthly_return REAL NOT NULL, -- decimal, e.g., 0.0123 = 1.23%
				PRIMARY KEY(asof, fund_id),
				FOREIGN KEY(fund_id) REFERENCES funds(fund_id)
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS contributions (
				contribution_id INTEGER PRIMARY KEY,
				asof TEXT NOT NULL,
				amount REAL NOT NULL,         -- positive=inflow, negative=outflow
				source TEXT                    -- e.g., gift, grant, operating
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS target_allocations (
				allocation_id INTEGER PRIMARY KEY,
				asof TEXT NOT NULL,
				asset_class_id INTEGER NOT NULL,
				weight REAL NOT NULL,         -- 0..1
				UNIQUE(asof, asset_class_id),
				FOREIGN KEY(asset_class_id) REFERENCES asset_classes(asset_class_id)
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS spending_policy (
				policy_id INTEGER PRIMARY KEY,
				name TEXT NOT NULL UNIQUE,
				rate REAL NOT NULL,           -- decimal, e.g., 0.045 for 4.5%
				smoothing_years INTEGER NOT NULL DEFAULT 3
			);
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS inflation (
				asof TEXT PRIMARY KEY,
				cpi_index REAL NOT NULL       -- arbitrary index level (e.g., 100 base)
			);
			"""
		)
		import sqlite3
		from pathlib import Path
		import argparse
		import datetime as dt
		import calendar
		from random import Random
		from typing import Dict, Tuple, Iterable


		SCHEMA_VERSION = 1


		def _connect(db_path: Path) -> sqlite3.Connection:
			conn = sqlite3.connect(db_path)
			conn.execute("PRAGMA foreign_keys = ON;")
			return conn


		def ensure_schema(conn: sqlite3.Connection) -> None:
			"""Create the endowment schema if it doesn't exist and set schema version."""
			cur = conn.cursor()
			# meta first (used to store schema_version)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS meta (
					key TEXT PRIMARY KEY,
					value TEXT NOT NULL
				);
				"""
			)
			# core reference tables
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS asset_classes (
					asset_class_id INTEGER PRIMARY KEY,
					name TEXT NOT NULL UNIQUE
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS benchmarks (
					benchmark_id INTEGER PRIMARY KEY,
					name TEXT NOT NULL UNIQUE,
					ticker TEXT
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS funds (
					fund_id INTEGER PRIMARY KEY,
					name TEXT NOT NULL UNIQUE,
					asset_class_id INTEGER NOT NULL,
					benchmark_id INTEGER,
					FOREIGN KEY(asset_class_id) REFERENCES asset_classes(asset_class_id),
					FOREIGN KEY(benchmark_id) REFERENCES benchmarks(benchmark_id)
				);
				"""
			)
			# time series and policy tables
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS returns (
					asof TEXT NOT NULL,           -- YYYY-MM-DD month-end
					fund_id INTEGER NOT NULL,
					monthly_return REAL NOT NULL, -- decimal, e.g., 0.0123 = 1.23%
					PRIMARY KEY(asof, fund_id),
					FOREIGN KEY(fund_id) REFERENCES funds(fund_id)
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS contributions (
					contribution_id INTEGER PRIMARY KEY,
					asof TEXT NOT NULL,
					amount REAL NOT NULL,         -- positive=inflow, negative=outflow
					source TEXT                    -- e.g., gift, grant, operating
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS target_allocations (
					allocation_id INTEGER PRIMARY KEY,
					asof TEXT NOT NULL,
					asset_class_id INTEGER NOT NULL,
					weight REAL NOT NULL,         -- 0..1
					UNIQUE(asof, asset_class_id),
					FOREIGN KEY(asset_class_id) REFERENCES asset_classes(asset_class_id)
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS spending_policy (
					policy_id INTEGER PRIMARY KEY,
					name TEXT NOT NULL UNIQUE,
					rate REAL NOT NULL,           -- decimal, e.g., 0.045 for 4.5%
					smoothing_years INTEGER NOT NULL DEFAULT 3
				);
				"""
			)
			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS inflation (
					asof TEXT PRIMARY KEY,
					cpi_index REAL NOT NULL       -- arbitrary index level (e.g., 100 base)
				);
				"""
			)
			# mark schema version
			cur.execute(
				"INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
				(str(SCHEMA_VERSION),),
			)
			conn.commit()


		def _month_ends(start: dt.date, end: dt.date) -> Iterable[dt.date]:
			"""Yield month-end dates from start to end inclusive.

			Both start and end are treated as calendar bounds; iteration begins at the
			month of `start` and ends at the month of `end`.
			"""
			y, m = start.year, start.month
			while (y, m) <= (end.year, end.month):
				last_day = calendar.monthrange(y, m)[1]
				yield dt.date(y, m, last_day)
				# increment month
				if m == 12:
					y, m = y + 1, 1
				else:
					m += 1


		def seed_sample_data(conn: sqlite3.Connection, *, start_year: int = 2006, end_year: int = None, rng_seed: int = 42) -> None:
			"""Populate the database with realistic, synthetic endowment-like data.

			Data includes asset classes, benchmarks, funds, target allocations, a simple
			spending policy, monthly fund returns, annual contributions, and inflation.
			"""
			rng = Random(rng_seed)
			if end_year is None:
				end_year = dt.date.today().year
			start = dt.date(start_year, 1, 1)
			# up to last full month
			today = dt.date.today()
			end_month = today.month - 1 or 12
			end_year_adjusted = today.year if today.month > 1 else today.year - 1
			end = dt.date(end_year_adjusted, end_month, 1)
			end = dt.date(end.year, end.month, calendar.monthrange(end.year, end.month)[1])

			cur = conn.cursor()

			# Reference data
			assets = [
				("US Equity",),
				("International Equity",),
				("Fixed Income",),
				("Real Assets",),
				("Private Equity",),
				("Cash",),
			]
			cur.executemany("INSERT OR IGNORE INTO asset_classes(name) VALUES(?)", assets)

			benchmarks = [
				("S&P 500", "^GSPC"),
				("MSCI ACWI ex US", None),
				("Bloomberg US Agg", None),
				("NAREIT", None),
				("Cambridge PE (proxy)", None),
				("3M T-Bill", None),
			]
			cur.executemany(
				"INSERT OR IGNORE INTO benchmarks(name, ticker) VALUES(?, ?)", benchmarks
			)

			# Map asset_classes to ids
			cur.execute("SELECT asset_class_id, name FROM asset_classes")
			ac_id_by_name = {name: ac_id for ac_id, name in cur.fetchall()}
			cur.execute("SELECT benchmark_id, name FROM benchmarks")
			bm_id_by_name = {name: bm_id for bm_id, name in cur.fetchall()}

			funds = [
				("US Equity", ac_id_by_name["US Equity"], bm_id_by_name["S&P 500"]),
				("International Equity", ac_id_by_name["International Equity"], bm_id_by_name["MSCI ACWI ex US"]),
				("Fixed Income", ac_id_by_name["Fixed Income"], bm_id_by_name["Bloomberg US Agg"]),
				("Real Assets", ac_id_by_name["Real Assets"], bm_id_by_name["NAREIT"]),
				("Private Equity", ac_id_by_name["Private Equity"], bm_id_by_name["Cambridge PE (proxy)"]),
				("Cash", ac_id_by_name["Cash"], bm_id_by_name["3M T-Bill"]),
			]
			cur.executemany(
				"INSERT OR IGNORE INTO funds(name, asset_class_id, benchmark_id) VALUES(?, ?, ?)",
				funds,
			)

			# Target allocation policy (example as of 2019-06-30)
			alloc_date = "2019-06-30"
			allocations: Dict[str, float] = {
				"US Equity": 0.30,
				"International Equity": 0.20,
				"Fixed Income": 0.20,
				"Real Assets": 0.10,
				"Private Equity": 0.15,
				"Cash": 0.05,
			}
			rows = [
				(alloc_date, ac_id_by_name[name], weight) for name, weight in allocations.items()
			]
			cur.executemany(
				"INSERT OR IGNORE INTO target_allocations(asof, asset_class_id, weight) VALUES(?, ?, ?)",
				rows,
			)

			# Spending policy
			cur.execute(
				"INSERT OR IGNORE INTO spending_policy(name, rate, smoothing_years) VALUES(?, ?, ?)",
				("default", 0.045, 3),
			)

			# Generate monthly returns per fund (synthetic but plausible)
			# Annualized assumptions: (mu, sigma)
			assumptions: Dict[str, Tuple[float, float]] = {
				"US Equity": (0.07, 0.15),
				"International Equity": (0.065, 0.16),
				"Fixed Income": (0.03, 0.05),
				"Real Assets": (0.05, 0.10),
				"Private Equity": (0.09, 0.25),
				"Cash": (0.02, 0.01),
			}
			cur.execute("SELECT fund_id, name FROM funds")
			fund_id_by_name = {name: fid for fid, name in cur.fetchall()}

			def monthly_params(mu: float, sigma: float) -> Tuple[float, float]:
				return (mu / 12.0, sigma / (12.0 ** 0.5))

			return_rows = []
			for d in _month_ends(start, end):
				asof = d.isoformat()
				for name, (ann_mu, ann_sigma) in assumptions.items():
					m_mu, m_sd = monthly_params(ann_mu, ann_sigma)
					# Normal draw; lightweight clipping to avoid extreme tails
					r = max(min(rng.gauss(m_mu, m_sd), 0.35), -0.35)
					return_rows.append((asof, fund_id_by_name[name], r))
			cur.executemany(
				"INSERT OR IGNORE INTO returns(asof, fund_id, monthly_return) VALUES(?, ?, ?)",
				return_rows,
			)

			# Annual contributions: simple +$2M each July 1
			contrib_rows = []
			for y in range(max(start.year, 2010), end.year + 1):
				contrib_rows.append((f"{y}-07-01", 2_000_000.0, "gift"))
			cur.executemany(
				"INSERT OR IGNORE INTO contributions(asof, amount, source) VALUES(?, ?, ?)",
				contrib_rows,
			)

			# Inflation series (CPI index base ~100 at start)
			cpi_rows = []
			cpi = 100.0
			for d in _month_ends(start, end):
				mu = 0.025 / 12.0
				sd = 0.01 / (12.0 ** 0.5)
				infl = rng.gauss(mu, sd)
				cpi *= (1.0 + infl)
				cpi_rows.append((d.isoformat(), cpi))
			cur.executemany(
				"INSERT OR REPLACE INTO inflation(asof, cpi_index) VALUES(?, ?)",
				cpi_rows,
			)

			conn.commit()


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
			conn = _connect(p)
			try:
				ensure_schema(conn)
			finally:
				conn.close()

			return p.resolve()


		def _print_summary(conn: sqlite3.Connection) -> None:
			cur = conn.cursor()
			def count(table: str) -> int:
				cur.execute(f"SELECT COUNT(*) FROM {table}")
				return int(cur.fetchone()[0])
			cur.execute("SELECT value FROM meta WHERE key='schema_version'")
			row = cur.fetchone()
			version = row[0] if row else "?"
			print("Schema version:", version)
			for t in [
				"asset_classes",
				"benchmarks",
				"funds",
				"returns",
				"contributions",
				"target_allocations",
				"spending_policy",
				"inflation",
			]:
				print(f"{t}: {count(t):,} rows")


		def main() -> None:
			parser = argparse.ArgumentParser(description="Endowment DB utilities (SQLite)")
			subparsers = parser.add_subparsers(dest="command", required=False)

			# init command
			p_init = subparsers.add_parser("init", help="Create DB file and schema")
			p_init.add_argument("db_path", nargs="?", default="endowment.db")

			# seed command
			p_seed = subparsers.add_parser("seed", help="Populate DB with sample endowment-like data")
			p_seed.add_argument("db_path", nargs="?", default="endowment.db")
			p_seed.add_argument("--start-year", type=int, default=2006)
			p_seed.add_argument("--end-year", type=int)
			p_seed.add_argument("--seed", type=int, default=42, dest="rng_seed")

			# summary command
			p_sum = subparsers.add_parser("summary", help="Print table row counts and schema version")
			p_sum.add_argument("db_path", nargs="?", default="endowment.db")

			args = parser.parse_args()
			cmd = args.command or "init"

			if cmd == "init":
				created_path = init_db(args.db_path)
				print(f"SQLite database is ready at: {created_path}")
			elif cmd == "seed":
				p = Path(args.db_path)
				created = not p.exists()
				if created:
					print("DB does not exist; creating and initializing schema...")
					init_db(p.as_posix())
				conn = _connect(p)
				try:
					ensure_schema(conn)
					seed_sample_data(conn, start_year=args.start_year, end_year=args.end_year, rng_seed=args.rng_seed)
					print("Seeded sample data.")
				finally:
					conn.close()
			elif cmd == "summary":
				p = Path(args.db_path)
				if not p.exists():
					print(f"DB not found: {p}")
					return
				conn = _connect(p)
				try:
					_print_summary(conn)
				finally:
					conn.close()
			else:
				parser.print_help()


		if __name__ == "__main__":
			main()
		]
		cur.executemany("INSERT OR IGNORE INTO asset_classes(name) VALUES(?)", assets)

		benchmarks = [
			("S&P 500", "^GSPC"),
			("MSCI ACWI ex US", None),
			("Bloomberg US Agg", None),
			("NAREIT", None),
			("Cambridge PE (proxy)", None),
			("3M T-Bill", None),
		]
		cur.executemany(
			"INSERT OR IGNORE INTO benchmarks(name, ticker) VALUES(?, ?)", benchmarks
		)

		# Map asset_classes to ids
		cur.execute("SELECT asset_class_id, name FROM asset_classes")
		ac_id_by_name = {name: ac_id for ac_id, name in cur.fetchall()}
		cur.execute("SELECT benchmark_id, name FROM benchmarks")
		bm_id_by_name = {name: bm_id for bm_id, name in cur.fetchall()}

		funds = [
			("US Equity", ac_id_by_name["US Equity"], bm_id_by_name["S&P 500"]),
			("International Equity", ac_id_by_name["International Equity"], bm_id_by_name["MSCI ACWI ex US"]),
			("Fixed Income", ac_id_by_name["Fixed Income"], bm_id_by_name["Bloomberg US Agg"]),
			("Real Assets", ac_id_by_name["Real Assets"], bm_id_by_name["NAREIT"]),
			("Private Equity", ac_id_by_name["Private Equity"], bm_id_by_name["Cambridge PE (proxy)"]),
			("Cash", ac_id_by_name["Cash"], bm_id_by_name["3M T-Bill"]),
		]
		cur.executemany(
			"INSERT OR IGNORE INTO funds(name, asset_class_id, benchmark_id) VALUES(?, ?, ?)",
			funds,
		)

		# Target allocation policy (example as of 2019-06-30)
		alloc_date = "2019-06-30"
		allocations: Dict[str, float] = {
			"US Equity": 0.30,
			"International Equity": 0.20,
			"Fixed Income": 0.20,
			"Real Assets": 0.10,
			"Private Equity": 0.15,
			"Cash": 0.05,
		}
		rows = [
			(alloc_date, ac_id_by_name[name], weight) for name, weight in allocations.items()
		]
		cur.executemany(
			"INSERT OR IGNORE INTO target_allocations(asof, asset_class_id, weight) VALUES(?, ?, ?)",
			rows,
		)

		# Spending policy
		cur.execute(
			"INSERT OR IGNORE INTO spending_policy(name, rate, smoothing_years) VALUES(?, ?, ?)",
			("default", 0.045, 3),
		)

		# Generate monthly returns per fund (synthetic but plausible)
		# Annualized assumptions: (mu, sigma)
		assumptions: Dict[str, Tuple[float, float]] = {
			"US Equity": (0.07, 0.15),
			"International Equity": (0.065, 0.16),
			"Fixed Income": (0.03, 0.05),
			"Real Assets": (0.05, 0.10),
			"Private Equity": (0.09, 0.25),
			"Cash": (0.02, 0.01),
		}
		cur.execute("SELECT fund_id, name FROM funds")
		fund_id_by_name = {name: fid for fid, name in cur.fetchall()}

		def monthly_params(mu: float, sigma: float) -> Tuple[float, float]:
			return (mu / 12.0, sigma / (12.0 ** 0.5))

		return_rows = []
		for d in _month_ends(start, end):
			asof = d.isoformat()
			for name, (ann_mu, ann_sigma) in assumptions.items():
				m_mu, m_sd = monthly_params(ann_mu, ann_sigma)
				# Normal draw; lightweight clipping to avoid extreme tails
				r = max(min(rng.gauss(m_mu, m_sd), 0.35), -0.35)
				return_rows.append((asof, fund_id_by_name[name], r))
		cur.executemany(
			"INSERT OR IGNORE INTO returns(asof, fund_id, monthly_return) VALUES(?, ?, ?)",
			return_rows,
		)

		# Annual contributions: simple +$2M each July 1
		contrib_rows = []
		for y in range(max(start.year, 2010), end.year + 1):
			contrib_rows.append((f"{y}-07-01", 2_000_000.0, "gift"))
		cur.executemany(
			"INSERT OR IGNORE INTO contributions(asof, amount, source) VALUES(?, ?, ?)",
			contrib_rows,
		)

		# Inflation series (CPI index base ~100 at start)
		cpi_rows = []
		cpi = 100.0
		for d in _month_ends(start, end):
			mu = 0.025 / 12.0
			sd = 0.01 / (12.0 ** 0.5)
			infl = rng.gauss(mu, sd)
			cpi *= (1.0 + infl)
			cpi_rows.append((d.isoformat(), cpi))
		cur.executemany(
			"INSERT OR REPLACE INTO inflation(asof, cpi_index) VALUES(?, ?)",
			cpi_rows,
		)

		conn.commit()
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
		conn = _connect(p)
		nargs="?",
			ensure_schema(conn)

	created_path = init_db(args.db_path)
	print(f"SQLite database is ready at: {created_path}")


	def _print_summary(conn: sqlite3.Connection) -> None:
		cur = conn.cursor()
		def count(table: str) -> int:
			cur.execute(f"SELECT COUNT(*) FROM {table}")
			return int(cur.fetchone()[0])
		cur.execute("SELECT value FROM meta WHERE key='schema_version'")
		row = cur.fetchone()
		version = row[0] if row else "?"
		print("Schema version:", version)
		for t in [
			"asset_classes",
			"benchmarks",
			"funds",
			"returns",
			"contributions",
			"target_allocations",
			"spending_policy",
			"inflation",
		]:
			print(f"{t}: {count(t):,} rows")

if __name__ == "__main__":
		parser = argparse.ArgumentParser(description="Endowment DB utilities (SQLite)")
		subparsers = parser.add_subparsers(dest="command", required=False)

		# init command
		p_init = subparsers.add_parser("init", help="Create DB file and schema")
		p_init.add_argument("db_path", nargs="?", default="endowment.db")

		# seed command
		p_seed = subparsers.add_parser("seed", help="Populate DB with sample endowment-like data")
		p_seed.add_argument("db_path", nargs="?", default="endowment.db")
		p_seed.add_argument("--start-year", type=int, default=2006)
		p_seed.add_argument("--end-year", type=int)
		p_seed.add_argument("--seed", type=int, default=42, dest="rng_seed")

		# summary command
		p_sum = subparsers.add_parser("summary", help="Print table row counts and schema version")
		p_sum.add_argument("db_path", nargs="?", default="endowment.db")

		args = parser.parse_args()
		cmd = args.command or "init"

		if cmd == "init":
			created_path = init_db(args.db_path)
			print(f"SQLite database is ready at: {created_path}")
		elif cmd == "seed":
			p = Path(args.db_path)
			created = not p.exists()
			if created:
				print("DB does not exist; creating and initializing schema...")
				init_db(p.as_posix())
			conn = _connect(p)
			try:
				ensure_schema(conn)
				seed_sample_data(conn, start_year=args.start_year, end_year=args.end_year, rng_seed=args.rng_seed)
				print("Seeded sample data.")
			finally:
				conn.close()
		elif cmd == "summary":
			p = Path(args.db_path)
			if not p.exists():
				print(f"DB not found: {p}")
				return
			conn = _connect(p)
			try:
				_print_summary(conn)
			finally:
				conn.close()
		else:
			parser.print_help()

