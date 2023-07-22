def check_approved_preflight_cors(event: dict):
    """
    Checks the Preflight message and either silently passes or raises an error
    if not an accepted site.
    """

    # Check dynamo for site names + secret api key name then compare api key
    # to secret. If both pass, then log and move on.
    # else, raise exception

    pass
