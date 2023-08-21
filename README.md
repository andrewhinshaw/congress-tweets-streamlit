
# Congress Tweets Sentiment

This project is an exploration into the sentiment of tweets written by members of the US Congress. Tweets from accounts of Congress members, parties, caucuses, and committees were collected between June 2017 and July 2023 and analyzed for sentiment using the VADER NLP library. Each tweet's content is given a combined sentiment score between -1 (negative) and 1 (positive).

Data is stored in a DuckDB database for improved retrieval and analysis performance over pandas.

## Filtering

![filtering image](https://i.ibb.co/HrRv6Dz/Screen-Shot-2023-08-20-at-10-24-09-PM.jpg)

Use the filters on the sidebar to adjust the following settings:

- Year range: The range of years to show data for
- Member accounts only: If enabled, non-member accounts will be removed from the results. This includes party accounts, caucus accounts, etc.

## Sections

### Year-To-Date KPIs

This section shows 2023 sentiment data up to July of 2023 compared to the same date range in 2022.

![kpi section](https://i.ibb.co/25J3DYS/Screenshot-2023-08-20-at-22-24-34-app-Streamlit.png)

### Average Sentiment

This section shows the average sentiment by month for both parties combined as well as split out for Republicans and Democrats. A few interesting things to note:

- Sentiment seems to spike regulary around November each year and fall off around January and June.
- While Republicans typiclly trended slightly above Democrats, this flipped after January of 2021.
- Democrats are trending slowly upward between 2017 and today while Republicans are trending downward.
- Republicans reached their highest average sentiment in November 2020 followed closely by their lowest average sentiment in August of 2021.

![combined average sentiment](https://i.ibb.co/dQdNkLt/Screenshot-2023-08-20-at-22-24-53-app-Streamlit.png)

![party average sentiment](https://i.ibb.co/wcth4GF/Screenshot-2023-08-20-at-22-25-09-app-Streamlit.png)

### Sentiment Breakdown

This section shows the percentage breakdown of positive, neutral, and negative tweets for each party. While they are close in aggregate across 2017-2023, adjusting the year range filters shows that these values are more skewed in recent times.

#### 2017-2023

![sentiment breakdown by party 2017-23](https://i.ibb.co/FxvJzQ5/Screenshot-2023-08-20-at-22-25-23-app-Streamlit.png)

#### 2022-2023

![sentiment breakdown by party 2022-23](https://i.ibb.co/7CVN6kK/Screenshot-2023-08-20-at-22-45-24-app-Streamlit.png)

### Most Positive/Negative Accounts

This section shows the most positive and negative accounts for each party. Use the tabs to switch between measurement methods: Average sentiment score, highest percentage of positive/negative tweets, and most positive/negative tweets. Expand the Examples section below the charts for a fun look inside the data used for this analysis!

#### Most Positive Accounts

![most positive accounts](https://i.ibb.co/j3Q6CTg/Screenshot-2023-08-20-at-22-25-35-app-Streamlit.png)

#### Most Negative Accounts

![most negative accounts](https://i.ibb.co/7RJ3cSL/Screenshot-2023-08-20-at-22-26-00-app-Streamlit.png)

## Acknowledgements

This exploration would not be possible without the countless hours that went into building the libraries, databases, and tools that it is written on top of. Notably:

- VADER-Sentiment-Analysis by cjhutto: Library for analyzing the sentiment of text using natural language processing with a focus on social media content
- Tweets of Congress by alexlitel: Database containing millions of tweets from members of congress over the course of 6+ years
- Streamlit by Streamlit: Library for hosting data applications, what you're looking at right now!
- DuckDB by DuckDB: An open-source, high-performance database system.
