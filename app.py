import requests
import duckdb
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px

COLORS = {
	"white": "#f3f4f6",
	"blue": {
		"primary": "#3b82f6",
		"light": "#93c5fd",
		"dark": "#1d4ed8"
	},
	"red": {
		"primary": "#ef4444",
		"light": "#fca5a5",
		"dark": "#b91c1c"
	}
}

con = duckdb.connect(database="./data/tweets_sentiment.duckdb", read_only=True)

def show_kpis_combined():

	st.header("Combined Party Sentiment Year-To-Date")
	st.caption("Data only available through July 2023")

	df = con.execute("""--sql
		SELECT
			CASE 
				WHEN tweets.created_at BETWEEN '2023-01-01' AND '2023-07-21' THEN '2023'
				WHEN tweets.created_at BETWEEN '2022-01-01' AND '2022-07-21' THEN '2022'
				ELSE 'N/A'
				END AS 'Year',
			AVG(sentiment) AS avg_sentiment,
			SUM(CASE WHEN sentiment >= 0.05 THEN 1 ELSE 0 END) AS 'count_pos',
			SUM(CASE WHEN sentiment <= -0.05 THEN 1 ELSE 0 END) AS 'count_neg',
			SUM(CASE WHEN sentiment < 0.05 AND sentiment > -0.05 THEN 1 ELSE 0 END) AS 'count_neu',
			COUNT(*) AS 'count_total'
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party IN ('D', 'R')
		GROUP BY Year
		HAVING Year IN ('2022', '2023')
	""").df()
	
	df = df.set_index("Year")

	avg_sentiment_2022 = df.loc["2022"]["avg_sentiment"]
	avg_sentiment_2023 = df.loc["2023"]["avg_sentiment"]
	avg_sentiment_change = (avg_sentiment_2023 - avg_sentiment_2022) / abs(avg_sentiment_2022) * 100

	pct_neg_2022 = df.loc["2022"]["count_neg"] / df.loc["2022"]["count_total"] * 100
	pct_neg_2023 = df.loc["2023"]["count_neg"] / df.loc["2023"]["count_total"] * 100
	pct_neg_change = (pct_neg_2023 - pct_neg_2022) / abs(pct_neg_2022) * 100
	
	pct_pos_2022 = df.loc["2022"]["count_pos"] / df.loc["2022"]["count_total"] * 100
	pct_pos_2023 = df.loc["2023"]["count_pos"] / df.loc["2023"]["count_total"] * 100
	pct_pos_change = (pct_pos_2023 - pct_pos_2022) / abs(pct_pos_2022) * 100

	column_left, column_middle, column_right = st.columns(3)

	with column_left:
		column_left.metric("Average Sentiment (YTD)", round(avg_sentiment_2023, 2), f"{int(avg_sentiment_change)}%")

	with column_middle:
		column_middle.metric("Percentage Positive (YTD)", f"{int(pct_pos_2023)}%", f"{int(pct_pos_change)}%")

	with column_right:
		column_right.metric("Percentage Negative (YTD)", f"{int(pct_neg_2023)}%", f"{int(pct_neg_change)}%")

def show_average_sentiment_combined(page_options):

	st.header("Average Sentiment with Parties Combined")
	
	begin_date = f"{page_options['begin_year']}-01-01"
	end_date = f"{page_options['end_year']}-12-31"
	account_types = "'member'" if page_options["show_members_only"] else "'committee', 'member', 'caucus', 'party'"

	df = con.execute(f"""--sql
		SELECT
			STRFTIME(CAST(tweets.created_at AS TIMESTAMP), '%b %y') AS created_date,
			STRFTIME(CAST(tweets.created_at AS TIMESTAMP), '%Y-%m') AS created_date_order,
			'C' AS combined,
			AVG(tweets.sentiment) AS avg_sentiment
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party IN ('D', 'R')
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY created_date, created_date_order, combined
		ORDER BY created_date_order ASC
	""").df()

	fig = px.line(
		df, 
		x="created_date", 
		y="avg_sentiment", 
		color="combined", 
		line_shape="spline",
		color_discrete_map={ 
			"C": COLORS["white"],
		},
		labels={
			"avg_sentiment": "Average Sentiment",
			"created_date": "Date",
			"combined": "Party"
		}
	)

	# Rotate x-axis labels by 45 degrees
	fig.update_layout(xaxis_tickangle=-45)

	st.plotly_chart(fig, theme="streamlit", use_container_width=True)
		
