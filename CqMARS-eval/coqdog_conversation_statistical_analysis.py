import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

"""Auther: @Amer N. Tahat, Collins Aerospace, Nov 2023 all rights reserved. Description: analyze stats calculated 
from the conversations and  visualize them it also creates a csv file for conversational statistics like median, 
mean, min, max etc.. summary. it also creates combined_df.csv and calculates statistics and distributions plots 
visualizations."""


# Helper functions
def extract_filename(full_path):
    # Split the path by '/' and take the last element
    parts = full_path.split('/')
    file_name = parts[-1]
    return file_name


def remove_last_four_chars(string):
    # Remove the last four characters
    return string[:-4]


# primary computation function :
def conversation_shots_statistical_analysis():
    # Directory containing the inputs CSV files
    csv_dir = './proof_analysis/csv_coqdog_conversation_stat_analysis'
    csv_dir_2 = './proof_analysis/other_spaces'

    # Directory to save the output files
    output_dir = './conversation_statistical_analysis'  # currently contains the o good spaces
    output_dir_2 = './conversation_statistical_analysis/other_spaces'

    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    csv_files = [os.path.join(csv_dir, file) for file in os.listdir(csv_dir) if file.endswith('.csv')]
    # combined output analysis
    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df_output_dir = './conversation_statistical_analysis/combined_df_csv_list'

    if not os.path.exists(combined_df_output_dir):
        os.makedirs(combined_df_output_dir)

    output_file = os.path.join(combined_df_output_dir, 'combined_df.csv')
    combined_df.to_csv(output_file, index=False)
    print(f'combined_df.csv file created at {output_file} for:\n')

    csv_files.append(f'{output_file}')

    # paths of CSV files
    print(csv_files)  # csv_files = ['path_to_csv1.csv', 'path_to_csv2.csv', 'path_to_csv3.csv', ... ,
    # path_to_combined_csv.csv]

    for file in csv_files:
        # Read the CSV file
        df = pd.read_csv(file)

        # Data cleaning (example for converting a string-list to list)
        # df['column_name'] = df['column_name'].apply(lambda x: eval(x) if pd.notnull(x) else x)

        # Calculate statistics for specific columns
        stats = df[['number of shots']].describe().loc[['mean', '50%', 'std', 'min', 'max']]  # can use it for 'cosine
        # distance',

        base_file_name_with_extension = extract_filename(file)
        base_file_name = remove_last_four_chars(base_file_name_with_extension)

        # Save the statistics to a new CSV file
        stats.to_csv(os.path.join(output_dir, f'stats_{base_file_name}.csv'))

        # Distribution Analysis
        # Customizing the box plot for more details
        annotated_boxplot(base_file_name, df, output_dir)
        column_name = 'number of shots'
        create_histogram_with_percentages(df, column_name, output_dir, base_file_name)
        # Strip plot for the same column
        create_and_save_strip_plot(df, column_name, output_dir, base_file_name)
        # new_std = remove_outliers_and_calculate_std(df['number of shots'])
        # print(new_std)

    print("\n conversation shots and combined analysis completed.")


# helper functions:

def annotated_boxplot(base_file_name, df, output_dir):
    plt.figure()
    boxplot = df['number of shots'].plot(kind='box', title='Distribution of Number of Shots')
    boxplot.annotate(f'Median: {df["number of shots"].median()}',
                     xy=(1, df['number of shots'].median()),
                     xytext=(1.1, df['number of shots'].median()),
                     arrowprops=dict(facecolor='black', shrink=0.05))
    plt.savefig(os.path.join(output_dir, f'boxplot_{base_file_name}.png'))


def annotated_boxplot_2(base_file_name, df, output_dir):
    plt.figure()
    boxplot = df['number of shots'].plot(kind='box', title='Distribution of Number of Shots')

    # Calculate the medians and quartiles
    median = df['number of shots'].median()
    Q1 = df['number of shots'].quantile(0.25)
    Q3 = df['number of shots'].quantile(0.75)

    # Annotate the Median
    boxplot.annotate(f'Median: {median}',
                     xy=(1, median),
                     xytext=(1.1, median),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     horizontalalignment='left')

    # Annotate the First Quartile (Q1)
    boxplot.annotate(f'Q1: {Q1}',
                     xy=(2, Q1),
                     xytext=(1.3, Q1),
                     arrowprops=dict(facecolor='blue', shrink=0.05),
                     horizontalalignment='right')

    # Annotate the Third Quartile (Q3)
    boxplot.annotate(f'Q3: {Q3}',
                     xy=(1, Q3),
                     xytext=(1.1, Q3),
                     arrowprops=dict(facecolor='green', shrink=0.05),
                     horizontalalignment='left')

    plt.savefig(os.path.join(output_dir, f'boxplot_{base_file_name}.png'))
    plt.close()


def create_and_save_boxplot(df, column_name, output_dir, base_file_name):
    plt.figure()
    boxplot = df[column_name].plot(kind='box', title=f'Distribution of {column_name}')

    # Annotating the median
    boxplot.annotate(f'Median: {df[column_name].median()}',
                     xy=(1, df[column_name].median()),
                     xytext=(1.1, df[column_name].median()),
                     arrowprops=dict(facecolor='black', shrink=0.05))

    # Check if output directory exists, create if not
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the boxplot in the output directory
    plt.savefig(os.path.join(output_dir, f'boxplot_{base_file_name}.png'))
    plt.close()  # Close the plot to free up memory
    print("\nboxplot completed.")


def create_histogram_with_percentages(df, column_name, output_dir, base_file_name):
    plt.figure()

    # Creating histogram and calculating percentages
    n, bins, patches = plt.hist(df[column_name], bins=range(1, 7), color='lightblue', edgecolor='black')

    # Calculating percentages for each bin
    total = float(len(df))  # Total number of data points
    percentages = [(count / total) * 100 for count in n]

    # Adjusting the height of patches and annotating each bin with its percentage
    for patch, percentage in zip(patches, percentages):
        patch.set_height(percentage)
        plt.annotate(f"{percentage:.1f}%",  # This formats to one decimal place
                     xy=(patch.get_x() + patch.get_width() / 2, percentage),
                     xytext=(0, 5), textcoords='offset points', va='center', ha='center', fontsize=8)

    plt.title(f'Histogram of {column_name} with Percentages')
    plt.xlabel(column_name)
    plt.ylabel('Percentage (%)')
    plt.ylim(0, max(percentages) * 1.1)  # Adjust y-axis limit to fit annotations

    # Check if output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the histogram in the output directory
    plt.savefig(os.path.join(output_dir, f'histogram_{base_file_name}.png'))
    plt.close()


def create_and_save_strip_plot(df, column_name, output_dir, base_file_name):
    plt.figure()

    # Creating strip plot
    sns.stripplot(x=column_name, data=df, jitter=True)

    plt.title(f'Strip Plot of {column_name}')
    plt.xlabel(column_name)
    plt.ylabel('Value')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the figure
    plt.savefig(os.path.join(output_dir, f'strip_plot_{base_file_name}.png'), bbox_inches='tight')
    plt.close()

    # Show the plot
    # plt.show()


def remove_outliers_and_calculate_std(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1

    # Define bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter out the outliers
    filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]

    # Calculate the new standard deviation
    new_std = filtered_data.std()

    return new_std


def main():
    conversation_shots_statistical_analysis()


if __name__ == "__main__":
    main()
