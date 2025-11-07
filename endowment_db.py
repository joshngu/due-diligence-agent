import sqlite3
from pathlib import Path
import argparse
import datetime as dt
import calendar
from random import Random
from typing import Dict, Tuple, Iterable
import pandas as pd


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


def _get_or_create(cur: sqlite3.Cursor, table: str, key_col: str, key_val: str, id_col: str) -> int:
	cur.execute(f"SELECT {id_col} FROM {table} WHERE {key_col} = ?", (key_val,))
	row = cur.fetchone()
	if row:
		return int(row[0])
	cur.execute(f"INSERT INTO {table}({key_col}) VALUES(?)", (key_val,))
	return int(cur.lastrowid)


def import_from_excel(conn: sqlite3.Connection, xlsx_path: str) -> None:
	"""Import endowment data from an Excel workbook into the DB.

	Expected sheets and columns (case-insensitive headers):
	- asset_classes: name
	- benchmarks: name, ticker
	- funds: name, asset_class, benchmark
	- returns: asof, fund, monthly_return (decimal; percent allowed e.g., 1.2% or 1.2)
	- contributions: asof, amount, source
	- target_allocations: asof, asset_class, weight (0..1 or percent)
	- spending_policy: name, rate (decimal or %), smoothing_years
	- inflation: asof, cpi_index
	"""
	xls = pd.ExcelFile(xlsx_path)
	cur = conn.cursor()

	def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
		df = df.copy()
		df.columns = [str(c).strip().lower() for c in df.columns]
		return df

	if 'asset_classes' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'asset_classes'))
		for _, r in df.iterrows():
			name = str(r.get('name', '')).strip()
			if name:
				cur.execute("INSERT OR IGNORE INTO asset_classes(name) VALUES(?)", (name,))

	if 'benchmarks' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'benchmarks'))
		for _, r in df.iterrows():
			name = str(r.get('name', '')).strip()
			ticker = r.get('ticker')
			ticker = None if (pd.isna(ticker) or ticker == '') else str(ticker)
			if name:
				cur.execute("INSERT OR IGNORE INTO benchmarks(name, ticker) VALUES(?, ?)", (name, ticker))

	# build maps after potential inserts
	cur.execute("SELECT asset_class_id, name FROM asset_classes")
	ac_id = {name: i for i, name in cur.fetchall()}
	cur.execute("SELECT benchmark_id, name FROM benchmarks")
	bm_id = {name: i for i, name in cur.fetchall()}

	if 'funds' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'funds'))
		for _, r in df.iterrows():
			name = str(r.get('name', '')).strip()
			ac_name = str(r.get('asset_class', '')).strip()
			bm_name = str(r.get('benchmark', '')).strip() if 'benchmark' in df.columns else ''
			if not name or not ac_name:
				continue
			ac = ac_id.get(ac_name) or _get_or_create(cur, 'asset_classes', 'name', ac_name, 'asset_class_id')
			ac_id[ac_name] = ac
			bm = None
			if bm_name:
				bm = bm_id.get(bm_name)
				if bm is None:
					cur.execute("INSERT INTO benchmarks(name) VALUES(?)", (bm_name,))
					bm = int(cur.lastrowid)
					bm_id[bm_name] = bm
			cur.execute(
				"INSERT OR IGNORE INTO funds(name, asset_class_id, benchmark_id) VALUES(?, ?, ?)",
				(name, ac, bm),
			)

	# map funds after insertion
	cur.execute("SELECT fund_id, name FROM funds")
	fund_id = {name: i for i, name in cur.fetchall()}

	def parse_date(val) -> str:
		if pd.isna(val) or val == '':
			return ''
		try:
			d = pd.to_datetime(val)
			return d.date().isoformat()
		except Exception:
			return str(val)

	def parse_decimal(val) -> float:
		if pd.isna(val) or val == '':
			return None
		if isinstance(val, str) and val.strip().endswith('%'):
			try:
				return float(val.strip()[:-1]) / 100.0
			except Exception:
				return None
		try:
			v = float(val)
			# If it looks like a percent (e.g., 4.5) but not decimal, assume %
			if v > 1.0 and v <= 100.0:
				return v / 100.0
			return v
		except Exception:
			return None

	if 'returns' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'returns'))
		rows = []
		for _, r in df.iterrows():
			asof = parse_date(r.get('asof'))
			fund_name = str(r.get('fund', '')).strip()
			ret = parse_decimal(r.get('monthly_return'))
			fid = fund_id.get(fund_name)
			if asof and fid and (ret is not None):
				rows.append((asof, fid, ret))
		if rows:
			cur.executemany("INSERT OR REPLACE INTO returns(asof, fund_id, monthly_return) VALUES(?, ?, ?)", rows)

	if 'contributions' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'contributions'))
		rows = []
		for _, r in df.iterrows():
			asof = parse_date(r.get('asof'))
			amount = r.get('amount')
			try:
				amount = float(amount)
			except Exception:
				amount = None
			source = r.get('source')
			source = None if (pd.isna(source) or source == '') else str(source)
			if asof and amount is not None:
				rows.append((asof, amount, source))
		if rows:
			cur.executemany("INSERT INTO contributions(asof, amount, source) VALUES(?, ?, ?)", rows)

	if 'target_allocations' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'target_allocations'))
		rows = []
		for _, r in df.iterrows():
			asof = parse_date(r.get('asof'))
			ac_name = str(r.get('asset_class', '')).strip()
			w = parse_decimal(r.get('weight'))
			if not asof or not ac_name or w is None:
				continue
			ac = ac_id.get(ac_name) or _get_or_create(cur, 'asset_classes', 'name', ac_name, 'asset_class_id')
			ac_id[ac_name] = ac
			rows.append((asof, ac, w))
		if rows:
			cur.executemany("INSERT OR REPLACE INTO target_allocations(asof, asset_class_id, weight) VALUES(?, ?, ?)", rows)

	if 'spending_policy' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'spending_policy'))
		for _, r in df.iterrows():
			name = str(r.get('name', 'default') or 'default').strip()
			rate = parse_decimal(r.get('rate')) or 0.045
			smoothing_years = int(r.get('smoothing_years') or 3)
			cur.execute("INSERT OR REPLACE INTO spending_policy(policy_id, name, rate, smoothing_years) VALUES(1, ?, ?, ?)", (name, rate, smoothing_years))

	if 'inflation' in xls.sheet_names:
		df = norm_cols(pd.read_excel(xls, 'inflation'))
		rows = []
		for _, r in df.iterrows():
			asof = parse_date(r.get('asof'))
			idx = r.get('cpi_index')
			try:
				idx = float(idx)
			except Exception:
				idx = None
			if asof and (idx is not None):
				rows.append((asof, idx))
		if rows:
			cur.executemany("INSERT OR REPLACE INTO inflation(asof, cpi_index) VALUES(?, ?)", rows)

	conn.commit()


