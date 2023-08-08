from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum
from helpers import create_unique_sig_name
from math import floor

class GroupID(Enum):
    UNKNOWN = 0
    COMBAT = 1
    RELIC = 2
    DATA = 3
    GAS = 4
    WORMHOLE = 5
    ORE = 6
    GHOST = 7

# Ore description values that may show up as UNKNOWN group type

class Scanner(BaseModel):
    name: str
    total_sigs: int
    sigs_updated: List[Signature]
    valid_sig_audit: List[str]
    non_valid_sig_audit: List[str]
    

  
    

    def scanner_credits(self, sig:Signature, add:bool):
        if add and sig not in self.sigs_updated:
            self.sigs_updated.append(sig)
        
        if not add and sig in self.sigs_updated:
            self.sigs_updated.remove(sig)
        

    def get_audit(self, include_invalid:bool=False)-> List[str]:
        audit = { "valid_sigs": self.valid_sig_audit}
        if include_invalid:
            audit["non_valid_sigs"] = self.non_valid_sig_audit
        return audit
            
    def filter_non_valid_sigs(self, not_valid_sigs):
        self.valid_sig_audit = []
        self.non_valid_sig_audit = []
        for sig in self.sigs_updated:
            try:
                group = GroupID(int(sig.group_id))
            except:
                group = GroupID(0)
            
            log_entry = sig.build_audit()

            if group in [GroupID.ORE] or (sig.description is not None and "Deposit" in sig.description):
                self.non_valid_sig_audit.append(log_entry+f"#Reason: Green Ore Sig")
            elif group in [GroupID.UNKNOWN, GroupID.COMBAT] and sig.description in [None, "", " "]:
                self.non_valid_sig_audit.append(log_entry+f"#Reason: Not Scanned Down")
            elif create_unique_sig_name(sig.name, sig.id) in not_valid_sigs:
                self.non_valid_sig_audit.append(log_entry+f"#Reason: Flagged as Not Valid sig")
            else:
                self.valid_sig_audit.append(sig.build_audit())

        self.total_sigs = len(self.valid_sig_audit)

class Signature(BaseModel):
    name: str
    id: str
    first_update_timestamp: str
    original_scanner_name: str
    group_id: Optional[Union[str, int]]
    type_id: Optional[Union[str, int]]
    description: Optional[str]

    def build_audit(self)->str:
        date_time = datetime.fromtimestamp(float(self.first_update_timestamp))
        return f"{self.name} {self.id} @ {date_time}[{self.first_update_timestamp}]" +\
        f" [Group: {get_group(self.group_id)}, TypeID: {self.type_id}, Description: {self.description}]"
        

    def __hash__(self):
        return hash(self.build_audit())
    
    def __eq__(self, other):
        if type(other) == Signature:
            return self.build_audit() == other.build_audit()
        else:
            raise ValueError(f"Cannot compare Siganture to {type(other)}")

def get_group(group_id):
    try:
        return GroupID(int(group_id)).name
    except:
        return GroupID.UNKNOWN.name
    
def scanner_eve_mail_link(name)-> str:
    name_and_id = name.split("#")
    eve_id = name_and_id[1].strip()
    char_name = name_and_id[0].strip()

    return f"<url=showinfo:1377//{eve_id}>{char_name}</url>"


def scanner_payout(per_sig:float, scanners_sigs:int) -> int:
    if per_sig <=0:
        return scanners_sigs
    
    return int(floor(float(per_sig) * int(scanners_sigs)))