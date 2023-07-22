# Statistics Lambda

This is the retrieval lambda for getting back statistics data out of the database.

# General Functionality:

# Through restful API

Using a RESTful Api and keywords/querywords in combination in the api end point (and the fact this lambda is a Proxy connection to API gateway) a query "path" can be used to select the style of responses:

i.e. `/hero/legacy/freedom_five/versus/baron_blade`

This is parsed by the `LookUp` class into a list of `Operation` objects that that are then used to generate a query, as well as maintain an understanding of what was requested for the response.

This version of a look up makes only a single query to the database, a select all where (characters and locations) in the query are found in any of the appropriate columns. The lambda itself then parses this response using py-Linq (C# LINQ style notation for manipulating enumerable objects) to determine the necessary data - such as TotalGames (count), TotalPlayerWins (where end_result is a Player Win Condition) and a few other basic statistics.

The generation of the `StatisticsResults` object also generates a series of links for other characters that can continue drilling down into more detailed sets of data.


# Through a JSON object

**Future Implementation**

A Json payload can also be set directly to `statistics/` and it will arrive here, giving the end user a way to make more detailed queries of the statistics data that may look up additional information rather than just the Win/Loss/Incapacitated data.
