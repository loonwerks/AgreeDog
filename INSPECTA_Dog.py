# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTA_Dog copilot - ChatCompletion, and Multi-Modal Mode.
Date: 1st July 2024
"""
import os

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import openai
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
import zipfile
import base64
import json
import warnings
import time
import threading
from flask import request  # Import Flask's request

# Utility imports
import INSPECTA_Dog_cmd_util
import INSPECTA_dog_system_msgs
from INSPECTA_Dog_cmd_util import *
from git_actions import *

# Ensure necessary directories exist
directories = ["conversation_history", "temp_history", "shared_history", "counter_examples", "proof_analysis"]
INSPECTA_Dog_cmd_util.ensure_writable_directories(directories)

# Parse command-line arguments
args = INSPECTA_Dog_cmd_util.get_args()

# After loading environment variables, modify how openai.api_key is set:
if args.user_open_api_key:
    openai.api_key = args.user_open_api_key
else:
    load_dotenv(find_dotenv())
    openai.api_key = os.getenv('OPENAI_API_KEY')

# -------------------- Process sys-requirement.txt File --------------------
requirements_content = ""

def req_content():
    global requirements_content
    if args.requirement_file:
        requirement_path = args.requirement_file
        if os.path.isfile(requirement_path):
            print(f"Requirement file provided: {requirement_path}")
            try:
                with open(requirement_path, 'r') as f:
                    requirements_content = f.read()
                print("Contents of requirement.txt:")
                print(requirements_content)
                content = requirements_content
                return content
            except Exception as e:
                print(f"Error reading requirement file: {e}")
        else:
            print(f"Requirement file not found at: {requirement_path}")
    else:
        print("No requirement.txt file provided.")
        return "No requirement.txt file provided."

req_content()
requirements_file_content = requirements_content

# -------------------- Dash App Setup --------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Add components to the layout for displaying the token count and timer
token_display = html.Div(id='token-count', style={"margin-top": "20px"})
timer_display = html.Div(id='timer-display', style={"margin-top": "20px"})

gear_button = dbc.Button(
    [
        html.I(className="fa fa-cog", style={"margin-right": "5px"})
    ],
    id="gear-button",
    color="secondary",
    style={"display": "inline-block", "vertical-align": "middle"}
)

shutdown_button = dbc.Button(
    [
        html.I(className="fa fa-power-off", style={"margin-right": "5px"}),
        "Shutdown Server"
    ],
    id="shutdown-button",
    color="danger",
    className="ml-3",
    style={"display": "inline-block", "vertical-align": "middle"}
)

app.layout = dbc.Container([
    # Example "Footer" or other elements here, if needed

    # -------------------- Header with dog image & text on the left, Collins on the right --------------------
    html.Div([
        html.Div([
            # Sub-Div for dog icon + "AGREE-Dog" text on the left
            html.Div([
                html.Img(
                    src="assets/coqdog-5.png",
                    id="app-logo",
                    style={
                        "height": "70px",
                        "vertical-align": "middle"
                    }
                ),
                html.H1(
                    "AGREE-Dog",
                    #style={
                    #    "margin-left": "20px",
                    #    "vertical-align": "middle"
                    #}
                    style={
                        "font-family": "Arial, Helvetica",  # Modern sans-serif fonts
                        "font-weight": "bold",  # Makes the text bold
                        "font-size": "40px",  # Adjust the font size as needed
                        "margin-left": "20px",  # Optional for alignment or spacing
                        "vertical-align": "middle"
                    }
                )
            ], style={
                "display": "flex",
                "align-items": "center"
            }),

            # The Collins logo on the right
            html.Img(
                src="assets/collins_logo.png",
                id="collins-logo",
                style={
                    "height": "70px",
                    "width": "250px",
                    "vertical-align": "middle"
                }
            )
        ], style={
            # Outer flex container to push left item to left, Collins to right
            "display": "flex",
            "align-items": "center",
            "justify-content": "space-between",
            "margin-bottom": "5px"
        })
    ]),

    # -------------------- Settings Menu --------------------
    html.Div(
        id='system-message-menu',
        style={"display": "none", "margin-bottom": "20px"},
        children=[
            dcc.RadioItems(
                id='system-message-choice',
                options=[
                    {"label": "JKind SMTSolvers AI selector", "value": "Enable JKind SMTSolvers selector", "disabled": True},
                    {"label": "AgreeDog System Message", "value": "AgreeDog"}
                ],
                value="AgreeDog"
            ),
            dbc.Button(
                [
                    html.I(className="fa fa-check", style={"margin-right": "5px"}),
                    "Confirm Selection"
                ],
                id='confirm-system-message-button',
                color="primary",
                className="mr-1"
            ),
            html.Hr(),

            # Additional radio items...
            dcc.RadioItems(
                id='include-upload-folder',
                options=[
                    {"label": "Load additional context", "value": "yes"},
                    {"label": "Use Osate2", "value": "no"},
                ],
                value="no",
                inline=True,
                style={"margin-top": "10px"}
            ),
            dcc.RadioItems(
                id='include-requirements-chain',
                options=[
                    {"label": "Include import chain", "value": "yes"},
                    {"label": "Don't include import chain", "value": "no"},
                ],
                value="no",
                inline=True,
                style={"margin-top": "10px"}
            ),
            dbc.RadioItems(
                id="model-choice",
                options=[
                    {"label": "GPT-4o multi-modal (128k tk)", "value": "gpt-4o"},
                    {"label": "GPT-4-Turbo (128k tk)", "value": "gpt-4-turbo"},
                    {"label": "GPT-4 (8k tk)", "value": "gpt-4-0613", "disabled": True},
                ],
                value="gpt-4o",
                inline=True,
                style={"margin-top": "10px"}
            ),
            dbc.RadioItems(
                id="display-mode",
                options=[
                    {"label": "Full History", "value": "full"},
                    {"label": "Last Response", "value": "last"},
                ],
                value="last",
                inline=True,
                style={"margin-top": "10px"}
            ),

            # Radio for enabling Git push
            dbc.RadioItems(
                id='enable-git-push',
                options=[
                    {"label": "Enable Git push", "value": "yes"},
                    {"label": "Disable Git push", "value": "no"},
                ],
                value="no",
                inline=True,
                style={"margin-top": "10px"}
            ),

            html.Hr(),
            shutdown_button
        ]
    ),

    # -------------------- Main Textarea & Buttons --------------------
    dcc.Textarea(
        id='user-input',
        style={"width": "100%", "height": 200},
        placeholder='Enter your context...'
    ),

    # The "Enter the start file" input – initially hidden
    html.Div(
        id='initial-file-div',
        style={"display": "none"},
        children=[
            dbc.Input(
                id='initial-file',
                placeholder='Enter the start file (e.g., file_name)',
                type='text',
                style={"margin-top": "10px"}
            )
        ]
    ),

    html.Div([
        dbc.Button(
            [
                html.I(className="fa fa-paper-plane", style={"margin-right": "2px"}),
                "Submit"
            ],
            id='submit-button',
            color="primary",
            style={"margin-right": "2px"}
        ),
        dbc.Button(
            [
                html.I(className="fa fa-save", style={"margin-right": "2px"}),
                "Save"
            ],
            id='copy-button',
            color="secondary",
            style={"margin-right": "2px"}
        ),
        gear_button,

        html.Div(
            id='upload-folder-div',
            style={"display": "none", "margin-left": "2px"},
            children=[
                dcc.Upload(
                    id='upload-folder',
                    children=dbc.Button(
                        [
                            html.I(className="fa fa-upload", style={"margin-right": "2px"}),
                            "Upload Folder"
                        ],
                        color="secondary"
                    ),
                    multiple=False
                )
            ]
        )
    ], style={"display": "flex", "align-items": "center", "margin-top": "10px"}),

    html.Div(id='upload-status', style={"margin-top": "10px"}),
    html.Div(id='copy-status', style={"margin-top": "10px"}),
    html.Div(id='response-output', style={"white-space": "pre-line", "margin-top": "20px"}),

    # Hidden placeholders
    html.Div(
        id='conversation-history',
        style={'display': 'none'},
        children="[]"
    ),
    html.Div(
        id='context-added',
        style={'display': 'none'},
        children="false"
    ),

    token_display,
    timer_display,

    # Git commit field
    html.Div(
        id='git-commit-div',
        style={"display": "none"},
        children=[
            dbc.Input(
                id='commit-message',
                placeholder='Enter commit message',
                type='text',
                style={"margin-top": "20px"}
            ),
            dbc.Button(
                [
                    html.I(className="fab fa-github", style={"margin-right": "5px"}),
                    "Git Commit and Push"
                ],
                id='git-commit-push',
                color="success",
                className="mr-1"
            ),
            html.Div(id='push-status', style={"margin-top": "20px"}),
        ]
    ),

    dbc.Modal([
        dbc.ModalHeader("Confirm Shutdown"),
        dbc.ModalBody("Are you sure you want to shut down the server? This action cannot be undone."),
        dbc.ModalFooter([
            dbc.Button(
                [
                    html.I(className="fa fa-check", style={"margin-right": "5px"}),
                    "Yes, Shutdown"
                ],
                id="confirm-shutdown",
                color="danger"
            ),
            dbc.Button("Cancel", id="cancel-shutdown", className="ml-2")
        ])
    ], id="shutdown-modal", is_open=False),

    html.Div(id='shutdown-status', style={"margin-top": "10px", "color": "red"}),

], fluid=True)

# -------------------- Global Timer Variables --------------------
total_api_time = 0
time_frames = []
start_time = None
elapsed_time = timedelta(0)
formatted_elapsed_time = "00:00:00.00"

# -------------------- Callbacks --------------------
@app.callback(
    Output('system-message-menu', 'style'),
    Input('gear-button', 'n_clicks'),
    State('system-message-menu', 'style'),
    prevent_initial_call=True
)
def toggle_system_message_menu(gear_clicks, style):
    if not gear_clicks:
        return style
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style

@app.callback(
    Output('upload-folder-div', 'style'),
    Input('include-upload-folder', 'value'),
    prevent_initial_call=True
)
def toggle_upload_folder_div(include_upload):
    if include_upload == "yes":
        return {"display": "block", "margin-left": "10px"}
    return {"display": "none"}

@app.callback(
    Output('initial-file-div', 'style'),
    Input('include-upload-folder', 'value'),
    prevent_initial_call=True
)
def toggle_initial_file_div(include_upload):
    if include_upload == "yes":
        return {"display": "block", "margin-top": "10px"}
    return {"display": "none"}

@app.callback(
    Output('git-commit-div', 'style'),
    Input('enable-git-push', 'value'),
    prevent_initial_call=True
)
def toggle_git_commit_div(enable_git_push):
    if enable_git_push == "yes":
        return {"display": "block", "margin-top": "10px"}
    return {"display": "none"}

@app.callback(
    [
        Output('conversation-history', 'children'),
        Output('response-output', 'children'),
        Output('user-input', 'value'),
        Output('token-count', 'children'),
        Output('timer-display', 'children'),
        Output('context-added', 'children')
    ],
    [
        Input('confirm-system-message-button', 'n_clicks'),
        Input('submit-button', 'n_clicks')
    ],
    [
        State('system-message-choice', 'value'),
        State('conversation-history', 'children'),
        State('context-added', 'children'),
        State('model-choice', 'value'),
        State('display-mode', 'value'),
        State('user-input', 'value'),
        State('initial-file', 'value'),
        State('include-requirements-chain', 'value'),
        State('include-upload-folder', 'value')
    ]
)
def handle_app_interactions(confirm_n_clicks,
                            submit_n_clicks,
                            system_message_choice,
                            conversation_history_json,
                            context_added,
                            model_choice,
                            display_mode,
                            user_input,
                            initial_file,
                            include_requirements_chain,
                            include_upload_folder):
    global start_time, elapsed_time, formatted_elapsed_time, time_frames, total_api_time
    time_frames.append(elapsed_time)
    reset_timer_variables()

    ctx = dash.callback_context
    if not ctx.triggered:
        triggered_id = 'No clicks yet'
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    conversation_history = json.loads(conversation_history_json)

    if triggered_id == 'confirm-system-message-button' and confirm_n_clicks is not None:
        ch_json, resp, usr_val, tkn_count, tmr_display = set_system_message(conversation_history, system_message_choice)
        return ch_json, resp, usr_val, tkn_count, tmr_display, context_added

    elif triggered_id == 'submit-button' and submit_n_clicks is not None:
        if start_time is None:
            start_time = datetime.now()

        if submit_n_clicks is None:
            return (
                conversation_history_json,
                "Enter your context and press 'Submit'.",
                user_input,
                f"Tokens used: {0}",
                f"Elapsed Time: {formatted_elapsed_time}",
                context_added
            )

        if not conversation_history:
            conversation_history = [
                {'role': 'system', 'content': INSPECTA_dog_system_msgs.AGREE_dog_sys_msg}
            ]
            context_added = "false"

        upload_directory = get_resource_path("uploaded_dir")
        subdirectories = [
            os.path.join(upload_directory, d)
            for d in os.listdir(upload_directory)
            if os.path.isdir(os.path.join(upload_directory, d))
        ]
        if include_upload_folder == "yes" and not subdirectories:
            return (
                conversation_history_json,
                "No subdirectory found in the uploaded directory.",
                user_input,
                f"Tokens used: {0}",
                f"Elapsed Time: {formatted_elapsed_time}",
                context_added
            )

        if INSPECTA_Dog_cmd_util.get_args().working_dir is not None:
            args_local = INSPECTA_Dog_cmd_util.get_args()
            target_directory = args_local.working_dir
            if args_local.start_file is not None:
                initial_file = args_local.start_file
        else:
            target_directory = subdirectories[0] if subdirectories else ""
            print("Target directory:", target_directory)

        project_files = read_project_files(target_directory)

        if context_added == "false":
            if (include_requirements_chain == "yes" and initial_file and include_upload_folder == "no"):
                initial_file = remove_file_ext_from_cmd_like_ui(initial_file)
                file_context = concatenate_imports(
                    initial_file,
                    project_files,
                    target_directory,
                    include_requirements_chain,
                    include_upload_folder,
                    context_added
                )
                if file_context and INSPECTA_Dog_cmd_util.get_args().counter_example is not None:
                    cex_path = INSPECTA_Dog_cmd_util.get_args().counter_example
                    cex = read_counter_example_file(cex_path)
                    prompt = set_prompt(file_context, cex)
                    user_input = f"{prompt}\n{user_input}"
                context_added = "true"

            elif (include_requirements_chain == "no" and initial_file and
                  include_upload_folder == "no" and context_added == "false" and
                  INSPECTA_Dog_cmd_util.get_args().counter_example is not None):
                cex_path = INSPECTA_Dog_cmd_util.get_args().counter_example
                cex = read_counter_example_file(cex_path)
                start_file_with_ext = INSPECTA_Dog_cmd_util.get_args().start_file
                working_dir = INSPECTA_Dog_cmd_util.get_args().working_dir
                start_file_path = os.path.join(working_dir, start_file_with_ext)
                start_file_content = read_start_file_content(start_file_path)
                prompt = set_prompt(start_file_content, cex)
                user_input = f"{prompt}\n{user_input}"
                context_added = "true"

            elif (include_requirements_chain == "no" and initial_file and include_upload_folder == "yes"):
                pass

        if requirements_file_content:
            requirements_hint = (
                "When you modify the code or try to write the fixed code, "
                "consider the following requirements and make sure your modifications "
                "don't break them:\n" + requirements_file_content
            )
            user_input = f"\n{user_input}"
            print("Integrated requirements.txt content into user input.")

        conversation_history.append({'role': 'user', 'content': user_input})
        response_obj = get_completion_from_messages(conversation_history, model=model_choice)
        response = response_obj.choices[0].message["content"]
        tokens_used = response_obj['usage']['total_tokens']

        conversation_history.append({'role': 'assistant', 'content': response})
        save_conversation_history_to_file(conversation_history)
        display_text = format_display_text(conversation_history, display_mode)
        warning = token_warning(model_choice, tokens_used)
        total_time_display = total_timedisplay(start_time, time_frames, total_api_time)

        return (
            json.dumps(conversation_history),
            display_text,
            "",
            f"Tokens used : {tokens_used}" + warning,
            total_time_display,
            context_added
        )

    return (
        conversation_history_json,
        "",
        user_input,
        "Tokens used: 0",
        f"Elapsed Time: {formatted_elapsed_time}",
        context_added
    )

@app.callback(
    Output("shutdown-modal", "is_open"),
    [
        Input("shutdown-button", "n_clicks"),
        Input("confirm-shutdown", "n_clicks"),
        Input("cancel-shutdown", "n_clicks")
    ],
    [State("shutdown-modal", "is_open")],
)
def toggle_modal(shutdown_click, confirm_click, cancel_click, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "shutdown-button" and shutdown_click:
        return True
    elif button_id in ["confirm-shutdown", "cancel-shutdown"]:
        return False
    return is_open

@app.callback(
    Output('shutdown-status', 'children'),
    Input('confirm-shutdown', 'n_clicks'),
    prevent_initial_call=True
)
def shutdown_server(n_clicks):
    if n_clicks:
        def force_shutdown():
            os._exit(0)
        thread = threading.Thread(target=force_shutdown)
        thread.start()
        return "Server is shutting down immediately..."
    return ""

@app.callback(
    Output('copy-status', 'children'),
    Input('copy-button', 'n_clicks'),
    State('conversation-history', 'children'),
    prevent_initial_call=True
)
def copy_conversation_history(n_clicks, conversation_history_json):
    global total_api_time
    if n_clicks is None:
        return "Click the button to copy the conversation history."

    total_time_display = f"Total API Call Time: {total_api_time:.2f} seconds"
    conversation_history = json.loads(conversation_history_json)
    conversation_history.append({'role': 'system', 'content': total_time_display})

    source_file = 'conversation_history/conversation_history.json'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_dir = 'temp_history'
    destination_file = f'{destination_dir}/conversation_history_{timestamp}.json'

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    with open(destination_file, 'w') as file:
        json.dump(conversation_history, file, indent=4)

    return f"Successfully copied to {destination_file}"

@app.callback(
    Output('upload-status', 'children'),
    [Input('upload-folder', 'contents')],
    [State('upload-folder', 'filename'),
     State('include-upload-folder', 'value')]
)
def handle_upload(contents, filename, include_upload):
    if contents is None or include_upload != "yes":
        return " "

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    current_dir_path = os.path.abspath(".")
    upload_directory = os.path.join(current_dir_path, "uploaded_dir")
    if not os.path.exists(upload_directory):
        os.makedirs(upload_directory)

    zip_path = os.path.join(upload_directory, filename)
    with open(zip_path, "wb") as file:
        file.write(decoded)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(upload_directory)

    return "Folder uploaded and extracted successfully!"

def get_completion_from_messages(messages, temperature=0.7, model="gpt-4-0613"):
    global total_api_time
    start_time_local = time.time()
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    end_time_local = time.time()
    api_call_time = end_time_local - start_time_local
    total_api_time += api_call_time
    return response

def save_conversation_history_to_file(conversation_history, dir_name='conversation_history'):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_name = f"{dir_name}/conversation_history.json"
    json_string = json.dumps(conversation_history, indent=4)
    with open(file_name, 'w') as file:
        file.write(json_string)

@app.callback(
    Output('push-status', 'children'),
    Input('git-commit-push', 'n_clicks'),
    State('commit-message', 'value'),
    prevent_initial_call=True
)
def commit_and_push(n_clicks, commit_message):
    if n_clicks is not None:
        current_directory_1 = os.getcwd()
        try:
            success, message = git_commit_push(commit_message)
            os.chdir(current_directory_1)
            return message
        except Exception as e:
            os.chdir(current_directory_1)
            return f"An error occurred: {e}"

# -------------------- Utility Functions --------------------
def read_requirements_file(file_path):
    if not os.path.isfile(file_path):
        warnings.warn(
            f"The requirements file was not found at {file_path}. Proceeding without requirements.",
            UserWarning
        )
        return ""
    result = read_generic_file_content(file_path)
    return result

def get_requirements_content():
    args_local = INSPECTA_Dog_cmd_util.get_args()
    requirements_content_local = " "
    requirements_file_path = getattr(args_local, 'requirements_file', None)

    if requirements_file_path:
        if os.path.isfile(requirements_file_path):
            try:
                requirements_content_local = read_requirements_file(requirements_file_path)
            except Exception as e:
                warnings.warn(
                    f"Error reading requirements file at '{requirements_file_path}': {e}. "
                    f"Proceeding without requirements.",
                    UserWarning
                )
        else:
            warnings.warn(
                f"The requirements file was not found at '{requirements_file_path}'. "
                f"Proceeding without requirements.",
                UserWarning
            )
    else:
        requirements_content_local = " No req file provided"

    return requirements_content_local

def construct_requirements_section(requirements_file_cont):
    if requirements_file_cont:
        return (
            "When you modify the code or try to write the fixed code consider "
            "the following requirements and make sure your modifications don't break them:\n"
            + requirements_file_cont
        )
    return ""

def construct_prompt(aadl_content, counter_example_content, requirements_section):
    args_local = INSPECTA_Dog_cmd_util.get_args()
    if args_local.counter_example is None:
        return f"""
