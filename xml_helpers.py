import xml.etree.ElementTree as ET
import pandas as pd
from dash import dash_table


def parse_counterexample_xml(xml_path: str) -> pd.DataFrame:
    """
    Parse a JKind Results.xml file and extract the Counterexample block into a Pandas DataFrame.
    Index is "Step" (int), columns are signal names, values are strings.
    """
    # Load and parse XML
    root = ET.parse(xml_path).getroot()
    ce = root.find('.//Counterexample')
    if ce is None:
        return pd.DataFrame()

    data = {}
    # Iterate signals
    for sig in ce.findall('Signal'):
        name = sig.get('name')
        values = {}
        for v in sig.findall('Value'):
            t = int(v.get('time'))
            values[t] = v.text.strip()
        data[name] = values

    # Build DataFrame
    df = pd.DataFrame(data).sort_index()
    df.index.name = 'Step'
    return df


def make_dash_table(df: pd.DataFrame) -> dash_table.DataTable:
    """
    Convert a Pandas DataFrame into a Dash DataTable for interactive display.
    """
    if df.empty:
        return dash_table.DataTable()

    # Reset index so Step becomes a column
    display_df = df.reset_index()
    return dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in display_df.columns],
        fixed_rows={'headers': True},
        style_table={'overflowX': 'auto'},
        page_action='none',
        style_cell={
            'textAlign': 'left',
            'padding': '4px',
            'minWidth': '80px',
            'width': '80px',
            'maxWidth': '120px',
            'whiteSpace': 'normal'
        },
        style_header={
            'fontWeight': 'bold',
            'backgroundColor': '#f0f0f0'
        }
    )


def df_to_markdown(df: pd.DataFrame) -> str:
    """
    Serialize a Pandas DataFrame to a GitHub-flavored markdown table.
    """
    if df.empty:
        return ''
    # Use pandas built-in to_markdown (this requires pandas>=1.0)
    return df.to_markdown(tablefmt='github')
