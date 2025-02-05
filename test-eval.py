import dash
from dash import dcc, html, Input, Output, State
import INSPECTA_Dog_cmd_util # This is the file where your get_args() is defined
from INSPECTA_Dog_cmd_util import *
# --- Global configuration dictionary ---
# This dictionary holds your copilot variables (configuration) that are initially set by get_args()
copilot_config = {
    "working_dir": None,
    "start_file": "Car.aadl",
    "counter_example": "",
    "requirement_file": None,
}

# Initialize the configuration using your get_args() function.
# (This only happens when the app first loads.)
args = get_args()
copilot_config["working_dir"] = args.working_dir
copilot_config["start_file"] = args.start_file
copilot_config["counter_example"] = args.counter_example
copilot_config["requirement_file"] = args.requirement_file

# --- Dash Application Layout ---
app = dash.Dash(__name__)

app.layout = html.Div([
    # A Store component to keep conversation history between callbacks.
    dcc.Store(id="conversation-history", data=[]),

    # Some UI for your copilot conversation (chat history, etc.)
    html.Div(id="chat-window"),

    # The Update button for refreshing configuration from the command-line
    html.Button("Update Copilot Variables", id="update-config-btn"),

    # A status message to confirm the update
    html.Div(id="update-status")
])


# --- Callback to update configuration variables without losing conversation history ---
@app.callback(
    Output("update-status", "children"),
    Input("update-config-btn", "n_clicks"),
    State("conversation-history", "data")
)
def update_config(n_clicks, conversation_history):
    if n_clicks:
        # Read the (possibly updated) command-line arguments:
        new_args = get_args()

        # Update the global configuration without resetting the conversation history.
        copilot_config["working_dir"] = new_args.working_dir
        copilot_config["start_file"] = new_args.start_file
        copilot_config["counter_example"] = new_args.counter_example
        copilot_config["requirement_file"] = new_args.requirement_file

        # You can add logging here to inspect the new configuration:
        print("Updated copilot configuration:")
        print(copilot_config)

        # Return a confirmation message to the user.
        return "Copilot variables updated successfully!"
    return "Click the button to update configuration variables."


# --- (Other callbacks for your chat / copilot functionality would go here) ---

if __name__ == '__main__':
    app.run_server(debug=True)