def make_template_xlsx(path: str) -> None:
	"""Generate an Excel template with the expected sheets and headers."""
	with pd.ExcelWriter(path, engine='openpyxl') as xw:
		pd.DataFrame(columns=['name']).to_excel(xw, sheet_name='asset_classes', index=False)
		pd.DataFrame(columns=['name', 'ticker']).to_excel(xw, sheet_name='benchmarks', index=False)
		pd.DataFrame(columns=['name', 'asset_class', 'benchmark']).to_excel(xw, sheet_name='funds', index=False)
		pd.DataFrame(columns=['asof', 'fund', 'monthly_return']).to_excel(xw, sheet_name='returns', index=False)
		pd.DataFrame(columns=['asof', 'amount', 'source']).to_excel(xw, sheet_name='contributions', index=False)
		pd.DataFrame(columns=['asof', 'asset_class', 'weight']).to_excel(xw, sheet_name='target_allocations', index=False)
		pd.DataFrame(columns=['name', 'rate', 'smoothing_years']).to_excel(xw, sheet_name='spending_policy', index=False)
		pd.DataFrame(columns=['asof', 'cpi_index']).to_excel(xw, sheet_name='inflation', index=False)


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

	# import-xlsx command
	p_imp = subparsers.add_parser("import-xlsx", help="Import data from an Excel workbook into the DB")
	p_imp.add_argument("xlsx_path", help="Path to .xlsx file")
	p_imp.add_argument("db_path", nargs="?", default="endowment.db")

	# make-template-xlsx command
	p_tpl = subparsers.add_parser("make-template-xlsx", help="Generate an Excel template with required sheets/columns")
	p_tpl.add_argument("xlsx_path", help="Output path to .xlsx file to create")

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
	elif cmd == "import-xlsx":
		p = Path(args.db_path)
		if not p.exists():
			print("DB does not exist; creating and initializing schema...")
			init_db(p.as_posix())
		conn = _connect(p)
		try:
			ensure_schema(conn)
			import_from_excel(conn, args.xlsx_path)
			print("Imported data from Excel.")
		finally:
			conn.close()
	elif cmd == "make-template-xlsx":
		make_template_xlsx(args.xlsx_path)
		print(f"Template written to: {args.xlsx_path}")
	else:
		parser.print_help()


if __name__ == "__main__":
	main()