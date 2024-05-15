from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {

}

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    intent_handler_dict={
        'order.add - context:ongoing-order':add_to_order,
        # 'order.remove - context:ongoing-order':remove_from_order,
        'order.complete - context:ongoing-order':complete_order,
        'tracking.order - context:ongoing-tracking':track_order
    }
    return intent_handler_dict[intent](parameters,session_id)

    # if intent == "tracking.order - context:ongoing-tracking":
    #     # return JSONResponse(content={
    #     #     "fulfillmentText": f"Received =={intent}== in the backend"
    #     # })
    #     return track_order(parameters)
    # elif intent == "order.add - context:ongoing-order":
    #     return
    # elif intent == "order.remove - context:ongoing-order":
    #     return
    # elif intent == "order.complete - context:ongoing-order":
    #     return

def add_to_order(parameters:dict,session_id:str):
    food_items = parameters['food-item']
    quantities = parameters['number']

    if len(food_items)!=len(quantities):
        fulfillment_txt = "Sorry I didn't understand.Can you please specify food items and quantity"
    else:
        new_food_dict = dict(zip(food_items,quantities))
        if session_id in inprogress_orders:
            curr_food_dict = inprogress_orders[session_id]
            curr_food_dict.update(new_food_dict)
            inprogress_orders[session_id]=curr_food_dict
        else:
            inprogress_orders[session_id]=new_food_dict
        order_str=generic_helper.get_string_from_food_dict(inprogress_orders[session_id])
        fulfillment_txt = f"So far You have :{order_str}. Do you need anything else?"
    
    return JSONResponse(content={
        "fulfillmentText":fulfillment_txt
    })

def complete_order(parameters:dict,session_id:str):
    if session_id not in inprogress_orders:
        fullfillment_text="I'm having a trouble finding your order.Sorry you can place new order"
    else:
        order = inprogress_orders[session_id]
        save_to_db(order)

def track_order(parameters:dict):
    order_id = parameters['number']
    print(order_id)
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_txt = f"the order status for order id : {order_id} is: {order_status}"
    else:
        fulfillment_txt = f"No order status found for order id : {order_id} "
    return JSONResponse(content={
            "fulfillmentText": fulfillment_txt
        })
