from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

class GroupID(Enum):
    COMBAT = 1
    RELIC = 2
    DATA = 3
    GAS = 4
    WORMHOLE = 5
    ORE = 6
    GHOST = 7



class Scanner(BaseModel):
    name: str
    total_sigs: int
    sigs_updated: List[str]
    

    def scanner_credits(self, sig_name:str, add:bool):
        if add and sig_name not in self.sigs_updated:
            self.sigs_updated.append(sig_name)
        
        if not add and sig_name in self.sigs_updated:
            self.sigs_updated.remove(sig_name)
            
        self.total_sigs = len(set(self.sigs_updated))

    def get_audit(self, all_sigs: List[Signature])-> List[str]:
        return [all_sigs[sig].build_audit() for sig in self.sigs_updated]
            
        

class Signature(BaseModel):
    signature_name: str
    sig_id: str
    first_update_timestamp: float
    original_scanner_name: str
    group_id: Optional[Union[str, int]]
    type_id: Optional[Union[str, int]]
    description: Optional[str]

    def build_audit(self)->str:
        return f"{self.signature_name} {self.sig_id} @ {datetime.fromtimestamp(self.first_update_timestamp)}" +\
        f" [Group: {get_group(self.group_id)}, TypeID: {self.type_id}, Description: {self.description}]"
        


def get_group(group_id):
    try:
        return GroupID(int(group_id)).name
    except:
        return "Unknown"