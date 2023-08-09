from models.scanner_data import Signature, Scanner
from aws_lambda_powertools import Logger


logger = Logger()

def update_signatures(all_scanners, all_signatures, sig_name, sig_id, scanner_name, unique_sig_name, timestamp, group_id, type_id, description):
    """
    update_signatures will take the values extracted from a message and either create the signature if it does not exist or update an existing one with new values.

    it will also update the scanner involved if it is a new signature, and if it is an existing signature it will update scanners if the message timestamp is earlier than
    the currently recorded one.
    """
    if unique_sig_name not in all_signatures.keys():
        sig = Signature(
                name=sig_name,
                id=sig_id,
                first_update_timestamp=timestamp,
                original_scanner_name=scanner_name,
                group_id=group_id,
                type_id=type_id,
                description=description
            )
        

        all_signatures[unique_sig_name] = sig
        all_scanners[scanner_name].scanner_credits(sig, add=True)
        

    else:

        all_signatures[unique_sig_name] = update_sig_if_older(all_scanners, scanner_name, timestamp, all_signatures[unique_sig_name])
        if group_id is not None:
            all_signatures[unique_sig_name].group_id = group_id
        if type_id is not None:
            all_signatures[unique_sig_name].type_id = type_id
        if description is not None:
            all_signatures[unique_sig_name].description = description
        
        sig = all_signatures[unique_sig_name]

    logger.debug(f"{unique_sig_name} Updated", extra=sig.model_dump(mode="JSON"))
    return sig
    

def update_sig_if_older(all_scanners, scanner_name, timestamp, existing_sig):
    """
    update_sig_if_older checks to see if the signature that is already recorded as a scanner credit, if its timestamp is newer than the message being parsed.
    if so, the scanner credit is updated.
    """
    if timestamp < existing_sig.first_update_timestamp:
        original_scanner = existing_sig.original_scanner_name
        if original_scanner != scanner_name:
            all_scanners[scanner_name].scanner_credits(existing_sig, add=True)
            all_scanners[original_scanner].scanner_credits(existing_sig, add=False)
        existing_sig.first_update_timestamp = timestamp
    return existing_sig

def update_scanner(all_scanners, scanner_name):
    if scanner_name not in all_scanners.keys():
        scanner = Scanner(
                name=scanner_name,
                sigs_updated=[],
                total_sigs=0,
                valid_sig_audit = [],
                non_valid_sig_audit = []
            )
        all_scanners[scanner_name] = scanner
        return
        
    else:
        return