def show_average_sentiment_by_party(page_options):

	st.header("Average Sentiment by Party")
	
	begin_date = f"{page_options['begin_year']}-01-01"
	end_date = f"{page_options['end_year']}-12-31"
	account_types = "'member'" if page_options["show_members_only"] else "'committee', 'member', 'caucus', 'party'"

	df = con.execute(f"""--sql
		SELECT
			STRFTIME(CAST(tweets.created_at AS TIMESTAMP), '%b %y') AS created_date,
			STRFTIME(CAST(tweets.created_at AS TIMESTAMP), '%Y-%m') AS created_date_order,
			party,
			AVG(sentiment) AS avg_sentiment
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party IN ('D', 'R')
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY created_date, created_date_order, party
		ORDER BY created_date_order ASC
	""").df()

	fig = px.line(
		df, 
		x="created_date", 
		y="avg_sentiment", 
		color="party", 
		line_shape="spline",
		color_discrete_map={ 
			"D": COLORS["blue"]["primary"], 
			"R": COLORS["red"]["primary"] 
		},
		labels={
			"avg_sentiment": "Average Sentiment",
			"created_date": "Date",
			"party": "Party"
		}
	)

	# Rotate x-axis labels by 45 degrees
	fig.update_layout(xaxis_tickangle=-45)

	st.plotly_chart(fig, theme="streamlit", use_container_width=True)

def show_pies_by_party(page_options):

	st.header("Sentiment Breakdown by Party")
	
	begin_date = f"{page_options['begin_year']}-01-01"
	end_date = f"{page_options['end_year']}-12-31"
	account_types = "'member'" if page_options["show_members_only"] else "'committee', 'member', 'caucus', 'party'"

	df = con.execute(f"""--sql
		SELECT
			party,
			CASE 
				WHEN sentiment >= 0.05 THEN 'positive'
				WHEN sentiment <= -0.05 THEN 'negative'
				ELSE 'neutral'
				END AS 'sentiment_classification',
			COUNT(*) AS count_tweets
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party IN ('D', 'R')
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY party, sentiment_classification
	""").df()

	# Show pie charts of sentimaent breakdown
	left_column, right_column = st.columns(2)

	with left_column:
		df_d = df.loc[df["party"] == "D"]
		fig_d = px.pie(
			df_d, 
			values="count_tweets", 
			names="sentiment_classification", 
			title="Democrat Accounts",
			color_discrete_sequence=[
				COLORS["blue"]["primary"],
				COLORS["blue"]["dark"],
				COLORS["blue"]["light"]
			]
		)
		left_column.plotly_chart(fig_d, theme="streamlit", use_container_width=True)

	with right_column:
		df_r = df.loc[df["party"] == "R"]
		fig_r = px.pie(
			df_r, 
			values="count_tweets", 
			names="sentiment_classification", 
			title="Republican Accounts",
			color_discrete_sequence=[
				COLORS["red"]["primary"],
				COLORS["red"]["dark"],
				COLORS["red"]["light"]
			]
		)
		right_column.plotly_chart(fig_r, theme="streamlit", use_container_width=True)

def format_tweet(url, text="", embed_str=False):
	html = ""

	if not embed_str:
		try:
			api = f"https://publish.twitter.com/oembed?url={url}"
			response = requests.get(api)
			html = response.json()["html"]
		except:
			return None
	else:
		html = f"<blockquote>{text}</blockquote>"
	
	return components.html(html, height=700)

