#!/usr/bin/env python
# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: Jkind_wrapper.py - helper called by Jkind INSPECTA_Dog.py ai-router.
Date: 1st July 2024
"""
import argparse
import subprocess
import sys

def run_jkind(
    input_file,
    all_ivcs=False,
    excel=False,
    help=False,
    induct_cex=False,
    ivc=False,
    main=None,
    n=None,
    no_bmc=False,
    no_inv_gen=False,
    no_k_induction=False,
    no_slicing=False,
    pdr_max=None,
    read_advice=None,
    scratch=False,
    smooth=False,
    solver=None,
    timeout=None,
    version=False,
    write_advice=None,
    xml=False,
    xml_to_stdout=False,
    jkind_jar="jkind.jar",
):
    """
    Executes jkind.jar using the specified parameters.

    :param input_file:     The Lustre file or input file to analyze.
    :param all_ivcs:       Corresponds to -all_ivcs.
    :param excel:          Corresponds to -excel.
    :param help:           Corresponds to -help.
    :param induct_cex:     Corresponds to -induct_cex.
    :param ivc:            Corresponds to -ivc.
    :param main:           Corresponds to -main <arg>.
    :param n:              Corresponds to -n <arg>.
    :param no_bmc:         Corresponds to -no_bmc.
    :param no_inv_gen:     Corresponds to -no_inv_gen.
    :param no_k_induction: Corresponds to -no_k_induction.
    :param no_slicing:     Corresponds to -no_slicing.
    :param pdr_max:        Corresponds to -pdr_max <arg>.
    :param read_advice:    Corresponds to -read_advice <arg>.
    :param scratch:        Corresponds to -scratch.
    :param smooth:         Corresponds to -smooth.
    :param solver:         Corresponds to -solver <arg>.
    :param timeout:        Corresponds to -timeout <arg>.
    :param version:        Corresponds to -version.
    :param write_advice:   Corresponds to -write_advice <arg>.
    :param xml:            Corresponds to -xml.
    :param xml_to_stdout:  Corresponds to -xml_to_stdout.
    :param jkind_jar:      Path to jkind.jar (default: "jkind.jar").
    """
    command = ["java", "-jar", jkind_jar]

    # Add flags that do not take an additional argument
    if help:
        command.append("-help")
    if all_ivcs:
        command.append("-all_ivcs")
    if excel:
        command.append("-excel")
    if induct_cex:
        command.append("-induct_cex")
    if ivc:
        command.append("-ivc")
    if no_bmc:
        command.append("-no_bmc")
    if no_inv_gen:
        command.append("-no_inv_gen")
    if no_k_induction:
        command.append("-no_k_induction")
    if no_slicing:
        command.append("-no_slicing")
    if scratch:
        command.append("-scratch")
    if smooth:
        command.append("-smooth")
    if version:
        command.append("-version")
    if xml:
        command.append("-xml")
    if xml_to_stdout:
        command.append("-xml_to_stdout")

    # Add flags that require a value
    if main is not None:
        command.extend(["-main", main])
    if n is not None:
        command.extend(["-n", str(n)])
    if pdr_max is not None:
        command.extend(["-pdr_max", str(pdr_max)])
    if read_advice is not None:
        command.extend(["-read_advice", read_advice])
    if solver is not None:
        command.extend(["-solver", solver])
    if timeout is not None:
        command.extend(["-timeout", str(timeout)])
    if write_advice is not None:
        command.extend(["-write_advice", write_advice])

    # Finally, add the input file
    if input_file:
        command.append(input_file)

    print("Executing:", " ".join(command))
    subprocess.run(command, check=False)


def main():
    parser = argparse.ArgumentParser(
        description="Python wrapper for jkind.jar",
        # By default, argparse uses -h/--help for its own help.
        # If you also want to pass `-help` through to jkind, we do:
        add_help=False
    )

    # Define your own help so that -help goes to jkind
    parser.add_argument(
        "-help", action="store_true",
        help="Print JKind help (passed through to jkind)."
    )
    # Re-add standard Python help under a different flag if desired
    parser.add_argument(
        "--pyhelp", action="help",
        help="Show this wrapper's help message and exit."
    )

    # Positional input file (required by JKind)
    parser.add_argument(
        "input_file", nargs="?",
        help="Path to the input Lustre file (required by JKind)."
    )

    # Flags that do not take additional arguments
    parser.add_argument("-all_ivcs", action="store_true", help="Find all inductive validity cores.")
    parser.add_argument("-excel", action="store_true", help="Generate results in Excel format.")
    parser.add_argument("-induct_cex", action="store_true", help="Generate inductive counterexamples.")
    parser.add_argument("-ivc", action="store_true", help="Find an inductive validity core.")
    parser.add_argument("-no_bmc", action="store_true", help="Disable bounded model checking.")
    parser.add_argument("-no_inv_gen", action="store_true", help="Disable invariant generation.")
    parser.add_argument("-no_k_induction", action="store_true", help="Disable k-induction.")
    parser.add_argument("-no_slicing", action="store_true", help="Disable slicing.")
    parser.add_argument("-scratch", action="store_true", help="Produce files for debugging.")
    parser.add_argument("-smooth", action="store_true", help="Smooth counterexamples.")
    parser.add_argument("-version", action="store_true", help="Display JKind version information.")
    parser.add_argument("-xml", action="store_true", help="Generate results in XML format.")
    parser.add_argument("-xml_to_stdout", action="store_true", help="Generate XML results to stdout.")

    # Flags that do take additional arguments
    parser.add_argument("-main", help="Specify main node (overrides --%MAIN).")
    parser.add_argument("-n", type=int, help="Maximum depth for BMC and k-induction.")
    parser.add_argument("-pdr_max", type=int, help="Maximum number of PDR parallel instances.")
    parser.add_argument("-read_advice", help="Read advice from the specified file.")
    parser.add_argument("-solver", help="Choose SMT solver (e.g., z3, yices2, cvc4, mathsat).")
    parser.add_argument("-timeout", type=int, help="Maximum runtime in seconds.")
    parser.add_argument("-write_advice", help="Write advice to the specified file.")

    # Optional: Let the user specify the path to jkind.jar if it's not in the same directory
    parser.add_argument("--jkind_jar", default="jkind.jar", help="Path to jkind.jar (default: jkind.jar)")

    args = parser.parse_args()

    # If no input file was given, let's be safe and show usage or handle it
    if not args.input_file and not args.help and not args.version:
        parser.print_usage()
        print("\nERROR: You must specify an input file OR use -help/-version.", file=sys.stderr)
        sys.exit(1)

    # Call the run_jkind function with the parsed arguments
    run_jkind(
        input_file=args.input_file,
        all_ivcs=args.all_ivcs,
        excel=args.excel,
        help=args.help,
        induct_cex=args.induct_cex,
        ivc=args.ivc,
        main=args.main,
        n=args.n,
        no_bmc=args.no_bmc,
        no_inv_gen=args.no_inv_gen,
        no_k_induction=args.no_k_induction,
        no_slicing=args.no_slicing,
        pdr_max=args.pdr_max,
        read_advice=args.read_advice,
        scratch=args.scratch,
        smooth=args.smooth,
        solver=args.solver,
        timeout=args.timeout,
        version=args.version,
        write_advice=args.write_advice,
        xml=args.xml,
        xml_to_stdout=args.xml_to_stdout,
        jkind_jar=args.jkind_jar,
    )


if __name__ == "__main__":
    main()
