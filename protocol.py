# Protocol pentru aplicatia de licitatii
# Mesaje JSON pentru comunicare client-server


LOGIN_REQUEST = {
    "action": "login",
    "username": "string" 
}

ADD_PRODUCT_REQUEST = {
    "action": "add_product",
    "name": "string", 
    "min_price": "int"  
}

BID_REQUEST = {
    "action": "bid",
    "product": "string",  
    "price": "int" 
}


WELCOME_RESPONSE = {
    "type": "welcome",
    "message": "string",
    "products": {
        "nume_produs": {
            "owner": "string",
            "min_price": "int",
            "current_price": "int",
            "bidders": ["string"],
            "active": "bool"
        }
    }
}

ERROR_RESPONSE = {
    "type": "error",
    "message": "string"
}

NOTIFICATION = {
    "type": "notification",
    "message": "string"
}

UPDATE_PRODUCTS = {
    "type": "update",
    "products": {  
    }
}
