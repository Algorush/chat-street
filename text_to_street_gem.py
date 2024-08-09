import os
import json
import dotenv
import jsonschema
import google.generativeai as genai


config = dotenv.dotenv_values(".env")
#  OPENAI_API_KEY. API Gemini 
os.environ["GEMINI_API_KEY"] = config['GEMINI_API_KEY']
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

ASSIST_TEXT_FILENAME = 'prompt_bot.txt'
STREETMIX_SCHEMA_FILENAME = 'streetmix_schema.json'

def load_prompt():
    with open(ASSIST_TEXT_FILENAME, "r") as file:
        return file.read()
    

def load_streetmix_schema():
    with open(STREETMIX_SCHEMA_FILENAME, "r") as file:
        return json.load(file)

streetmix_schema = load_streetmix_schema()


def validate_streetmix_json(data, schema):
    """Validate data JSON  with Streetmix schema.

    Args:
        data: JSON data
        schema: schema Streetmix

    Returns:
        True, if data is valid
        False, if data is invalid
    """

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"Validation error: {e}")
        return False
    

def get_street(obj_response):
    """get 3d street (JSON object in Streetmix format with street parameters) by its textual description.
    Args: 

    Returns:
        A object in Streetmix format with street parameters.
    """
    # here will be valid JSON checking
    print("get_street")
    return json.dumps(obj_response)


def init_model_with_json_output():
    prompt_instructions = load_prompt()
    
    model = genai.GenerativeModel('gemini-1.5-flash-latest', 
                                system_instruction=prompt_instructions,
                                # Set the `response_mime_type` to output JSON
                                # Pass the schema object to the `response_schema` field
                                generation_config={"response_mime_type": "application/json",
                                                    "response_schema": streetmix_schema})
    return model


# Chat Interaction
def chat_with_gemini():
    model = init_model_with_json_output()
    chat = model.start_chat(history=[])
    while True:
        user_input = input("Describe a street (or type 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        response = chat.send_message(user_input)

        try:
            streetmix_json = json.loads(response.text)
            validation_result = validate_streetmix_json(streetmix_json, streetmix_schema)
            if validation_result is True:
                print("Streetmix JSON:", json.dumps(streetmix_json, indent=4))
            else:
                max_attempts = 2
                for attempt in range(max_attempts):
                    print(f"Validation error (attempt {attempt + 1}):", validation_result)
                    correction_request = f"Previous response does not correspond to the Streetmix schema. Please correct the following errors and provide a new JSON:\n{validation_result}"
                    correction_response = chat.send_message(correction_request)
                    streetmix_json = json.loads(correction_response.text)
                    validation_result = validate_streetmix_json(streetmix_json, streetmix_schema)
                    if validation_result is True:
                        print("Corrected Streetmix JSON:", json.dumps(streetmix_json, indent=4))
                        break  # Выходим из цикла, если данные валидны
                else:
                    print("Error: Unable to get a valid Streetmix JSON after multiple attempts.")
        except json.JSONDecodeError:
            print("Error: Unable to decode JSON.")
