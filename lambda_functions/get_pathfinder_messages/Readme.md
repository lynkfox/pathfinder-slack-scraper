## Updating this Lambda for something other than Slack integration

I've tried to keep the Slack integration as a basic module that can eventually be replaced with other ways of getting the data. Be it through Discord channels, actuall pathfinder logs, or even direct access to the database of history

Keep in mind this is designed as a tool to *scrape* the data from a source - not as an active update on trigger of change. That would require more database use.

If you want to substitute in the integration the following things need to be replaced/updated

### slack_integration.py

This controlls the slack integration. So you'll want to swap things out from here with your own implementation

The main lambda index is looking for the following:

* `slack_client_factory(TOKEN)`
: This generates the client for interacting with Slack - replace it with a client factory of whatever you need it to be.

* `get_messages(client, conversation_id, start_timestamp, end_timestamp)`
: this retrieves the messages from the source and outputs a generic list of them. It does not parse them and it does not filter them. It should return a `List[json_like_object]`

* `not_signature_message(message)`
: This is a quick filter during the loop over the message list to skip any that is not a valid log message. it can be removed if you are 100% sure the message list returned by `get_messages` is all messages that need to be parsed as potential sig updates. It can be expanded if you know more ways to filter to increase response times. It could be refactored into a `filter` or `reduce` list comp on the message list itself if you wanted.

* `parse_message(message: Union[SlackMessage, dict], all_scanners: Dict[str, Scanner], all_signatures: Dict[str, Signature], non_valid_sigs: List[str] )`
: This is the meat and potatoes. Right now its working with referenced dicts and updating them as it loops - which is not the most ideal but is slightly faster than using Function Paradigms and returning the message to be reset in the overall dictionary (or building a new dictionary)
: Whatever you replace this with to parse your message should eventually call `update_scanner` and then `update_signature` functions from `sig_and_scanner_parse.py` - which will update the two dictionaries passed by reference with Scanner and Sig objects.

* `scanner_eve_mail_link(name)` expects the passed in name to be in the format of `name #eve_char_id` so like `Luxxianna Seraph #123456789` and will split on the `#` to generate the link. Id recomend the parser concat those two if they are seperate in whatever system is being integrated with.

* I highly recomend you have some form of `not_valid_sigature` that adds the signature name to non_valid_sigs. There is one on Scanner object, btu that could be refactored for better performance. These are the things I have taken into account:
* Remove all Ore type signatures - these are green sigs and dont need to be scanned down
* Remove all Combat Signatures - you can try to filter for scannable ones if you want, and I've tried to but ... its a bit of a pain
* Remove messages that are just the signature being placed before its scanned - in Pathfinder this is just pasting the signature with no information scanned down yet
* Make sure each signature is only counted to a scanner once
* Try to make sure each signature is only counted for the first person who updates it
: I handle this by seeing the first person who changes any of the values of a signature from NULL in pathfinder logs to `anything not null`



* The rest of the functionality of the lambda (output and validation) relies on the Signature and Scanner classes, so once the messages are transformed into them it will continue to work


## Moving to Tripwire or anything not Pathfinder

Besides the above parsing methods needing to be updated for whatever the logs look like in a non Pathfinder situation, you also need to update and/or handle the `class GroupID(Enum)` in `scanner_data.py`  - this is not just a random enum - the numbers are the same that Pathfinder uses for the Group column on sigs (unfortunatly Type is not so easy) - so these will be different depending on how the system logging it maintains what each signature is (data, relic, combat, wormhole, ect)



# Edge Cases Handled:

1) The first person to scan a sig down gets credit:
: this means someone who enters a system and pastes in the sig list but then leaves without scanning does NOT get any credit as they did not update the signature
2) Scanning down a sig entirely before pasting it into Pathfinder still gives credit
3) Green Sigs are *mostly* ignored:
: Combat sites and Ore sites dont require scanning down and so ignored


# Known Issues:

1) Now way to tell how many jumps away from Home system a signature is:
: WHC used to pay out only for sigs scanned within 3 jumps of HomeSystem, on the idea that most people arent going to go that far out. 
: Due to the way Pathfinder logging seems to be so far, there is no indication in the logs which system a given signature belongs to. I can kinda figure out the chain of a system, but honestly I dont want to repeat the wheel here
: Database access *probably* would fix this, as a) a chain of keys could be followed out from or back to Innu and b) there is undoubtedly a 1:many relationship key in a system entry or the sig entry as pathfinder does know what sigs are in what systems - it just doesnt output that to the logs

2) Wormholes are counted twice if the exit hole is updated:
: When a scanner updates a wh, then jumps through if they take the time to scan down and update the exit hole with data, they will recieve credit twice.
: Again, because the logs dont show what system a given sig is in this makes it impossible to tell which sig is which. There is an indication when a scanner links a wormhole to another system in pathfinder, and that *might* be able to be used, but its unreliable

3) Partially Updated sigs are counted as credit:
: If a scanner scans it down enough to know its type, but doesnt finish and doesnt bookmark, the system will still count that as a credit for that scanner.

4) It can be cheated fairly simple by just creating sigs in pathfinder. 
: Yep, this is 100% the case. Honor system. This is also why there is a audit trail. 
: If there is suspicion, comparison to bookmarks and sigs actually in system can be done against the audit trail

5) Some Combat sites may not be attributed to the scanner.
: Its hard to find all the edge cases here. I've done what I can to make sure the scannable Combat Sites in K-Space are captured without doing some crazy hardcoding that would require constant updates whenever CCP changes something. 
: However its still reliant on some pattern matching (Pirate faction names, known formats for scannable DED sites) so if things change...this will no longer work as well.

6) Likewise, New Site Types may get counted for credit even if green
: When pathfinder doesn't recognize a site, it plops the name of the site in the description. This is a perfectly excellent way of handling new sig types that Pathfinder doesnt know about until its updated.
: Unfortunately, that counts as an update to the signature (the desc is not Null when pasted) so it can get counted. Ive tried to accomadate for this as best as possible, but without hardcoding or having acess to a list that can be checked, there are bound to be mis-credits.