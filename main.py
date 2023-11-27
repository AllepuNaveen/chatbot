from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_conn
import func_file
# creating instance for fastapi
app = FastAPI()

inprogress_orders = {}

@app.post('/')
async def handle_request(request: Request):
    # Retrieve the JSON Response fromm the request
    payload = await request.json()

    # Extract necessary information from the payload (from queryResult : [intent, parameters])
    # which is based on the structure of WebhookRequest of DialogFlow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = func_file.extract_session_id(output_contexts[0]["name"])



    intent_handler_dict = {
        "new_order":new_order,
        "order_add - Context:Ongoing_Order" : add_to_order,
        "order_complete - Context:Ongoing_Order" : complete_order,
        "order_remove - Context:Ongoing_Order" : remove_from_order,
        "track_order - Context:Ongoing_Order" : track_order,
        #"track_order":track_order,
        "cancel_order" : cancel_order,
    }

    return intent_handler_dict[intent](parameters, session_id)



# Function for new order
def new_order(parameters: dict, session_id: str):
    if session_id in inprogress_orders:
        fulfillment_text = "You already have an in-progress order, Please complete or Cancel the above order,"
    
    else:
        fulfillment_text ="Sure! Let's start a new order. What would you like to order?,Also, we have only the following items on our menu: Pav Bhaji, Chole Bhature, Pizza, Mango Lassi, Masala Dosa, Biryani, Vada Pav, Rava Dosa, and Samosa."
        inprogress_orders[session_id] = {}

    return JSONResponse(content={
        "fulfillment_text" : fulfillment_text
    })


# Function to add order items
def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["Food_items"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Please specify the food items and quantity"

    else:
        # merging food_items and quantity to a dictionary
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:

            current_food_dict = inprogress_orders[session_id]
            # updating the current food order/items with new food order/items
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict

        else:
            inprogress_orders[session_id] = new_food_dict

        # returns the order in string format i.e, 2 Masala Dosa, 1 lassi
        order_str = func_file.get_str_from_food_dict(inprogress_orders[session_id])
        
        fulfillment_text = f"You have ordered: {order_str}, Do you need Anything else?"

    return JSONResponse(content={
            'fulfillmentText': fulfillment_text
        })

def save_to_db(order: dict):
    next_order_id = db_conn.get_next_order_id()

    # inserting individual order items along with quantity in order table
    for food_item, quantity in order.items():
        rcode = db_conn.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1
    
    # inserting new order tracking status
    db_conn.insert_order_tracking(next_order_id, 'in progress')

    return next_order_id

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db_conn.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Function to remove items from the order
def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillment_text": "Cannot find your Order, Place a new order"
        })
    food_items = parameters["food_items"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = func_file.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Function to cancel the order
def cancel_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders: #
        fulfillment_text ="I'm having trouble finding your order to cancel. Please make sure you have items in your order."
    
    else:
        order_id = inprogress_orders[session_id]['order_id']

        if order_id:

            # calling the Cancel order function from db.conn
            result = db_conn.cancel_order(order_id)

            if result == 1:
                fulfillment_text = "Your Order has been cancelled"
                # deleting the inprogress session
                del inprogress_orders[session_id]
            
            else:
                fulfillment_text = "Sorry, error occurded while cancelling your order, Please try again!!"
        
        else:
            fulfillment_text = "I'm having trouble finding your order.Please try again."
        
    return JSONResponse(content={
        "fulfillment_text" : fulfillment_text
    })


# Function to track the order
def track_order(parameters: dict, session_id: str):
    order_id = parameters['order_id']
    #order_id = inprogress_orders[session_id].get('order_id')
    order_status = db_conn.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status of Order id: {order_id} is {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
            'fulfillmentText': fulfillment_text
        })