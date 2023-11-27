import mysql.connector
global cnx

cnx= mysql.connector.connect(
    host= "localhost",
    user= "root",
    password="1234",
    database="pandeyji_eatery" 
)


# Function to call stored procedure and insert an order item
def insert_order_item(food_item, quantity, order_id):
    try:
        # creating a cursor object
        cursor = cnx.cursor()

        #calling the stored procedure
        cursor.callproc("insert_order_item",(food_item, quantity, order_id))

        # commiting the changes
        cnx.commit()

        # close the cursor
        cursor.close()

        print("Order item inserted successfully!")
 
        return 1
    
    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # rolling nack changes if necessary
        cnx.rollback()

        return -1
    
    except Exception as e:
        print(f"An error occurred: {err}")

        # rolling nack changes if necessary
        cnx.rollback()
        
        return -1


# Function to store the order tracking status into order_tracking table
def insert_order_tracking(order_id, status):

    cursor = cnx.cursor()

    # Inserting the record into order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES(%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # commiting the changes
    cnx.commit()

    # closing the cursor
    cursor.close()

# Function to return to total price of order
def get_total_order_price(order_id):

    cursor = cnx.cursor()

    # Executing the SQL query to get the total price of the order
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    result = cursor.fetchone()[0]
    
    cursor.close()
    
    return result


# Function to get the next avilable order_id
def get_next_order_id():

    # create a cursor object
    cursor = cnx.cursor()

    # Executing the query to get the MAX avialable order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)  

    #stroing the max order_id in result
    result = cursor.fetchone()[0]

    # closing the cursor
    cursor.close()

    # returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1

# Function to get the order status from order_tracking table
def get_order_status(order_id: int):

    try:
        # create a cursor object to execute sql queries
        cursor = cnx.cursor()

        # SQL query to retrieve the status for a given order_id
        query = "SELECT status FROM order_tracking WHERE order_id = %s"

        # Execute the query
        cursor.execute(query, (order_id,))
        print('order id: ', order_id)

        # Fetch the result
        result = cursor.fetchone()
        print('result: ', result)

        # Close the cursor
        cursor.close()

        if result is not None:
            print('result[0]: ', result[0])
            return result[0]
        else:
            return None
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# Cancelling the order
def cancel_order(order_id):

    try:
        cursor = cnx.cursor()

        # Deleting items from order table
        delete_items_query = "DELETE FROM orders WHERE order_id = %s"
        cursor.execute(delete_items_query, (order_id,))

        # Deleting order status from order_tracking table
        delete_tracking_query = "DELETE FROM order_tracking WHERE order_id = %s"
        cursor.execute(delete_tracking_query, (order_id,))

        # commiting the changes
        cnx.commit()

        cursor.close()

        print("Order cancelled successfully!")
        
        return 1

    except mysql.connector.Error as err:
        print(f"Error cancelling order: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1
    
    except Exception as e:
        print(f"An error occurred: {e}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1
