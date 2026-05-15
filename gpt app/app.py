from flask import Flask, request, render_template_string, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Configure the Gemini API
genai.configure(api_key='AIzaSyDnQ7TujjQyU4Kjl6o9U7GN2CkzaDOrxX0')

# Store conversation history
conversation_history = {}

# Function to interact with Gemini model with limited tokens
def get_gemini_response(prompt, session_id, model_name="gemini-2.0-flash", max_tokens=300):
    model = genai.GenerativeModel(model_name)
    
    # Get history for this session
    history = conversation_history.get(session_id, [])
    
    # Add user prompt to history
    history.append({"role": "user", "parts": [prompt]})
    
    # Set generation config with max output tokens
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=0.7,
        top_p=0.95,
        top_k=40
    )
    
    # Generate response with limited tokens
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    response_text = response.text
    
    # Add bot response to history
    history.append({"role": "model", "parts": [response_text]})
    
    # Update conversation history
    conversation_history[session_id] = history
    
    return response_text

# Load template from file
with open('index.ejs', 'r') as file:
    TEMPLATE = file.read()

@app.route("/", methods=["GET", "POST"])
def index():
    # Generate a unique session ID (in a real app, use sessions)
    session_id = request.cookies.get('session_id', str(hash(request.remote_addr)))
    
    # Format conversation history for display
    formatted_history = ""
    history = conversation_history.get(session_id, [])
    
    for i in range(0, len(history), 2):
        if i < len(history):
            user_message = history[i]["parts"][0]
            formatted_history += f"""
            <div class="message-group user-message">
                <div class="message-header user-header">
                    <div class="avatar user-avatar">U</div>
                    You
                </div>
                <div class="message-content user-content">{user_message}</div>
            </div>
            """
        
        if i + 1 < len(history):
            bot_message = history[i + 1]["parts"][0]
            formatted_history += f"""
            <div class="message-group bot-message">
                <div class="message-header bot-header">
                    <div class="avatar bot-avatar">G</div>
                    Gemini
                </div>
                <div class="message-content bot-content">{bot_message}</div>
            </div>
            """
    
    # Render the template
    response = render_template_string(
        TEMPLATE, 
        conversation_history=formatted_history
    )
    
    # Set session cookie
    resp = app.make_response(response)
    resp.set_cookie('session_id', session_id)
    
    return resp

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    
    # Get max tokens from request or use default
    max_tokens = data.get("max_tokens", 300)
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    # Get session ID
    session_id = request.cookies.get('session_id', str(hash(request.remote_addr)))
    
    try:
        # Get response from Gemini with limited tokens
        response = get_gemini_response(prompt, session_id, max_tokens=max_tokens)
        
        return jsonify({
            "response": response
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

