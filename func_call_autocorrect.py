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
CREATE_STREET = 'create_street.txt'

def load_file(filename):
    with open(filename, "r") as file:
        return file.read()
    

def load_json_file(filename):
    with open(filename, "r") as file:
        return json.load(file)

validation_streetmix_schema = load_json_file(STREETMIX_SCHEMA_FILENAME)

def validate_streetmix_json(data):
    """Validate data JSON with Streetmix schema.

    Args:
        data: JSON data

    Returns:
        True, if data is valid.
        Otherwise, returns the validation error message as a string.
    """

    try:
        jsonschema.validate(instance=data, schema=validation_streetmix_schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        return False
    
"""
def get_street(obj_response):
    get 3d street (JSON object in Streetmix format with street parameters) by its textual description.
    Args: 
        obj_response: JSON object in Streetmix format with street parameters.
    Returns:
        A object in Streetmix format with street parameters.
    
    # here will be valid JSON checking
    
    return json.dumps(obj_response)
"""

# Model Initialization with Function Call
def init_model_with_function_calls():
    create_street_description = load_file(CREATE_STREET)
    prompt_instructions = load_file(ASSIST_TEXT_FILENAME)
    #streetmix_schema = load_streetmix_schema()
    functions = [
        genai.protos.FunctionDeclaration(
            name="get_street",
            description=create_street_description,
            parameters=streetmix_schema
        )
    ]
    model = genai.GenerativeModel("gemini-1.5-flash-latest", 
                        system_instruction=prompt_instructions, 
                        tools=functions,
                        generation_config=genai.types.GenerationConfig(temperature=0.5)
                        ) 
    return model


model = init_model_with_function_calls()
chat = model.start_chat(history=[], enable_automatic_function_calling=True)

# Chat Interaction
def chat_with_gemini(user_input, image_path=None):
    if image_path:
        with open(image_path, "rb") as image_file:
            image_content = image_file.read()
        response = chat.send_message(user_input, image=image_content)
    else:
        response = chat.send_message(user_input)

    # Extract function call and text from response
    fc = response.candidates[0].content.parts[0].function_call
    text = response.candidates[0].content.parts[0].text

    result = {}
    
    if text:
        result["text"] = text 

    func_data = json.loads(json.dumps(type(fc).to_dict(fc), indent=4))

    print("func_data: ", func_data)
    print("text: ", text)

    if func_data and (func_data['name'] == "get_street"):
        try:
            streetmix_json = func_data['args']
            print("streetmix_json: ", streetmix_json)
            # Validation and correction loop
            for attempt in range(3):
                validation_result = validate_streetmix_json(streetmix_json)
                print("validation_result: ", validation_result)
                if validation_result is True:
                    result["streetmix_json"] = streetmix_json
                    break
                else:  # Validation failed
                    print(f"Validation error (attempt {attempt + 1}):", validation_result)

                    # Ask the model to correct the JSON itself
                    correction_request = (
                        f"The generated JSON does not conform to the Streetmix schema. "
                        f"Please correct the JSON to make it valid according to the schema, "
                        f"and also replace any invalid 'variantString' or segmetn type values with the closest supported ones for their respective segment types. "
                        f"Here's the invalid JSON and the schema:\n\n"
                        f"Invalid JSON:\n{json.dumps(streetmix_json, indent=4)}\n\n"
                        f"Streetmix Schema:\n{json.dumps(streetmix_schema, indent=4)}\n\n"
                        f"Corrected JSON:"
                    )
                    correction_response = chat.send_message(correction_request)
                    print("correction_response: ", correction_response)

                    # Extract the corrected JSON from the response IF it's a function call
                    new_fc = correction_response.candidates[0].content.parts[0].function_call
                    if new_fc and new_fc.name == "get_street":
                        streetmix_json = json.loads(new_fc.arguments)
                    else:
                        # If the model didn't provide a function call, 
                        # it might have provided an explanation or suggestion in the text
                        result["error"] = f"Model was unable to correct the JSON: {correction_response.text}. Please try to describe the street another way, with more details."
                        break  # Exit the loop since we couldn't get a valid JSON

        except json.JSONDecodeError:
            result["error"] = "Unable to decode JSON."

    return result