def show_positive_accounts_by_party(page_options):

	st.header("Most Positive Accounts by Party")
	
	begin_date = f"{page_options['begin_year']}-01-01"
	end_date = f"{page_options['end_year']}-12-31"
	account_types = "'member'" if page_options["show_members_only"] else "'committee', 'member', 'caucus', 'party'"

	# Get statistics for positive tweets for Democrat accounts
	df_d_pos = con.execute(f"""--sql
		SELECT
			accounts.name,
			accounts.type,
			AVG(sentiment) AS avg_sentiment,
			SUM(CASE WHEN sentiment >= 0.05 THEN 1 ELSE 0 END) AS count_positive,
			SUM(CASE WHEN sentiment >= 0.05 THEN 1 ELSE 0 END) / COUNT(*) AS pct_positive
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='D'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY accounts.name, accounts.type
	""").df()

	# Get statistics for positive tweets for Republican accounts
	df_r_pos = con.execute(f"""--sql
		SELECT
			accounts.name,
			accounts.type,
			AVG(sentiment) AS avg_sentiment,
			SUM(CASE WHEN sentiment >= 0.05 THEN 1 ELSE 0 END) AS count_positive,
			SUM(CASE WHEN sentiment >= 0.05 THEN 1 ELSE 0 END) / COUNT(*) AS pct_positive
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='R'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY accounts.name, accounts.type
	""").df()

	# Get most positive tweet examples for Democrat accounts
	df_d_tweets_pos = con.execute(f"""--sql
		SELECT DISTINCT
			tweets.sentiment,
			tweets.text,
			tweets.link
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='D'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		ORDER BY tweets.sentiment DESC
		LIMIT 10
	""").df()

	# Get most positive tweet examples for Republican accounts
	df_r_tweets_pos = con.execute(f"""--sql
		SELECT DISTINCT
			tweets.sentiment,
			tweets.text,
			tweets.link
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='R'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		ORDER BY tweets.sentiment DESC
		LIMIT 10
	""").df()

	tab1, tab2, tab3 = st.tabs(["Average Sentiment", "Count Positive Tweets", "Percentage Positive Tweets"])

	with tab1:
		tab1.subheader("Average Sentiment by Account")

		# Show pie charts of sentimaent breakdown
		tab1_left_column, tab1_right_column = st.columns(2)

		with tab1_left_column:
			fig_d_tab1 = px.bar(
				df_d_pos.sort_values("avg_sentiment", ascending=False)[:10],
				x="avg_sentiment",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"avg_sentiment": "Average Sentiment",
					"name": "Name"
				}
			)
			fig_d_tab1.update_layout(yaxis_autorange="reversed")
			tab1_left_column.plotly_chart(fig_d_tab1, theme="streamlit", use_container_width=True)

		with tab1_right_column:
			fig_r_tab1 = px.bar(
				df_r_pos.sort_values("avg_sentiment", ascending=False)[:10],
				x="avg_sentiment",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"avg_sentiment": "Average Sentiment",
					"name": "Name"
				}
			)
			fig_r_tab1.update_layout(yaxis_autorange="reversed")
			tab1_right_column.plotly_chart(fig_r_tab1, theme="streamlit", use_container_width=True)

	with tab2:
		tab2.subheader("Count Positive Tweets by Account")

		# Show pie charts of sentimaent breakdown
		tab2_left_column, tab2_right_column = st.columns(2)

		with tab2_left_column:
			fig_d_tab2 = px.bar(
				df_d_pos.sort_values("count_positive", ascending=False)[:10],
				x="count_positive",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"count_positive": "Positive Tweets",
					"name": "Name"
				}
			)
			fig_d_tab2.update_layout(yaxis_autorange="reversed")
			tab2_left_column.plotly_chart(fig_d_tab2, theme="streamlit", use_container_width=True)

		with tab2_right_column:
			fig_r_tab2 = px.bar(
				df_r_pos.sort_values("count_positive", ascending=False)[:10],
				x="count_positive",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"count_positive": "Positive Tweets",
					"name": "Name"
				}
			)
			fig_r_tab2.update_layout(yaxis_autorange="reversed")
			tab2_right_column.plotly_chart(fig_r_tab2, theme="streamlit", use_container_width=True)

	with tab3:
		tab3.subheader("Percentage Positive Tweets by Account")
		
		# Show pie charts of sentimaent breakdown
		tab3_left_column, tab3_right_column = st.columns(2)

		with tab3_left_column:
			fig_d_tab3 = px.bar(
				df_d_pos.sort_values("pct_positive", ascending=False)[:10],
				x="pct_positive",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"pct_positive": "Positive Percentage",
					"name": "Name"
				}
			)
			fig_d_tab3.update_layout(yaxis_autorange="reversed", xaxis_tickformat = "~%")

			tab3_left_column.plotly_chart(fig_d_tab3, theme="streamlit", use_container_width=True)

		with tab3_right_column:
			fig_r_tab3 = px.bar(
				df_r_pos.sort_values("pct_positive", ascending=False)[:10],
				x="pct_positive",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"pct_positive": "Positive Percentage",
					"name": "Name"
				}
			)
			fig_r_tab3.update_layout(yaxis_autorange="reversed", xaxis_tickformat = "~%")
			tab3_right_column.plotly_chart(fig_r_tab3, theme="streamlit", use_container_width=True)
		
	example_tweets_expander = st.expander("Positive Tweet Examples")

	with example_tweets_expander:

		column_left_example_tweets, column_right_example_tweets = st.columns(2)

		with column_left_example_tweets:
			count_successful_retrievals_d = 0

			for index, row in df_d_tweets_pos.iterrows():
				tweet_d = format_tweet(url=row["link"], text="text")

				if (tweet_d):
					count_successful_retrievals_d += 1
				
				if count_successful_retrievals_d == 5:
					break
		
		with column_right_example_tweets:
			count_successful_retrievals_r = 0

			for index, row in df_r_tweets_pos.iterrows():
				tweet_r = format_tweet(url=row["link"], text="text")
				
				if (tweet_r):
					count_successful_retrievals_r += 1
				
				if count_successful_retrievals_r == 5:
					break

