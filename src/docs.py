# -*- coding: utf-8 -*-
#
# src/docs.py
#

class Doc:

    def __init__(self, summary, code, returns, notes):
        self.summary = summary
        self.code = code
        self.returns = returns
        self.notes = notes


def get_documentation():
    return [
        Doc("CheckIn", "/station/checkin?barcode=<barcode>",
            returns="Returns Links",
            notes=["This checks the specified barcode into the building, if "
                   "already checked in then it does nothing.",
                   "If you are the first keyholder checking in, it will make "
                   "you the keyholder."]),
        Doc("CheckOut", "/station/checkout?barcode=<barcode>",
            returns="Returns Links",
            notes=["This checks the specified barcode out of the building, if "
                   "already checked out then it does nothing.",
                   "If you are the active keyholder and you checkout AND you "
                   "are not the only one in the building then you will "
                   "get a list of people who are in the building and a chance "
                   "to checkout or cancel. (In 30 seconds it will cancel on "
                   "its own.)"]),
        Doc("Make New Keyholder", "/station/make_keyholder?barcode=<barcode>",
            returns="Returns the station webpage",
            notes=["This makes the given barcode the active keyholder. If "
                   "that barcode was not checked in, it also checks it in."]),
        Doc("Links", "/links[?barcode=<barcode>]",
            returns="Returns a webpage",
            notes=["This shows a list of links that that barcode might find "
                   "useful based off their role.",
                   "If the barcode is left off, it is a list of links for "
                   "display stations."]),
        Doc("Unlock", "/unlock?location=TFI&barcode=<barcode>",
            returns="Returns the station webpage",
            notes=["This records that the door was unlocked and checks in the "
                   "person that unlocks the door. For use with the door app "
                   "ONLY"]),
        Doc("Get Keyholder list", "/admin/get_keyholder_json",
            returns="Encrypted JSON",
            notes=["This is how the doorapp gets the updated list. It is "
                   "encrypted using Fernet (symmetric) encryption with a 32 "
                   "byte key that both the doorapp and checkmeIn share.",
                   "Not useful except for the doorapp."])
        ]
