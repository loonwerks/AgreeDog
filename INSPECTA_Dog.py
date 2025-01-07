# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True,suspend=False)
"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTA_Dog copilot - ChatCompletion, and Multi-Modal Mode.
Date: July 2024
"""
import os.path
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
import os

# Your utility imports
import INSPECTA_Dog_cmd_util
import INSPECTA_dog_system_msgs
from INSPECTA_Dog_cmd_util import *
from git_actions import *

# Ensure necessary directories exist
directories = ["conversation_history", "temp_history", "shared_history", "counter_examples", "proof_analysis"]
INSPECTA_Dog_cmd_util.ensure_writable_directories(directories)

args = get_args()  # If --help is passed, argparse prints help and exits here.

# After loading environment variables, modify how openai.api_key is set:
if args.user_open_api_key:
    openai.api_key = args.user_open_api_key
else:
    load_dotenv(find_dotenv())
    openai.api_key = os.getenv('OPENAI_API_KEY')

# -------------------- Dash App Setup --------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Add components to the layout for displaying the token count and timer
token_display = html.Div(id='token-count', style={"margin-top": "20px"})
timer_display = html.Div(id='timer-display', style={"margin-top": "20px"})

gear_button = dbc.Button(
    [
        # Using Font Awesome gear icon
        html.I(className="fa fa-cog", style={"margin-right": "5px"}),
        "Settings"
    ],
    id="gear-button",
    color="secondary",
    className="ml-3",
    style={"display": "inline-block", "vertical-align": "middle"}
)

app.layout = dbc.Container([
    # Footer
    html.Footer([
        html.P([
            html.Span("", style={"font-size": "14px"}),
            html.Span("©", style={"font-size": "14px"}),
            " Proof of Concept Web Service"
        ])
    ], style={
        "text-align": "center",
        "background-color": "#f1f1f1",
        "padding": "10px",
        "margin-bottom": "20px"
    }),

    # Header with logo, title, and gear button
    html.Div([
        html.Img(
            src="assets/coqdog-5.png",
            id="app-logo",
            style={
                "display": "inline-block",
                "height": "50px",
                "vertical-align": "middle"
            }
        ),
        html.H1(
            "AGREE-Dog ",
            style={
                "display": "inline-block",
                "vertical-align": "middle",
                "margin-left": "20px"
            }
        ),
        gear_button
    ], style={"display": "flex", "align-items": "center", "margin-bottom": "20px"}),

    # -------------------- Settings Menu --------------------
    html.Div(
        id='system-message-menu',
        style={"display": "none", "margin-bottom": "20px"},
        children=[
            # 1) System Message choice
            dcc.RadioItems(
                id='system-message-choice',
                options=[
                    {"label": "JKind SMTSolvers AI selector", "value": "Enable JKind SMTSolvers selector", "disabled": True}, # used to be CoqDog System Message
                    {"label": "AgreeDog System Message", "value": "AgreeDog"}
                ],
                value="AgreeDog"
            ),
            dbc.Button("Confirm Selection", id='confirm-system-message-button', color="primary", className="mr-1"),
            html.Hr(),

            # 2) Move advanced items here
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
                    {"label": "Include requirement chain", "value": "yes"},
                    {"label": "Don't include requirement chain", "value": "no"},
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
                    #{"label": "GPT-3.5 (16K tk)", "value": "gpt-3.5-turbo-16k-0613", "disabled": True},
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
                value="full",
                inline=True,
                style={"margin-top": "10px"}
            ),
            #dcc.RadioItems(
            #    id="use-recommendation",
            #    options=[
            #        {"label": "Use Copland Customized Recommendation System", "value": "yes", "disabled": True},
            #        {"label": "Don't Use Recommendation System", "value": "no", "disabled": True},
            #    ],
            #    value="no",
            #    inline=True,
            #    style={"margin-top": "10px"}
            #),
        ]
    ),

    # -------------------- Main Textarea & Buttons --------------------
    dcc.Textarea(
        id='user-input',
        style={"width": "100%", "height": 200},
        placeholder='Enter your context...'
    ),

    # 3) The "Enter the start file" input – initially hidden
    html.Div(
        id='initial-file-div',
        style={"display": "none"},  # hidden by default; toggled by callback
        children=[
            dbc.Input(
                id='initial-file',
                placeholder='Enter the start file (e.g., file_name)',
                type='text',
                style={"margin-top": "10px"}
            )
        ]
    ),

    # 4) Buttons row: Submit, Save, Upload Folder (optional)
    html.Div([
        dbc.Button("Submit", id='submit-button', color="primary", className="mr-1"),
        dbc.Button("Save", id='copy-button', color="secondary", className="mr-1"),
        # We wrap the Upload Folder button in a small div that we can show/hide:
        html.Div(
            id='upload-folder-div',
            style={"display": "none"},  # hidden by default; toggled by callback
            children=[
                dcc.Upload(
                    id='upload-folder',
                    children=dbc.Button("Upload Folder", color="secondary", className="mr-1"),
                    multiple=False
                )
            ]
        )
    ], style={"display": "flex", "align-items": "center", "margin-top": "10px"}),

    html.Div(id='upload-status', style={"margin-top": "10px"}),
    html.Div(id='copy-status', style={"margin-top": "10px"}),
    html.Div(id='response-output', style={"white-space": "pre-line", "margin-top": "20px"}),

    # Hidden fields / placeholders
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

    dbc.Input(
        id='commit-message',
        placeholder='Enter commit message',
        type='text',
        style={"margin-top": "20px"}
    ),
    dbc.Button("Git Commit and Push", id='git-commit-push', color="success", className="mr-1"),
    html.Div(id='push-status', style={"margin-top": "20px"})
])

# -------------------- Global Timer Variables --------------------
total_api_time = 0
time_frames = []
start_time = None
elapsed_time = timedelta(0)
formatted_elapsed_time = "00:00:00.00"


# -------------------- Callbacks --------------------

# 1) Toggle the advanced menu (system-message-menu) with the GEAR button
@app.callback(
    Output('system-message-menu', 'style'),
    Input('gear-button', 'n_clicks'),
    State('system-message-menu', 'style'),
    prevent_initial_call=True
)
def toggle_system_message_menu(gear_clicks, style):
    """
    When the gear button is clicked, toggle the display
    of the system message menu (show/hide).
    """
    if not gear_clicks:
        return style  # If button was never clicked, do nothing

    # If the 'display' is "none", show it; otherwise hide it
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style


# 2) Conditionally show/hide the "Upload Folder" button
@app.callback(
    Output('upload-folder-div', 'style'),
    Input('include-upload-folder', 'value'),
    prevent_initial_call=True
)
def toggle_upload_folder_div(include_upload):
    """
    Shows the Upload Folder button if the user selected "Load additional context"
    in the Settings menu.
    """
    if include_upload == "yes":
        return {"display": "block", "margin-left": "10px"}
    return {"display": "none"}

# 3) Conditionally show/hide the "Enter the start file" input
@app.callback(
    Output('initial-file-div', 'style'),
    Input('include-upload-folder', 'value'),
    prevent_initial_call=True
)
def toggle_initial_file_div(include_upload):
    """
    Shows the "Enter the start file" field if the user selected
    "Load additional context" in the Settings menu.
    """
    if include_upload == "yes":
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
        State('use-recommendation', 'value'),
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
                            use_recommendation,
                            user_input,
                            initial_file,
                            include_requirements_chain,
                            include_upload_folder):
    """
    Handles both the selection/confirmation of the system message
    (when Confirm Selection is clicked)
    and the submission of user input.
    """
    global start_time, elapsed_time, formatted_elapsed_time, time_frames, total_api_time
    time_frames.append(elapsed_time)
    reset_timer_variables()

    # Determine which button was clicked
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    conversation_history = json.loads(conversation_history_json)

    # 2A) System Message Confirmation
    if triggered_id == 'confirm-system-message-button' and confirm_n_clicks is not None:
        print(f"Confirm button clicked, selected message: {system_message_choice}")
        ch_json, resp, usr_val, tkn_count, tmr_display = set_system_message(conversation_history, system_message_choice)
        # We do not change context_added here
        return ch_json, resp, usr_val, tkn_count, tmr_display, context_added

    # 2B) User Input Submission
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

        # Initialize conversation if empty
        if not conversation_history:
            conversation_history = [
                {
                    'role': 'system',
                    'content': INSPECTA_dog_system_msgs.AGREE_dog_sys_msg
                }
            ]
            context_added = "false"

        upload_directory = get_resource_path("uploaded_dir")
        subdirectories = [
            os.path.join(upload_directory, d) for d in os.listdir(upload_directory)
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

        # If command line arguments are provided
        if INSPECTA_Dog_cmd_util.get_args().working_dir is not None:
            args = INSPECTA_Dog_cmd_util.get_args()
            target_directory = args.working_dir
            if args.start_file is not None:
                initial_file = args.start_file
        else:
            # Use uploaded directory if no cmd args
            target_directory = subdirectories[0] if subdirectories else ""
            print("Target directory:", target_directory)

        project_files = read_project_files(target_directory)

        # Only add initial context if it's not already added
        if context_added == "false":
            # If "Include requirements chain" is chosen
            if include_requirements_chain == "yes" and initial_file and include_upload_folder == "no":
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

            # If "Include requirements chain" is not chosen
            elif (
                include_requirements_chain == "no"
                and initial_file
                and include_upload_folder == "no"
                and context_added == "false"
                and INSPECTA_Dog_cmd_util.get_args().counter_example is not None
            ):
                cex_path = INSPECTA_Dog_cmd_util.get_args().counter_example
                cex = read_counter_example_file(cex_path)
                start_file_with_ext = INSPECTA_Dog_cmd_util.get_args().start_file
                working_dir = INSPECTA_Dog_cmd_util.get_args().working_dir
                start_file_path = os.path.join(working_dir, start_file_with_ext)
                start_file_content = read_start_file_content(start_file_path)
                prompt = set_prompt(start_file_content, cex)
                user_input = f"{prompt}\n{user_input}"
                context_added = "true"

            elif (
                include_requirements_chain == "no"
                and initial_file
                and include_upload_folder == "yes"
            ):
                # If the user chooses to upload and not use requirements chain,
                # we do not re-add context from cmd line. user_input stays as-is.
                pass

        # Append user input to conversation
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

    # Default return
    return (
        conversation_history_json,
        "",
        "",
        "",
        (f"Elapsed Time: {formatted_elapsed_time}, "
         f"Total API Call Time: {total_api_time:.2f} seconds"),
        context_added
    )


# -------------------- Utility Functions --------------------
def set_prompt(aadl_content, counter_example_content):
    """Generates the initial prompt with AADL model and counterexample content."""
    if INSPECTA_Dog_cmd_util.get_args().counter_example is None:
        # If the counterexample content is empty, provide a warning in the prompt
        prompt = f"""
        For the following AADL model:
        {aadl_content}

        Warning: No counterexample was generated or provided by AGREE.
        There is no cex to explain any further.
        Would you like me to assist with something else?
        """
    else:
        prompt = f"""
        Consider the following AADL model:
        {aadl_content}

        AGREE generated a counterexample:
        {counter_example_content}

        Can you explain why and how to fix it?
        """
    return prompt


def remove_file_ext_from_cmd_like_ui(initial_file):
    if INSPECTA_Dog_cmd_util.get_args().start_file is not None:
        initial_file = INSPECTA_Dog_cmd_util.get_args().start_file
        initial_file_without_ext = initial_file[:-5]
        return initial_file_without_ext
    else:
        return initial_file


def token_warning(model_choice, tokens_used):
    warning = ""
    if 7000 <= tokens_used < 8000 and model_choice == "gpt-4-0613":
        warning = " Warning: Tokens used are higher than 7000. If you are using GPT-4 8k, consider switching to GPT-3.5 16K."
    return warning


def total_timedisplay(start_time, time_frames, total_api_time):
    global elapsed_time, formatted_elapsed_time
    elapsed_time = datetime.now() - start_time
    time_frames.append(elapsed_time)
    formatted_elapsed_time = str(elapsed_time)[:10]
    total_time_display = f"Elapsed Time: {formatted_elapsed_time}, Total API Call Time: {total_api_time:.2f} seconds"
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
                    if (required_pkg in project_files and
                            required_pkg not in processed_files and
                            required_pkg not in files_to_check):
                        files_to_check.append(required_pkg)


def read_project_files(directory):
    if INSPECTA_Dog_cmd_util.get_args().working_dir is not None:
        agree_files = os.path.join(directory, "_AgreeFiles")
        if not os.path.exists(agree_files):
            create_agree_files_file(directory)
            agree_files = os.path.join(directory, "_AgreeFiles")
    else:
        agree_files = os.path.join(directory, "packages/_AgreeFiles")
        if not os.path.exists(agree_files):
            directory = os.path.join(directory, "packages")
            INSPECTA_Dog_cmd_util.create_agree_files_file(directory)
            agree_files = os.path.join(directory, "/_AgreeFiles")

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
                project_files.append(filename[:-5])  # Remove '.aadl' extension
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

        if (include_requirements_chain == "yes" and start_file
                and context_added == "false" and include_upload_folder == "no"):
            file_path = os.path.join(folder_path, current_file + ".aadl")
        elif (include_requirements_chain == "yes" and start_file
              and context_added == "true" and include_upload_folder == "yes"):
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
            if message['role'] == 'user':
                label = html.Span("User:", style={'color': 'blue'})
            elif message['role'] == 'assistant':
                label = html.Span("INSPECTA-Dog:", style={'color': 'red'})
            else:
                continue
            display_elements.append(label)
            display_elements.extend(
                highlight_keywords(" " + message['content'] + "\n\n")
            )
        return display_elements
    else:
        last_message = conversation_history[-1]
        if last_message['role'] == 'user':
            label = html.Span("User:", style={'color': 'blue'})
        else:
            label = html.Span("INSPECTA-Dog:", style={'color': 'red'})
        return [label, " " + last_message['content']]


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
    start_time = time.time()  # Record the start time
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    end_time = time.time()  # Record the end time
    api_call_time = end_time - start_time
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


# -------------------- Main --------------------
if __name__ == '__main__':
    print("Starting the Dash server...")
    try:
        app.run_server(debug=False, host='127.0.0.1', port=8050)
    except KeyboardInterrupt:
        print("Shutting down the server gracefully.")

