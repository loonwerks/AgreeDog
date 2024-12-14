# AgreeDog
AgreeDog is an AI-Copilot for the AGREE tool, designed to enhance AADL-based system design and analysis. It provides counterexample explanations and contract updates, assisting engineers in automating proof synthesis and repair. By leveraging AI capabilities, AgreeDog improves the efficiency and reliability of system verification processes.

We recently presented a workshop paper on AgreeDog and are actively developing a command-line interface for seamless integration into automated pipelines. The first official release is expected in Spring 2025.

## How to Run INSPECTA-Dog from the Command Line

You can run the INSPECTA-Dog application directly from the command line.  
First, ensure you have activated your Python virtual environment (tested on 
python 3.9.7):


1. **Activate your virtual environment** (if applicable):

    On Unix-like systems:
    ```bash
    source myenv/bin/activate
    ```
    
    On Windows (Command Prompt):
    ```powershell
    myenv\Scripts\activate
    ```

2. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the script with `--help`** to see available options:
    ```bash
    python INSPECTA_Dog.py --help
    ``` 
   e.g., on Windows:
    ```bash 
       PS C:\Users\amer_\AgreeDog> python INSPECTA_Dog.py --help
       usage: INSPECTA_Dog.py [-h] [--working-dir WORKING_DIR] [--user-open-api-key USER_OPEN_API_KEY]
       [--counter-example COUNTER_EXAMPLE] [--start-file START_FILE]
   ```

### Example Usage 

python INSPECTA_Dog.py 
  --working-dir path/to/work_dir 
  --start-file MySystem.aadl 
  --counter-example path/to/counter_example.txt 
  --user-open-api-key [YOUR_API_KEY_HERE]

You can adjust these paths and options as needed. 
## on Linux
1. **Example of cli**:

```bash
python INSPECTA_Dog.py \
  --working-dir /home/AgreeDog/uploaded_dir/car/packages \
  --counter-example /home/AgreeDog/counter_examples/car_model_cex_3.txt \
  --start-file Car.aadl \
  --user-open-api-key [YOUR_API_KEY_HERE]
  ```

Note: The --user-open-api-key option is optional. If you prefer, you can save your API key in the .env file located in the AgreeDog directory. If no key is provided, the application will attempt to read it from .env.

## on Windows
1. **Example of cli**:

```bash
python INSPECTA_Dog.py \
  --working-dir C:\Users\AgreeDog\uploaded_dir\car\packages \
  --counter-example C:\Users\AgreeDog\counter_examples\car_model_cex_3.txt\
  --start-file Car.aadl \
  --user-open-api-key [YOUR_API_KEY_HERE]
```