def show_negative_accounts_by_party(page_options):

	st.header("Most Negative Accounts by Party")
	
	begin_date = f"{page_options['begin_year']}-01-01"
	end_date = f"{page_options['end_year']}-12-31"
	account_types = "'member'" if page_options["show_members_only"] else "'committee', 'member', 'caucus', 'party'"

	df_d_neg = con.execute(f"""--sql
		SELECT
			accounts.name,
			accounts.type,
			AVG(sentiment) AS avg_sentiment,
			SUM(CASE WHEN sentiment <= 0.05 THEN 1 ELSE 0 END) AS count_negative,
			SUM(CASE WHEN sentiment <= 0.05 THEN 1 ELSE 0 END) / COUNT(*) AS pct_negative
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='D'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY accounts.name, accounts.type
	""").df()

	df_r_neg = con.execute(f"""--sql
		SELECT
			accounts.name,
			accounts.type,
			AVG(sentiment) AS avg_sentiment,
			SUM(CASE WHEN sentiment <= 0.05 THEN 1 ELSE 0 END) AS count_negative,
			SUM(CASE WHEN sentiment <= 0.05 THEN 1 ELSE 0 END) / COUNT(*) AS pct_negative
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='R'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		GROUP BY accounts.name, accounts.type
	""").df()

	# Get most negative tweet examples for Democrat accounts
	df_d_tweets_neg = con.execute(f"""--sql
		SELECT DISTINCT
			tweets.sentiment,
			tweets.text,
			tweets.link
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='D'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		ORDER BY tweets.sentiment ASC
		LIMIT 10
	""").df()

	# Get most negative tweet examples for Republican accounts
	df_r_tweets_neg = con.execute(f"""--sql
		SELECT DISTINCT
			tweets.sentiment,
			tweets.text,
			tweets.link
		FROM tweets
			JOIN accounts ON accounts.id = tweets.account_id
		WHERE accounts.party ='R'
			AND tweets.created_at BETWEEN \'{begin_date}\' AND \'{end_date}\'
			AND accounts.type IN ({account_types})
		ORDER BY tweets.sentiment ASC
		LIMIT 10
	""").df()

	tab1, tab2, tab3 = st.tabs(["Average Sentiment", "Count Negative Tweets", "Percentage Negative Tweets"])

	with tab1:
		tab1.subheader("Average Sentiment by Account")

		# Show pie charts of sentimaent breakdown
		tab1_left_column, tab1_right_column = st.columns(2)

		with tab1_left_column:
			fig_d_tab1 = px.bar(
				df_d_neg.sort_values("avg_sentiment", ascending=True)[:10],
				x="avg_sentiment",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"avg_sentiment": "Average Sentiment",
					"name": "Name"
				}
			)
			fig_d_tab1.update_layout(yaxis_autorange="reversed")
			tab1_left_column.plotly_chart(fig_d_tab1, theme="streamlit", use_container_width=True)

		with tab1_right_column:
			fig_r_tab1 = px.bar(
				df_r_neg.sort_values("avg_sentiment", ascending=True)[:10],
				x="avg_sentiment",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"avg_sentiment": "Average Sentiment",
					"name": "Name"
				}
			)
			fig_r_tab1.update_layout(yaxis_autorange="reversed")
			tab1_right_column.plotly_chart(fig_r_tab1, theme="streamlit", use_container_width=True)

	with tab2:
		tab2.subheader("Count Negative Tweets by Account")

		# Show pie charts of sentimaent breakdown
		tab2_left_column, tab2_right_column = st.columns(2)

		with tab2_left_column:
			fig_d_tab2 = px.bar(
				df_d_neg.sort_values("count_negative", ascending=False)[:10],
				x="count_negative",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"count_negative": "Negative Tweets",
					"name": "Name"
				}
			)
			fig_d_tab2.update_layout(yaxis_autorange="reversed")
			tab2_left_column.plotly_chart(fig_d_tab2, theme="streamlit", use_container_width=True)

		with tab2_right_column:
			fig_r_tab2 = px.bar(
				df_r_neg.sort_values("count_negative", ascending=False)[:10],
				x="count_negative",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"count_negative": "Negative Tweets",
					"name": "Name"
				}
			)
			fig_r_tab2.update_layout(yaxis_autorange="reversed")
			tab2_right_column.plotly_chart(fig_r_tab2, theme="streamlit", use_container_width=True)

	with tab3:
		tab3.subheader("Percentage Negative Tweets by Account")
		
		# Show pie charts of sentimaent breakdown
		tab3_left_column, tab3_right_column = st.columns(2)

		with tab3_left_column:
			fig_d_tab3 = px.bar(
				df_d_neg.sort_values("pct_negative", ascending=False)[:10],
				x="pct_negative",
				y="name",
				title="Democrat Accounts",
				color_discrete_sequence=[COLORS["blue"]["primary"]],
				labels={
					"pct_negative": "Negative Percentage",
					"name": "Name"
				}
			)
			fig_d_tab3.update_layout(yaxis_autorange="reversed", xaxis_tickformat = "~%")

			tab3_left_column.plotly_chart(fig_d_tab3, theme="streamlit", use_container_width=True)

		with tab3_right_column:
			fig_r_tab3 = px.bar(
				df_r_neg.sort_values("pct_negative", ascending=False)[:10],
				x="pct_negative",
				y="name",
				title="Republican Accounts",
				color_discrete_sequence=[COLORS["red"]["primary"]],
				labels={
					"pct_negative": "Negative Percentage",
					"name": "Name"
				}
			)
			fig_r_tab3.update_layout(yaxis_autorange="reversed", xaxis_tickformat = "~%")
			tab3_right_column.plotly_chart(fig_r_tab3, theme="streamlit", use_container_width=True)

	example_tweets_expander_neg = st.expander("Negative Tweet Examples")

	with example_tweets_expander_neg:

		column_left_example_tweets, column_right_example_tweets = st.columns(2)

		with column_left_example_tweets:
			count_successful_retrievals_d = 0

			for index, row in df_d_tweets_neg.iterrows():
				tweet_d = format_tweet(url=row["link"], text="text")

				if (tweet_d):
					count_successful_retrievals_d += 1
				
				if count_successful_retrievals_d == 5:
					break
		
		with column_right_example_tweets:
			count_successful_retrievals_r = 0

			for index, row in df_r_tweets_neg.iterrows():
				tweet_r = format_tweet(url=row["link"], text="text")
				
				if (tweet_r):
					count_successful_retrievals_r += 1
				
				if count_successful_retrievals_r == 5:
					break


