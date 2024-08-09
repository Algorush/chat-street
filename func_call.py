import os
import json
import dotenv
import jsonschema
import google.generativeai as genai
from streetmix_schema_params import streetmix_schema


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
        obj_response: JSON object in Streetmix format with street parameters.
    Returns:
        A object in Streetmix format with street parameters.
    """
    # here will be valid JSON checking
    
    return json.dumps(obj_response)


# Model Initialization with Function Call
def init_model_with_function_calls():
    prompt_instructions = load_prompt()
    #streetmix_schema = load_streetmix_schema()
    functions = [
        genai.protos.FunctionDeclaration(
            name="get_street",
            description="Get 3D street (JSON object in Streetmix format) by its textual description",
            parameters=streetmix_schema
        )
    ]
    model = genai.GenerativeModel("gemini-1.5-flash-latest", 
                        system_instruction=prompt_instructions, 
                        tools=functions
                        ) 
    return model


model = init_model_with_function_calls()
chat = model.start_chat(history=[], enable_automatic_function_calling=True)


# Chat Interaction
def chat_with_gemini(user_input):
    response = chat.send_message(user_input)

    # Extract function call and text from response
    fc = response.candidates[0].content.parts[0].function_call
    text = response.candidates[0].content.parts[0].text

    result = {}
    if text:
        result["text"] = text 

    if fc and fc.name == "get_street":
        try:
            streetmix_json = json.loads(fc.parameters)

            # Validation and correction loop
            for attempt in range(3):
                validation_result = validate_streetmix_json(streetmix_json, streetmix_schema)
                if validation_result is True:
                    result["streetmix_json"] = streetmix_json
                    break
                else:
                    print(f"Validation error (attempt {attempt + 1}):", validation_result)
                    correction_request = f"The previous response does not conform to the Streetmix schema. Please correct the following errors and provide a new JSON:\n{validation_result}"
                    correction_response = chat.send_message(correction_request)
                    fc = correction_response.candidates[0].content.parts[0].function_call
                    streetmix_json = json.loads(fc.parameters)
            else:
                result["error"] = "Unable to get a valid Streetmix JSON after multiple attempts. Please try to describe the street another way, with more details."

        except json.JSONDecodeError:
            result["error"] = "Unable to decode JSON."

    return result 