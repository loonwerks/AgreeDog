#!/usr/bin/env python
# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTA_Dog copilot - ChatCompletion, and Multi-Modal Mode.
Strat Date: 1st July 2024
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
import xml.etree.ElementTree as ET
# Utility imports
import INSPECTA_Dog_cmd_util
import INSPECTA_dog_system_msgs
from INSPECTA_Dog_cmd_util import *
from git_actions import *
import webbrowser

# -------------------- Global Logging Setup --------------------
# A global list to store log messages.
copilot_logs = []

def log_message(msg, level="info"):
    """
    Appends a message with timestamp and level (INFO, WARNING, ERROR) to the global log list.
    Also prints the message to the console.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {level.upper()}: {msg}"
    print(full_msg)
    copilot_logs.append(full_msg)
    return full_msg  # also return the message for callback outputs


# -------------------- Ensure necessary directories exist --------------------
directories = ["conversation_history", "temp_history", "shared_history", "counter_examples", "proof_analysis"]
INSPECTA_Dog_cmd_util.ensure_writable_directories(directories)

# -------------------- INITIAL CONFIGURATION --------------------
# Parse command-line arguments once at startup:
args = INSPECTA_Dog_cmd_util.get_args()

# Create a global configuration dictionary.
cli_config = {
    "working_dir": args.working_dir,
    "start_file": args.start_file,
    "counter_example": args.counter_example,
    "requirement_file": args.requirement_file,
    "user_open_api_key": args.user_open_api_key,
}

# Set the OpenAI API key based on CLI or environment variable
if cli_config["user_open_api_key"]:
    openai.api_key = cli_config["user_open_api_key"]
else:
    load_dotenv(find_dotenv())
    openai.api_key = os.getenv('OPENAI_API_KEY')

# -------------------- Process sys-requirement.txt File --------------------
requirements_content = ""


def req_content():
    global requirements_content
    if cli_config["requirement_file"]:
        requirement_path = cli_config["requirement_file"]
        if os.path.isfile(requirement_path):
            log_message(f"Requirement file provided: {requirement_path}", "info")
            try:
                with open(requirement_path, 'r') as f:
                    requirements_content = f.read()
                log_message("Contents of sys_requirement.txt loaded successfully.", "info")
                return requirements_content
            except Exception as e:
                log_message(f"Error reading sys_requirement file: {e}", "error")
        else:
            log_message(f"Requirement file not found at: {requirement_path}", "warning")
    else:
        log_message("No sys_requirement.txt file provided.", "warning")
        return "No sys_requirement.txt file provided."


req_content()
requirements_file_content = requirements_content

# -------------------- NEW GLOBAL VARIABLE for Refresh Prompt --------------------
last_counterexample_file = None

# -------------------- Dash App Setup --------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# -------------------- Button Components with Tooltips --------------------
# Refresh Prompt button and tooltip
refresh_prompt_button = dbc.Button(
    [
        html.I(className="fa fa-sync", style={"margin-right": "5px"}),
        "Feedback Loop"
    ],
    id="refresh-prompt",
    color="warning",
    style={"margin-left": "5px"}
)
refresh_tooltip = dbc.Tooltip(
    "Update variables from AGREE messages and auto-generate prompts for new counterexamples. You can still add extra requirements",
    target="refresh-prompt",
    placement="top"
)
refresh_prompt_status = html.Div(
    id='refresh-prompt-status',
    #style={"margin-top": "10px", "color": "green", "font-weight": "bold"}
    style={"display": "none"}
)

# Gear button and tooltip
gear_button = dbc.Button(
    [
        html.I(className="fa fa-cog", style={"margin-right": "5px"})
    ],
    id="gear-button",
    color="secondary",
    style={"display": "inline-block", "vertical-align": "middle"}
)
gear_tooltip = dbc.Tooltip(
    "Click to toggle system message menu",
    target="gear-button",
    placement="top"
)

# Shutdown button and tooltip
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
shutdown_tooltip = dbc.Tooltip(
    "Click to shutdown the server",
    target="shutdown-button",
    placement="top"
)

# Apply (Insert) button and tooltip
apply_button = dbc.Button(
    [
        html.I(className="fa fa-check-circle", style={"margin-right": "5px"}),
        "Insert"
    ],
    id="apply-modifications",
    color="secondary",
    style={"margin-left": "5px"}
)
apply_tooltip = dbc.Tooltip(
    "Applies changes to the file. Use undo or Git revert to restore previous work.",
    target="apply-modifications",
    placement="top"
)

# Submit button and tooltip
submit_button = dbc.Button(
    [
        html.I(className="fa fa-paper-plane", style={"margin-right": "2px"}),
        "Submit"
    ],
    id='submit-button',
    color="primary",
    style={"margin-right": "2px"}
)
submit_tooltip = dbc.Tooltip(
    "Submit your input",
    target="submit-button",
    placement="top"
)

# Copy (Save) button and tooltip
copy_button = dbc.Button(
    [
        html.I(className="fa fa-save", style={"margin-right": "2px"}),
        "Save"
    ],
    id='copy-button',
    color="secondary",
    style={"margin-right": "2px"}
)
copy_tooltip = dbc.Tooltip(
    "Click to save conversation history to the temp-history directory on your local disk. To share with your\
     team, enable the Git commit feature to submit it to the shared memory repo. ",
    target="copy-button",
    placement="top"
)

# Upload Folder button (inside dcc.Upload) and tooltip.
# Assign an id ("upload-button") to the inner button for targeting.
upload_button = dbc.Button(
    [
        html.I(className="fa fa-upload", style={"margin-right": "2px"}),
        "Upload Folder"
    ],
    id="upload-button",
    color="secondary"
)
upload_tooltip = dbc.Tooltip(
    "Click to upload a folder",
    target="upload-button",
    placement="top"
)

# Git Commit and Push button and tooltip
git_commit_push_button = dbc.Button(
    [
        html.I(className="fab fa-github", style={"margin-right": "5px"}),
        "Git Commit and Push"
    ],
    id='git-commit-push',
    color="success",
    className="mr-1"
)
git_tooltip = dbc.Tooltip(
    "Click to commit and push changes",
    target="git-commit-push",
    placement="top"
)

# -------------------- Other UI Components --------------------
token_display = html.Div(id='token-count', style={"margin-top": "20px"})
timer_display = html.Div(id='timer-display', style={"margin-top": "20px"})

# -------------------- Dash App Layout --------------------
app.layout = dbc.Container([
    # Header with dog image & text on the left, Collins on the right
    html.Div([
        html.Div([
            html.Div([
                html.Img(
                    src="assets/coqdog-5.png",
                    id="app-logo",
                    style={"height": "70px", "vertical-align": "middle"}
                ),
                html.H1(
                    "AGREE-Dog",
                    style={
                        "font-family": "Arial, Helvetica",
                        "font-weight": "bold",
                        "font-size": "40px",
                        "margin-left": "20px",
                        "vertical-align": "middle"
                    }
                )
            ], style={"display": "flex", "align-items": "center"}),
            html.Img(
                src="assets/collins_logo.png",
                id="collins-logo",
                style={"display":"none"}
                #style={"height": "70px", "width": "250px", "vertical-align": "middle"}
            )
        ], style={"display": "flex", "align-items": "center", "justify-content": "space-between",
                  "margin-bottom": "5px"})
    ]),
    # Settings Menu
    html.Div(
        id='system-message-menu',
        style={"display": "none", "margin-bottom": "20px"},
        children=[
            dcc.RadioItems(
                id='system-message-choice',
                options=[
                    {"label": "JKind SMTSolvers AI selector", "value": "Enable JKind SMTSolvers selector",
                     "disabled": True},
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
                    {"label": "GPT-O3 reasoning (128k tk)", "value": "o3"},
                    {"label": "GPT-4.1 multi-modal (1 m tk)", "value": "gpt-4.1.2025-4-14"},
                    {"label": "GPT-4o multi-modal (128k tk)", "value": "gpt-4o"},
                    {"label": "GPT-4-Turbo (128k tk)", "value": "gpt-4-turbo"},
                    {"label": "GPT-4 (8k tk)", "value": "gpt-4-0613", "disabled": True},
                ],
                value="o3",#"gpt-4o",
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
            shutdown_button,
            shutdown_tooltip
        ]
    ),
    # Main Textarea & Buttons
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
        submit_button,
        submit_tooltip,
        copy_button,
        copy_tooltip,
        gear_button,
        gear_tooltip,
        refresh_prompt_button,  # Refresh Prompt button
        refresh_tooltip,
        refresh_prompt_status,  # Status message for refresh prompt
        html.Div(
            id='upload-folder-div',
            style={"display": "none", "margin-left": "2px"},
            children=[
                dcc.Upload(
                    id='upload-folder',
                    children=upload_button,
                    multiple=False
                ),
                upload_tooltip
            ]
        ),
        apply_button,
        apply_tooltip
    ], style={"display": "flex", "align-items": "center", "margin-top": "10px"}),
    html.Div(id='upload-status', style={"margin-top": "10px"}),
    html.Div(id='copy-status', style={"margin-top": "10px"}),
    html.Div(id='response-output', style={"white-space": "pre-line", "margin-top": "20px"}),
    # Hidden placeholders
    html.Div(id='conversation-history', style={'display': 'none'}, children="[]"),
    html.Div(id='context-added', style={'display': 'none'}, children="false"),
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
            git_commit_push_button,
            git_tooltip,
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
    html.Div(id='apply-status', style={"margin-top": "10px", "color": "green"}),
    # Hidden global store for the context prompt
    dcc.Store(id="global-context-prompt", data=""),
    # -------------------- New Logging Section --------------------
    html.Hr(),
    html.H4("Copilot Logs", style={"margin-top": "20px"}),
    html.Div(
        id="log-section",
        style={
            "backgroundColor": "#f8f9fa",
            "padding": "10px",
            "border": "1px solid #ccc",
            "maxHeight": "200px",
            "overflowY": "auto"
        }
    ),
    # Hidden Interval component to periodically update the log display
    dcc.Interval(id="log-update-interval", interval=2000, n_intervals=0)
], fluid=True)

# -------------------- Global Timer Variables --------------------
total_api_time = 0
time_frames = []
start_time = None
elapsed_time = timedelta(0)
formatted_elapsed_time = "00:00:00.00"


# -------------------- Helper functions for Counterexample Handling --------------------
def find_agree_log_dir(start_dir="."):
    """
    Recursively search for a directory named 'AgreeDog' starting from 'start_dir'.
    Returns the full path if found, else returns None.
    """
    for root, dirs, files in os.walk(start_dir):
        if 'AgreeDog' in dirs:
            return os.path.join(root, 'AgreeDog')
    return None

def try_load_cli_counterexample(aadl_content: str, requirements_content: str) -> tuple:
    """
    Attempts to load a counterexample file from the CLI.
    If successful, returns a constructed prompt and status message.
    Otherwise, returns (None, None) so the fallback logic can proceed.
    """
    ce_examples = []
    cli_cex_path = cli_config.get("counter_example")

    if cli_cex_path and os.path.isfile(cli_cex_path):
        cli_cex_content = read_counter_example_file(cli_cex_path)
        if cli_cex_content.strip():
            ce_examples.append(f"Counterexample provided via command-line:\n{cli_cex_content}\n---")
            prompt = construct_comprehensive_prompt(aadl_content, ce_examples, requirements_content)
            status = log_message("Prompt updated using counterexample from CLI", "info")
            return prompt, status
        else:
            log_message("CLI counterexample file was empty or invalid. Falling back to log/xml.", "warning")

    return None, None

def read_counter_example_file(cex_path: str) -> str:
    try:
        with open(cex_path, 'r') as f:
            content = f.read()
        log_message(f"Loaded counterexample from CLI path: {cex_path}", "info")
        return content
    except Exception as e:
        log_message(f"Failed to read CLI counterexample file at {cex_path}: {e}", "warning")
        return ""


def read_agree_log(log_dir: str) -> list:
    path = os.path.join(log_dir, 'agree.log')
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def is_model_valid(results: list) -> bool:
    def _rec(node):
        if node.get('result') == 'Invalid':
            return False
        for child in node.get('analyses', []):
            if not _rec(child):
                return False
        return True
    return all(_rec(entry) for entry in results)

def find_failing_contracts(log_dir: str) -> list:
    data = read_agree_log(log_dir)
    failing = []
    def _rec(node):
        if node.get('result') == 'Invalid':
            name = node.get('name')
            if name:
                failing.append(name)
        for child in node.get('analyses', []):
            _rec(child)
    for entry in data:
        _rec(entry)
    return list(dict.fromkeys(failing))

def find_xmls_with_failures(xml_dir: str, fail_names: list) -> list:
    matches = []
    for fn in os.listdir(xml_dir):
        if not fn.endswith(".lus.xml"):
            continue
        path = os.path.join(xml_dir, fn)
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            for prop in root.findall('.//Property'):
                if prop.get('name') in fail_names:
                    matches.append(path)
                    break
        except ET.ParseError:
            continue
    return matches

def parse_counterexample_xml(xml_path: str) -> pd.DataFrame:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    cex = root.find('.//Counterexample')
    data = {}
    times = set()
    for sig in cex.findall('Signal'):
        name = sig.get('name')
        for val in sig.findall('Value'):
            t = int(val.get('time'))
            v = val.text
            times.add(t)
            data.setdefault(name, {})[t] = v
    df = pd.DataFrame.from_dict(data, orient='columns')
    df.index = sorted(times)
    df.index.name = 'Step'
    return df

def df_to_markdown(df: pd.DataFrame) -> str:
    return df.to_markdown(tablefmt='github')

def construct_comprehensive_prompt(aadl_content, ce_examples, requirements_content):
    prompt_parts = []
    if requirements_content:
        prompt_parts.append("When analyzing and modifying the code, consider these requirements:\n"
                            f"{requirements_content}\n")
    if aadl_content:
        prompt_parts.append("Analyze the following AADL model:\n"
                            f"{aadl_content}\n")
    if ce_examples:
        prompt_parts.extend(ce_examples)
    prompt_parts.append("Please explain why the verification failed and suggest modifications to fix the issues. "
                        "Write the modified AADL code between ``` ```.")
    return "\n".join(prompt_parts)

# -------------------- Callbacks --------------------
# Callback for Log Display
@app.callback(
    Output('log-section', 'children'),
    Input('log-update-interval', 'n_intervals')
)
def update_log_display(n):
    return html.Ul([html.Li(msg) for msg in copilot_logs])


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


# Auto-refresh on load callback
@app.callback(
    Output('refresh-prompt', 'n_clicks'),
    Input('refresh-prompt', 'id'),
    prevent_initial_call=False
)
def auto_refresh_on_load(id_value):
    # This will trigger the refresh_prompt_callback once when the app loads
    return 1


# Update the input placeholder based on context availability
@app.callback(
    Output('user-input', 'placeholder'),
    Input('global-context-prompt', 'data')
)
def update_placeholder(global_context_prompt):
    if global_context_prompt:
        return "Context from files loaded. Add any additional questions or requests here..."
    else:
        return "Enter your context..."


# Update submit button text based on context status
@app.callback(
    Output('submit-button', 'children'),
    Input('global-context-prompt', 'data')
)
def update_submit_button(global_context_prompt):
    if global_context_prompt:
        return [
            html.I(className="fa fa-paper-plane", style={"margin-right": "5px"}),
            "Submit with Context"
        ]
    else:
        return [
            html.I(className="fa fa-paper-plane", style={"margin-right": "5px"}),
            "Submit"
        ]


# -------------------- Enhanced Refresh Prompt Callback --------------------

cex_extensions = [".lus.xml", ".txt", ".xls", ".ods"]

# Helper: find new counterexample files (not previously used)
def get_new_counterexample_files(dir_path: str, previously_seen: set) -> list:
    if not os.path.isdir(dir_path):
        return []
    candidates = []
    for fn in os.listdir(dir_path):
        if os.path.splitext(fn)[1] in cex_extensions:
            full_path = os.path.join(dir_path, fn)
            if full_path not in previously_seen:
                candidates.append(full_path)
    return candidates

# Modified refresh_prompt_callback
@app.callback(
    [Output('global-context-prompt', 'data'), Output('refresh-prompt-status', 'children')],
    Input('refresh-prompt', 'n_clicks')
)
def refresh_prompt_callback(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    global last_counterexample_file
    aadl_content = ""
    requirements_content = ""

    if cli_config["start_file"]:
        working_dir = cli_config["working_dir"] if cli_config["working_dir"] else os.getcwd()
        start_file_path = os.path.join(working_dir, cli_config["start_file"])
        if os.path.exists(start_file_path):
            aadl_content = read_start_file_content(start_file_path)
        else:
            log_message(f"AADL model file not found: {start_file_path}", "warning")

    if cli_config["requirement_file"]:
        requirements_content = read_requirements_file(cli_config["requirement_file"])

    # Try CLI-provided counterexample first
    cli_cex_path = cli_config.get("counter_example")
    counter_example_dir_path = None

    if cli_cex_path and os.path.isfile(cli_cex_path):
        cli_cex_content = read_counter_example_file(cli_cex_path)
        if cli_cex_content.strip():
            ce_examples = [f"Counterexample provided via command-line:\n{cli_cex_content}\n---"]
            prompt = construct_comprehensive_prompt(aadl_content, ce_examples, requirements_content)
            status = log_message("Prompt updated using counterexample from CLI", "info")
            counter_example_dir_path = os.path.dirname(cli_cex_path)
            cli_config["counter_example"] = None
            last_counterexample_file = cli_cex_path
            return prompt, status
        else:
            log_message("CLI counterexample file was empty or invalid. Falling back to log/xml.", "warning")

    # Fallback: agree.log + XML
    counterexample_dir = os.path.dirname(cli_config["counter_example"]) if cli_config["counter_example"] else "."
    #agree_log_dir = "~/AgreeDog"#
    agree_log_dir = find_agree_log_dir(os.path.expanduser("~"))  # or os.getcwd()
    if not agree_log_dir:
        log_message("Could not locate AgreeDog directory. Falling back to current directory.", "warning")
        agree_log_dir = os.getcwd()
    try:
        agree_data = read_agree_log(agree_log_dir)
    except FileNotFoundError:
        prompt = construct_comprehensive_prompt(aadl_content, [], requirements_content)
        status = "agree.log not found. Only requirements and model shown."
        return prompt, log_message(status, "warning")

    if not is_model_valid(agree_data):
        fail_names = find_failing_contracts(agree_log_dir)

        # Check counterexamples/ directory first
        #counterexample_dir = os.path.join(working_dir, "counter_examples")
        if not os.path.isdir(counterexample_dir) and counter_example_dir_path:
            counterexample_dir = counter_example_dir_path

        seen = {last_counterexample_file} if last_counterexample_file else set()
        new_cex_files = get_new_counterexample_files(counterexample_dir, seen)

        if not new_cex_files:
            log_message("No new counterexamples found in counterexamples/. Falling back to /tmp", "info")
            counterexample_dir = tempfile.gettempdir() ## ToDo check the import for xml
            new_cex_files = get_new_counterexample_files(counterexample_dir, seen)

        ce_examples = []
        used_paths = set()
        for fail_name in fail_names:
            for path in new_cex_files:
                if path in used_paths:
                    continue
                if path.endswith(".lus.xml"):
                    try:
                        tree = ET.parse(path)
                        root = tree.getroot()
                        for prop in root.findall('.//Property'):
                            if prop.get('name') == fail_name: ## ToDo this is the property name not the file name
                                df = parse_counterexample_xml(path)
                                md = df_to_markdown(df)
                                ce_examples.append(f"Counterexample for `{fail_name}` (from `{os.path.basename(path)}`):\n{md}\n---")
                                used_paths.add(path)
                                break
                    except Exception:
                        continue
                else:
                    try:
                        with open(path, 'r') as f:
                            ce_text = f.read()
                        ce_examples.append(f"Counterexample (from `{os.path.basename(path)}`):\n{ce_text}\n---")
                        used_paths.add(path)
                        break
                    except Exception:
                        continue

        prompt = construct_comprehensive_prompt(aadl_content, ce_examples, requirements_content)
        status = f"Prompt updated with failures: {', '.join(fail_names)}"
        return prompt, log_message(status, "info")

    status = "Great, all AGREE results are valid and no counterexamples were detected."
    prompt = status  # Make the prompt just this status message
    return prompt, log_message(status, "info")

# -------------------- Enhanced handle_app_interactions Callback --------------------
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
        State('include-upload-folder', 'value'),
        State('global-context-prompt', 'data')  # Global context prompt state
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
                            include_upload_folder,
                            global_context_prompt):
    global start_time, elapsed_time, formatted_elapsed_time, time_frames, total_api_time
    time_frames.append(elapsed_time)
    reset_timer_variables()

    ctx = dash.callback_context
    if not ctx.triggered:
        triggered_id = 'No clicks yet'
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    conversation_history = json.loads(conversation_history_json)

    # Handle system message confirmation
    if triggered_id == 'confirm-system-message-button' and confirm_n_clicks is not None:
        ch_json, resp, usr_val, tkn_count, tmr_display = set_system_message(conversation_history, system_message_choice)
        return ch_json, resp, usr_val, tkn_count, tmr_display, context_added

    # Handle submission with the submit button
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

        # Initialize conversation history if empty
        if not conversation_history:
            conversation_history = [
                {'role': 'system', 'content': INSPECTA_dog_system_msgs.AGREE_dog_sys_msg}
            ]
            context_added = "false"

        # Prepare the user input with global context prompt if available
        effective_user_input = prepare_effective_input(user_input or "", global_context_prompt)
        # effective_user_input = user_input or ""
        #
        # # If we have a global context prompt, use it as the base for the user's input
        # if global_context_prompt and not effective_user_input.startswith(global_context_prompt):
        #     if effective_user_input:
        #         # Combine global prompt with user's additional input
        #         effective_user_input = (
        #             f"{global_context_prompt}\n\n"
        #             f"Additional request: {effective_user_input}"
        #         )
        #         log_message("Combined global context prompt with user's additional input", "info")
        #     else:
        #         # Just use the global prompt
        #         effective_user_input = global_context_prompt
        #         log_message("Using global context prompt as there was no additional user input", "info")
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

        # Use cli_config for working directory and start file:
        if cli_config["working_dir"] is not None:
            target_directory = cli_config["working_dir"]
            if cli_config["start_file"] is not None:
                initial_file = cli_config["start_file"]
        else:
            target_directory = subdirectories[0] if subdirectories else ""
            log_message(f"Using subdirectory {target_directory} as target directory.", "info")

        # If we're still in manual context mode, process it
        if context_added == "false" and include_upload_folder == "yes":
            project_files = read_project_files(target_directory)
            if (include_requirements_chain == "yes" and initial_file):
                initial_file = remove_file_ext_from_cmd_like_ui(initial_file)
                file_context = concatenate_imports(
                    initial_file,
                    project_files,
                    target_directory,
                    include_requirements_chain,
                    include_upload_folder,
                    context_added
                )
                if file_context and cli_config["counter_example"] is not None:
                    cex_path = cli_config["counter_example"]
                    cex = read_counter_example_file(cex_path)
                    prompt = set_prompt(file_context, cex)
                    effective_user_input = f"{prompt}\n{effective_user_input}"
                context_added = "true"
            elif (include_requirements_chain == "no" and initial_file and context_added == "false" and cli_config[
                "counter_example"] is not None):
                cex_path = cli_config["counter_example"]
                cex = read_counter_example_file(cex_path)
                start_file_with_ext = cli_config["start_file"]
                working_dir = cli_config["working_dir"]
                start_file_path = os.path.join(working_dir, start_file_with_ext)
                start_file_content = read_start_file_content(start_file_path)
                prompt = set_prompt(start_file_content, cex)
                effective_user_input = f"{prompt}\n{effective_user_input}"
                context_added = "true"

        if requirements_file_content and not global_context_prompt:
            requirements_hint = (
                    "When you modify the code or try to write the fixed code, "
                    "consider the following requirements and make sure your modifications "
                    "don't break them:\n" + requirements_file_content
            )
            effective_user_input = f"\n{effective_user_input}"
            log_message("Integrated sys_requirements.txt content into user input.", "info")

        # Add the effective user input to the conversation history
        conversation_history.append({'role': 'user', 'content': effective_user_input})

        # Get completion from the model
        response_obj = get_completion_from_messages(conversation_history, model=model_choice)
        response = response_obj.choices[0].message["content"]
        tokens_used = response_obj['usage']['total_tokens']

        # Add the assistant's response to the conversation history
        conversation_history.append({'role': 'assistant', 'content': response})
        save_conversation_history_to_file(conversation_history)

        # Format the display text
        display_text = format_display_text(conversation_history, display_mode)
        warning = token_warning(model_choice, tokens_used)
        total_time_display = total_timedisplay(start_time, time_frames, total_api_time)

        return (
            json.dumps(conversation_history),
            display_text,
            "",  # Clear the input field
            f"Tokens used: {tokens_used}" + warning,
            total_time_display,
            "true"  # Mark context as added
        )

    # Default return when no action is triggered
    return (
        conversation_history_json,
        "",
        user_input,
        "Tokens used: 0",
        f"Elapsed Time: {formatted_elapsed_time}",
        context_added
    )


# -------------------- Callback for Apply Modifications (Insert) --------------------
@app.callback(
    Output('apply-status', 'children'),
    Input('apply-modifications', 'n_clicks'),
    State('conversation-history', 'children'),
    State('initial-file', 'value'),
    prevent_initial_call=True
)
def handle_apply_modifications(n_clicks, conversation_history_json, initial_file):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not conversation_history_json:
        log_message("No conversation history to parse.", "warning")
        return "No conversation history to parse."

    conversation_history = json.loads(conversation_history_json)
    assistant_messages = [msg for msg in conversation_history if msg['role'] == 'assistant']
    if not assistant_messages:
        message = "No assistant messages found to extract modifications."
        return log_message(message, "warning")

    last_assistant = assistant_messages[-1]['content']

    import re
    code_blocks = re.findall(r"```(.*?)```", last_assistant, flags=re.DOTALL)
    if not code_blocks:
        message = "No code blocks (``` ```) found in the last assistant message."
        return log_message(message, "warning")

    new_code = code_blocks[0].strip()

    # Use cli_config instead of re-calling get_args()
    working_dir = cli_config["working_dir"] if cli_config["working_dir"] else os.getcwd()

    if not initial_file and cli_config["start_file"]:
        initial_file = cli_config["start_file"]

    if not initial_file:
        error_message = "No initial file specified. Provide it via CLI or UI."
        return log_message(error_message, "warning")

    if not initial_file.lower().endswith(".aadl"):
        initial_file += ".aadl"

    target_path = os.path.join(working_dir, initial_file)

    # Modify first line if "aadl" is present.
    new_code = re.sub(r'^(?:\s*)aadl', '-- aadl', new_code)

    try:
        with open(target_path, "w") as f:
            f.write(new_code)
    except Exception as e:
        error_message = f"Failed to overwrite {target_path}: {e}"
        return log_message(error_message, "error")

    success_message = (
        f"Successfully updated {target_path}. \n Please refresh the model in your editor to see the updated file. "
        "If you're not happy with these changes, please revert via your IDE's Git or undo."
    )
    return log_message(success_message, "info")


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
    return log_message("Server is shutting down immediately...", "info")


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

    message = f"Successfully copied to {destination_file}"
    return log_message(message, "info")


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

    log_message(f"Folder '{filename}' uploaded and extracted successfully.", "info")
    return log_message(f"Folder '{filename}' uploaded and extracted successfully.", "info")


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
            log_message(message, "info")
            return message
        except Exception as e:
            os.chdir(current_directory_1)
            error_message = f"An error occurred: {e}"
            log_message(error_message, "error")
            return error_message


# -------------------- Utility Functions --------------------
def get_completion_from_messages(messages,temperature=1, model="o3"): #temperature=0.7, model="gpt-4-0613"):
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
    requirements_content_local = " "
    requirements_file_path = cli_config["requirement_file"]

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
    if cli_config["counter_example"] is None:
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
    if cli_config["start_file"] is not None:
        initial_file_cmd = cli_config["start_file"]
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
        log_message(f"File not found: {file_path}", "error")
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
    if cli_config["working_dir"] is not None:
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
            log_message(f"{current_file} is not in packages", "warning")
            continue

        if current_file == start_file:
            content = read_start_file_content(file_path)
        else:
            content = read_generic_file_content(file_path)
        context += content + "\n"

        handle_requires(file_path, project_files, files_to_check, processed_files)
    return context

def handle_valid_model_prompt(user_input, global_prompt):
    """
    Checks if the global prompt indicates no counterexamples and formats user input accordingly.
    """
    if global_prompt and "All properties valid, no counterexamples found." in global_prompt:
        return f"Great, all AGREE results are valid and no counterexamples were detected.\n\n{user_input or ''}"
    return None


def prepare_effective_input(user_input, global_prompt):
    """
    Prepares the final user input by conditionally modifying it based on context.
    """
    handled_valid = handle_valid_model_prompt(user_input, global_prompt)
    if handled_valid is not None:
        log_message("Handled input for valid model prompt.", "info")
        return handled_valid

    if global_prompt and not user_input.startswith(global_prompt):
        if user_input:
            log_message("Combined global context prompt with user's additional input", "info")
            return f"{global_prompt}\n\nAdditional request: {user_input}"
        else:
            log_message("Using global context prompt as there was no additional user input", "info")
            return global_prompt

    return user_input


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



# -------------------- Run the Server --------------------
if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:8050")
    log_message("Starting the Dash server...", "info")
    try:
        app.run_server(debug=False, host='127.0.0.1', port=8050)
    except KeyboardInterrupt:
        log_message("Shutting down the server gracefully.", "warning")
