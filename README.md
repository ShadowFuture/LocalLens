So basically, this is a simple Flask server created with Python working with a simple HTML and Java template. 
The code takes information from multiple API's such as Open-Meteo(Air Quality Index, Temperature, Wind Speed). Jokes API provides a joke every time it has been called
I also used Ollama's Mistral to answer any person's questions about weather or events based on the information I fed to the AI model

The frontend requests data from Flask routes (/weather, /air, /events, /joke).
The AI assistant sends the user’s question to /assistant, where the backend gathers live data and sends it to an Ollama model running locally to generate a personalized response

To run this program, Install and Run Ollama, Clone this repo, use pip install -r requirements.txt to get all the dependencies and run the server with python app.py in terminal
http://127.0.0.1:5000