def main():
	"""
	Main entrypoint for displaying the streamlit page.
	"""

	page_options = {
		"begin_year": "2017",
		"end_year": "2023",
		"show_members_only": False,
	}

	with st.sidebar:
		st.subheader("Filters")
		
		page_options["begin_year"], page_options["end_year"] = st.select_slider(
			":calendar: Select year range",
			options=["2017", "2018", "2019", "2020", "2021", "2022", "2023"],
			value=["2017", "2023"]
		)

		st.write("\n")

		page_options["show_members_only"] = st.checkbox(
			":bust_in_silhouette: Show only member accounts",
			value=False
		)

		st.caption("If enabled, non-member accounts will be removed from the results. This includes party accounts, caucus accounts, etc.")


	st.title("Congress Tweets Sentiment")

	st.write("""
		The following is an exploration into the sentiment of tweets written by members 
		of the US Congress. Tweets from accounts of Congress members, parties, caucuses, 
		and committees were collected between June 2017 and July 2023 and analyzed for
		sentiment using the VADER NLP library. Each tweet's content is given a combined 
		sentiment score between -1 (negative) and 1 (positive). 
	""")

	read_more_expander = st.expander("Acknowledgements")

	with read_more_expander:
		read_more_expander.caption("""
			This exploration would not be possible without the countless hours that went into building the libraries, databases, and tools that it is written on top of. Notably:
			- [VADER-Sentiment-Analysis](https://github.com/cjhutto/vaderSentiment) by [cjhutto](https://github.com/cjhutto): Library for analyzing the sentiment of text using natural language processing with a focus on social media content
			- [Tweets of Congress](https://github.com/alexlitel/congresstweets) by [alexlitel](https://github.com/alexlitel): Database containing millions of tweets from members of congress over the course of 6+ years
			- [Streamlit](https://github.com/streamlit/streamlit) by [Streamlit](https://github.com/streamlit): Library for hosting data applications, what you're looking at right now!
			- [DuckDB](https://github.com/duckdb/duckdb) by [DuckDB](https://github.com/duckdb): An open-source, high-performance database system.
		""")
		read_more_expander.write("\n")

	# Display combined data sections
	show_kpis_combined()
	show_average_sentiment_combined(page_options)

	# Display party split data sections
	show_average_sentiment_by_party(page_options)
	show_pies_by_party(page_options)
	show_positive_accounts_by_party(page_options)
	show_negative_accounts_by_party(page_options)

if __name__ == "__main__":
	main()