import re

def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        print("match Group: ",match.group)
        return extracted_string
    
    return ""

def get_str_from_food_dict(food_dict: dict):

    # converting {'Biryani': 2, 'pizza':1} into
    # 2 Biryani, 2 Pizza using list comprehension

    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])

if __name__ == "__main__":
    print(get_str_from_food_dict({'Biryani':2, 'Pizza':3}))
    #print(extract_session_id('"projects/wiggy-chatbot-cvht/locations/global/agent/sessions/51dbb76a-8555-503a-7669-2fe1a3f20c5b/contexts/ongoing_order"'))