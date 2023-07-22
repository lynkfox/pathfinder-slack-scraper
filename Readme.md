# Automatic recording of Scanner credit in Eve Online

the Wormhole Community (WHC) of Eve Uni pays its scanners. For each site scanned down in the Wormhole chain, scanners are paid based on how much isk was farmed by other members of the wormhole, proportional to the amount they scanned.

This tool is a dirty hack to help automate that. It works, but is not a great long term solution for Eve Uni

## What you need:

* AWS Account
* Slack Account
* Slack App integration and its Token
* Pathfinder
* AWS CDK
  * which requires node and npm
* Python 3.10

## Installation

1. Create a slack channel for the pathfinder logs
2. Add the webhook for the slack to the Pathfinder map output.
3. Create a slack App and get its token
4. Add the slack app token to config.json under "token" as a top level key.
5. Install the pip requirements file
6. Install AWS CDK
7. Bootstrap your aws environment
8. Run cdk deploy from the root of the project
  * this will deploy the stack - lambda and api gateway - to your aws account, and output the endpoint http address. 
9. go to  `[your endpoint]/prod/v1/thisweek` for getting the most recent information. 

It pulls via weeks, from Monday 00:00 UTC to Sunday 23:59: UTC.

- prod/v1/thisweek -> get the current week
- prod/v1/lastweek -> get last week
- prod/v1/-1 -> any negative number, get that many weeks ago
- prod/v1/29 -> any positive number, get that week of this year. 