For the following AADL model:
{aadl_content}

Warning: No counterexample was generated or provided by AGREE.
There is no cex to explain any further.
Would you like me to assist with something else?
"""
    else:
        return f"""
{requirements_section}

Consider the following AADL model:
{aadl_content}

AGREE generated a counterexample:
{counter_example_content}

Can you explain why and how to fix it?
Write the modified AADL code between ``` ```
"""

def set_prompt(aadl_content, counter_example_content):
    requirements_content_local = req_content()
    requirements_section = construct_requirements_section(requirements_content_local)
    return construct_prompt(aadl_content, counter_example_content, requirements_section)

def remove_file_ext_from_cmd_like_ui(initial_file):
    if INSPECTA_Dog_cmd_util.get_args().start_file is not None:
        initial_file_cmd = INSPECTA_Dog_cmd_util.get_args().start_file
        initial_file_without_ext = initial_file_cmd[:-5]
        return initial_file_without_ext
    else:
        return initial_file

def token_warning(model_choice, tokens_used):
    warning = ""
    if 7000 <= tokens_used < 8000 and model_choice == "gpt-4-0613":
        warning = " Warning: Tokens used are higher than 7000. If you are using GPT-4 8k, consider switching."
    return warning

def total_timedisplay(start_time_val, time_frames_local, total_api_time_val):
    global elapsed_time, formatted_elapsed_time
    elapsed_time = datetime.now() - start_time_val
    time_frames_local.append(elapsed_time)
    formatted_elapsed_time = str(elapsed_time)[:10]
    total_time_display = (
        f"Elapsed Time: {formatted_elapsed_time}, "
        f"Total API Call Time: {total_api_time_val:.2f} seconds"
    )
    return total_time_display

def set_system_message(conversation_history, system_message_choice):
    if not conversation_history:
        conversation_history = [{'role': 'system', 'content': ''}]
    if system_message_choice == "CoqDog":
        conversation_history[0]['content'] = INSPECTA_dog_system_msgs.COQ_dog_sys_msg
    elif system_message_choice == "AgreeDog":
        conversation_history[0]['content'] = INSPECTA_dog_system_msgs.AGREE_dog_sys_msg
    return json.dumps(conversation_history), "", "", "", ""

def reset_timer_variables():
    global start_time, elapsed_time, formatted_elapsed_time
    start_time = None
    elapsed_time = timedelta(0)
    formatted_elapsed_time = "00:00:00.00"

def read_start_file_content(file_path):
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
        return file_content.strip()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return ""

def read_generic_file_content(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def handle_requires(file_path, project_files, files_to_check, processed_files):
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith('with'):
                required_packages_line = line[4:].strip().rstrip(';')
                required_packages = [pkg.strip() for pkg in required_packages_line.split(',')]
                for required_pkg in required_packages:
                    if (
                        required_pkg in project_files
                        and required_pkg not in processed_files
                        and required_pkg not in files_to_check
                    ):
                        files_to_check.append(required_pkg)

def read_project_files(directory):
    if INSPECTA_Dog_cmd_util.get_args().working_dir is not None:
        agree_files = os.path.join(directory, "_AgreeFiles")
        if not os.path.exists(agree_files):
            INSPECTA_Dog_cmd_util.create_agree_files_file(directory)
            agree_files = os.path.join(directory, "_AgreeFiles")
    else:
        agree_files = os.path.join(directory, "packages/_AgreeFiles")
        if not os.path.exists(agree_files):
            directory = os.path.join(directory, "packages")
            INSPECTA_Dog_cmd_util.create_agree_files_file(directory)
            agree_files = os.path.join(directory, "_AgreeFiles")

    if not os.path.exists(agree_files):
        warnings.warn(
            f"The expected '_AgreeFiles' file was not found in {directory}. "
            f"Continuing, but some functionality may be affected.",
            UserWarning
        )
        return []

    project_files = []
    with open(agree_files, 'r') as file:
        for line in file:
            filename = line.strip()
            if filename.endswith(".aadl"):
                project_files.append(filename[:-5])
    return project_files

def concatenate_imports(start_file, project_files, folder_path,
                        include_requirements_chain, include_upload_folder,
                        context_added):
    processed_files = set()
    context = ""
    files_to_check = [start_file]

    while files_to_check:
        current_file = files_to_check.pop()
        if current_file in processed_files:
            continue
        processed_files.add(current_file)

        if (include_requirements_chain == "yes" and start_file and
            context_added == "false" and include_upload_folder == "no"):
            file_path = os.path.join(folder_path, current_file + ".aadl")
        elif (include_requirements_chain == "yes" and start_file and
              context_added == "true" and include_upload_folder == "yes"):
            file_path = os.path.join(folder_path, "packages", current_file + ".aadl")
        else:
            file_path = os.path.join(folder_path, current_file + ".aadl")

        if not os.path.exists(file_path):
            print(f"{current_file} is not in packages")
            continue

        if current_file == start_file:
            content = read_start_file_content(file_path)
        else:
            content = read_generic_file_content(file_path)
        context += content + "\n"

        handle_requires(file_path, project_files, files_to_check, processed_files)
    return context

def highlight_keywords(text):
    keywords = [
        "Lemma", "Proof", "Qed", "assume", "guarantee", "end",
        "system", "annex", "agree", "connections", "properties",
        "features", "lemma", "aadl", "initially"
    ]
    elements = []
    start = 0

    while start < len(text):
        closest_idx = len(text)
        closest_keyword = None
        for keyword in keywords:
            idx = text.find(keyword, start)
            if idx != -1 and idx < closest_idx:
                closest_idx = idx
                closest_keyword = keyword

        if closest_keyword is not None:
            if closest_idx != start:
                elements.append(text[start:closest_idx])
            key_color = 'purple'
            if closest_keyword in ["connections"]:
                key_color = 'blue'
            elements.append(
                html.Span(
                    text[closest_idx:closest_idx + len(closest_keyword)],
                    style={'color': key_color}
                )
            )
            start = closest_idx + len(closest_keyword)
        else:
            elements.append(text[start:])
            break
    return elements

def format_display_text(conversation_history, display_mode):
    if display_mode == "full":
        display_elements = []
        for message in conversation_history:
            if message['role'] == 'system':
                continue
            if message['role'] == 'user':
                label = html.Span("User:", style={'color': 'blue'})
            else:
                label = html.Span("AGREE-Dog:", style={'color': 'red'})

            display_elements.append(label)
            display_elements.extend(
                highlight_keywords(" " + message['content'] + "\n\n")
            )
        return display_elements
    else:  # "last" mode
        last_message = conversation_history[-1]
        if last_message['role'] == 'system':
            return [html.Span("(No user/assistant message yet.)", style={'color': 'gray'})]
        if last_message['role'] == 'user':
            label = html.Span("User:", style={'color': 'blue'})
        else:
            label = html.Span("AGREE-Dog:", style={'color': 'red'})
        highlighted_last = highlight_keywords(" " + last_message['content'] + "\n\n")
        return [label] + highlighted_last

if __name__ == '__main__':
    print("Starting the Dash server...")
    try:
        app.run_server(debug=False, host='127.0.0.1', port=8050)
    except KeyboardInterrupt:
        print("Shutting down the server gracefully.")
