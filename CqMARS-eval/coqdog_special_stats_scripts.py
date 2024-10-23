"""
Author: @Amer N.Tahat, Collins Aerospace 2023
Created: November 2023
Description: accuracy and repair rate of change metrics.
"""
import openai
import os
from dotenv import load_dotenv
import pandas as pd
import tiktoken

# Load the OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

comment = (
    "def compute_tokens(text):\n"
    "    '''\n"
    "    Compute the number of tokens in a given text using OpenAI's GPT tokenizer.\n"
    "    '''\n"
    "    response = openai.chat/Completion.create(engine=\"davinci-text-003\", prompt=text, max_tokens=1) # 003 deprecated\n"
    "    token_count = response['usage']['total_tokens'] - 1\n"
    "    return token_count\n"
)


def compute_tokens(text):
    """
    Compute the number of tokens in a given text using OpenAI's GPT tokenizer.
    """
    # Use the appropriate encoding from gpt-4
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    token_count = len(tokens)
    return token_count


def count_words_in_string(text):
    """
    Count the number of words in a given string.
    """
    return len(text.split())


def calculate_acc_w(proofshots):
    """
    Calculate the relative accuracy per proof shot based on word count - we should call it 1 - diff-w and 1 - diff_tk.
    """
    words_per_string = [count_words_in_string(proof) for proof in proofshots]
    golden_proof_words = words_per_string[-1]
    repair_rate_of_change_w_per_shot = [abs(1 - (word_count / golden_proof_words)) for word_count in words_per_string]
    acc_w_per_shot = [abs(1 - rep_rate) for rep_rate in repair_rate_of_change_w_per_shot]
    acc_w_percentages = [f"{acc_w * 100:.1f}%" for acc_w in acc_w_per_shot]
    return acc_w_percentages


def calculate_acc_tk(proofshots):
    """
    Calculate the relative accuracy per proof shot based on token count.
    """
    tokens_per_string = [compute_tokens(proof) for proof in proofshots]
    golden_proof_tokens = tokens_per_string[-1]
    repair_rate_of_change_tk_per_shot = [abs(1 - token_count / golden_proof_tokens) for token_count in
                                         tokens_per_string]
    acc_tk_per_shot = [abs(1 - rep_rate) for rep_rate in repair_rate_of_change_tk_per_shot]
    acc_tk_percentages = [f"{acc_tk * 100:.1f}%" for acc_tk in acc_tk_per_shot]
    return acc_tk_percentages


def main():
    # Sample proofshots
    my_proofshots = [
        """intros t.
  induction t; intros p e; simpl.
  - eapply star_tran; eauto. apply stasp.
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_strem.
    apply IHt.
    eapply star_tran; eauto. apply stattstop.
  - eapply star_tran; eauto. apply stlseq.
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stls.
    apply IHt1.
    eapply star_tran; eauto. apply stlseqstop.
  - eapply star_tran; eauto. apply stbseq.
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbsl.
    apply IHt1.
    eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbsr.
    apply IHt2. ##70
    eapply star_tran; eauto. apply stbsrstop.
  - eapply star_tran; eauto. apply stbpar.
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbp.
    apply IHt1. ##91
    eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbp.
    apply IHt2.
    eapply star_tran; eauto. apply stbpstop."""
        ,
        """ intros t.
  induction t; intros; simpl.
  - eapply star_tran; eauto. 
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_strem.
    apply IHt.
    eapply star_tran; eauto.  
  - eapply star_tran; eauto. 
    eapply star_transitive.
    apply star_stls.
    apply IHt1.
    eapply star_tran; eauto. 
  - eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbsl.
    apply IHt1.
    eapply star_tran; eauto.
    eapply star_transitive.
    apply star_stbsr.
    apply IHt2.
    eapply star_tran; eauto. 
  - repeat dest_range.
    eapply star_tran; eauto. 
    eapply star_transitive.
    apply star_stbp.
    apply IHt1.
    apply IHt2.
    eapply star_tran; eauto."""
    ]
    my_proofshots_2 = [
        "intros t. induction t...",
        "intros t. induction t; intros; simpl..."
        # Add more proof strings as needed
    ]

    # Calculate acc_w
    acc_w_results = calculate_acc_w(my_proofshots)
    print("Accuracy per proof string (acc_w):", acc_w_results)

    # Calculate acc_tk
    acc_tk_results = calculate_acc_tk(my_proofshots)
    print("Accuracy per proof string (acc_tk):", acc_tk_results)


if __name__ == "__main__":
    main()
