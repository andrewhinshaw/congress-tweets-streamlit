import time
import os
import glob
import json
import logging
from multiprocessing import Pool

import duckdb
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

DB_PATH = "./data/tweets_sentiment.duckdb"
logging.basicConfig(level=logging.DEBUG, format=f"%(levelname)s: %(message)s\n")

def analyze_sentiment(tweet):
	"""
	Analyzes the sentiment of a single tweet and returns the original tweet object
	with the sentiment field added.

	Arguments:
		tweet (dict): The tweet object containing the tweet text and other relevant fields
	Returns:
		dict: The tweet object with the sentiment field added or None if the tweet could
			not be abalyzed
	"""

	analyzer = SentimentIntensityAnalyzer()

	try:
		tweet["sentiment"] = analyzer.polarity_scores(tweet["text"]).get("compound")
	except KeyError as e:
		print(f"Unable to process tweet {tweet}")
		return None

	return tweet

def process_json_tweets_data():
	"""
	Get all the json files from the /data/json directory, analyze the tweet sentiment
	and write to parquet files. Uses multiprocessing to speed up workload.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Processing json tweets data...")

	# Initialize helper variables
	tweets = []

	# Initialize multiprocessing pool
	pool = Pool(processes=4)

	# Find all json data files
	files = glob.glob("./data/json/*.json")

	for current_file in files:
		with open(current_file, "r", encoding="utf8") as fin:

			# Load and analyze tweets
			tweets = json.load(fin)
			tweets_analyzed = pool.map(analyze_sentiment, tweets)
			tweets_analyzed = list(filter(lambda x: x is not None, tweets_analyzed))

			# Convert to pandas df and write to parquet file
			df = pd.DataFrame(tweets_analyzed)
			df.to_parquet(f"./data/parquet/{os.path.basename(current_file).replace('.json', '')}.parquet")

	logging.info("Done.")

def process_json_accounts_data():
	"""
	Get all the json files from the /data/json/accounts directory and write accounts to
	parquet file.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Processing json accounts data...")

	with open("./data/json/accounts/accounts.json", "r", encoding="utf8") as fin:
		accounts = []

		users = json.load(fin)
		df = pd.DataFrame(users)
		df = df.replace({np.nan: None})
		df = df.replace({"N/A": None})

		# Iterate over rows and grab all accounts for each row
		for index, row in df.iterrows():
			for account in row["accounts"]:
				accounts.append({
					"id": account["id"],
					"screen_name": account["screen_name"],
					"account_type": account["account_type"],
					"name": row["name"],
					"chamber": row["chamber"],
					"type": row["type"],
					"party": row["party"],
					"state": row["state"]
				})

		# Create an accounts dataframe and write to parquet file
		df_accounts = pd.DataFrame(accounts)
		df_accounts.to_parquet("./data/parquet/accounts/accounts.parquet")
	
	logging.info("Done.")

def aggregate_parquet_data():
	"""
	Aggregates all parquet files in the /data/parquet directories into one single parquet file
	each for tweets and accounts.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Aggregating parquet data...")

	pq.write_table(pq.ParquetDataset('./data/parquet/').read(), './data/tweets.parquet', row_group_size=100000)
	pq.write_table(pq.ParquetDataset('./data/parquet/accounts').read(), './data/accounts.parquet', row_group_size=100000)

	logging.info("Done.")

def read_parquet_data():
	"""
	Reads the aggregated parquet file into a pandas dataframe and prints a preview of the result.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Reading parquet data...")

	tweets_table = pq.read_table('./data/tweets.parquet')
	df_tweets = tweets_table.to_pandas()

	accounts_table = pq.read_table('./data/accounts.parquet')
	df_accounts = accounts_table.to_pandas()

	logging.info(f"Tweets data: {df_tweets.head()}")
	logging.info(f"Accounts data: {df_accounts.head()}")

def load_duckdb():
	"""
	Creates the tweets and accounts tables in the duckdb database from the parquet files.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Loading data into duckdb...")

	con = duckdb.connect(database=DB_PATH)

	# Drop the existing tables before recreating
	con.execute("DROP TABLE IF EXISTS tweets")
	con.execute("DROP TABLE IF EXISTS accounts")

	# Create the tweets table
	con.execute("""--sql
		CREATE OR REPLACE TABLE tweets
		AS SELECT
			user_id AS account_id,
			screen_name,
			text,
			sentiment,
			link,
			STRPTIME(time, '%xT%X%z') AS created_at
		FROM './data/tweets.parquet'
	""")

	# Create the accounts table
	con.execute("""--sql
		CREATE OR REPLACE TABLE accounts
		AS SELECT
			id,
			screen_name,
			account_type,
			name,
			chamber,
			type,
			party,
			state
		FROM './data/accounts.parquet'
	""")

	logging.info("Done.")

def read_duckdb():
	"""
	Selects all rows from the tables in the duckdb database to preview the data.

	Parameters: N/A
	Returns: N/A
	"""

	logging.info("Reading duckdb data...")

	con = duckdb.connect(database=DB_PATH, read_only=True)

	con.sql("SELECT * FROM tweets LIMIT 5").show()
	con.sql("SELECT * FROM accounts LIMIT 5").show()

if __name__ == '__main__':

	# Process json tweet data
	# process_json_tweets_data()

	# Process json account data
	# process_json_accounts_data()

	# Aggregate parquet data into one parquet file
	# aggregate_parquet_data()

	# Read parquet data into pandas df
	# read_parquet_data()

	# Load the parquet data into the duckdb database
	# load_duckdb()

	# Read the data from the duckdb database
	read_duckdb()
